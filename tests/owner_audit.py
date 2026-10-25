"""Real browser evidence for the current repository. Exits nonzero on failed checks."""
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
import argparse, json, sys, urllib.request, tarfile, io

parser=argparse.ArgumentParser()
parser.add_argument('--url',required=True)
parser.add_argument('--output',required=True)
parser.add_argument('--require-improvements',action='store_true')
parser.add_argument('--external',action='store_true')
args=parser.parse_args()
BASE=args.url.rstrip('/')
OUT=Path(args.output).resolve();OUT.mkdir(parents=True,exist_ok=True)
ROOT=Path(__file__).resolve().parents[1]
tool=ROOT/'.cache/axe.min.js';tool.parent.mkdir(exist_ok=True)
if not tool.exists():
    meta=json.load(urllib.request.urlopen('https://registry.npmjs.org/axe-core/4.14.0',timeout=25))
    with urllib.request.urlopen(meta['dist']['tarball'],timeout=25) as r:
        archive=tarfile.open(fileobj=io.BytesIO(r.read()),mode='r:gz')
        tool.write_bytes(archive.extractfile('package/axe.min.js').read())

results=[];observations=[];axe=[];console=[];http=[];external=[]
def check(name,fn):
    try:fn();results.append({'test':name,'status':'PASS'})
    except Exception as e:results.append({'test':name,'status':'FAIL','error':str(e)[:1400]})
    print(results[-1]['status'],name,flush=True)
def require(value,message):
    if not value:raise AssertionError(message)

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    destinations=set()
    for width,height in [(360,800),(390,844),(768,1024),(1440,900)]:
        context=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1)
        page=context.new_page()
        page.on('pageerror',lambda e:console.append({'type':'pageerror','message':str(e)}))
        page.on('console',lambda m:console.append({'type':m.type,'message':m.text}) if m.type=='error' else None)
        page.on('response',lambda r:http.append({'url':r.url,'status':r.status}) if r.status>=400 else None)
        for route in ['/','/menu/','/story/','/gallery/','/visit/','/studio/']:
            name=route.strip('/') or 'home'
            def capture(route=route,name=name):
                response=page.goto(BASE+route,wait_until='networkidle',timeout=30000)
                require(response.status==200,f'HTTP {response.status}')
                page.evaluate('document.fonts.ready')
                observation=page.evaluate('''()=>({overflow:document.documentElement.scrollWidth>innerWidth+1,photos:[...document.images].filter(i=>i.currentSrc).map(i=>({src:i.currentSrc,alt:i.alt,natural:i.naturalWidth,width:i.width,height:i.height})),phoneLinks:document.querySelectorAll('a[href^="tel:"]').length,disclosure:document.querySelector('.photo-label')?getComputedStyle(document.querySelector('.photo-label')).display:null})''')
                observation.update(route=route,width=width);observations.append(observation)
                require(not observation['overflow'],'Unexpected horizontal overflow')
                require(observation['phoneLinks']==0,'Calling must remain disabled during no-contact period')
                if args.require_improvements and route=='/menu/':
                    require(observation['disclosure']!='none','Illustrative photo label hidden')
                page.screenshot(path=str(OUT/f'{name}-{width}.png'),animations='disabled')
                if width in [390,1440]:page.screenshot(path=str(OUT/f'{name}-{width}-full.png'),full_page=True,animations='disabled')
                destinations.update(page.locator('a[href^="https://"]').evaluate_all('(links)=>links.map(a=>a.href)'))
                if width in [390,1440]:
                    page.add_script_tag(path=str(tool))
                    audit=page.evaluate('''async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','best-practice']}});return {passes:r.passes.length,violations:r.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}))}}''')
                    audit.update(route=route,width=width);axe.append(audit)
                    require(not audit['violations'],'Accessibility violations: '+str(audit['violations']))
            check(f'{width}px {route}: capture, layout, no-contact and accessibility',capture)
        context.close()

    source=json.loads((ROOT/'data/menu.json').read_text(encoding='utf-8'))
    for width in [390,1440]:
        context=browser.new_context(viewport={'width':width,'height':844 if width==390 else 900})
        page=context.new_page();page.goto(BASE+'/menu/',wait_until='networkidle')
        def categories():
            for cat in source['categories']:
                page.locator(f'[data-cat="{cat["id"]}"]').click()
                expected=[i['name'] for i in source['items'] if i['category']==cat['id']]
                require(sorted(page.locator('.product-title').all_text_contents())==sorted(expected),'Wrong items: '+cat['id'])
            page.locator('[data-cat=all]').click()
        check(f'{width}px: every category returns its named source items',categories)
        def details():
            for item in source['items']:
                trigger=page.locator(f'.details-button[data-open="{item["id"]}"]')
                trigger.click();expect(page.locator('#item-title')).to_have_text(item['name'])
                expect(page.locator('#item-dialog')).to_contain_text('Dine-in prices unverified')
                expect(page.locator('#item-dialog')).to_contain_text('illustrative')
                page.keyboard.press('Escape');expect(trigger).to_be_focused()
            require(not page.locator('#item-dialog').is_visible(),'Dialog did not close')
        check(f'{width}px: all 40 details open, disclose source, close with ESC and restore focus',details)
        def category_visibility():
            page.goto(BASE+'/menu/#category-beverages',wait_until='networkidle')
            page.evaluate('document.fonts.ready')
            if args.require_improvements:
                page.wait_for_function('''()=>{const chip=document.querySelector('[data-cat=beverages]').getBoundingClientRect(),rail=document.querySelector('#category-rail').getBoundingClientRect();return chip.left>=rail.left-1&&chip.right<=rail.right+1}''',timeout=3000)
            chip=page.locator('[data-cat=beverages]').bounding_box();rail=page.locator('#category-rail').bounding_box()
            visible=chip['x']>=rail['x']-1 and chip['x']+chip['width']<=rail['x']+rail['width']+1
            observations.append({'route':'/menu/#category-beverages','width':width,'active_chip_visible':visible})
            if args.require_improvements:require(visible,'Selected category hidden on fresh load: '+str({'chip':chip,'rail':rail}))
        check(f'{width}px: fresh category-link visibility audit',category_visibility)
        if args.require_improvements:
            def keyboard_visibility():
                page.goto(BASE+'/menu/',wait_until='networkidle');page.locator('#menu-search').focus()
                checked=0
                for _ in range(80):
                    page.keyboard.press('Tab')
                    item=page.evaluate('''()=>{const e=document.activeElement;if(!e.closest('.product-card'))return null;const r=e.getBoundingClientRect(),bar=document.querySelector('.menu-controls').getBoundingClientRect();return {top:r.top,bottom:r.bottom,bar:bar.bottom,label:e.getAttribute('aria-label')}}''')
                    if item:
                        checked+=1
                        require(item['top']>=item['bar']-1 and item['bottom']<=page.viewport_size['height']+1,'Keyboard target obscured: '+str(item))
                require(checked>=20,'Too few product keyboard targets checked')
            check(f'{width}px: keyboard product targets stay clear of sticky controls',keyboard_visibility)
        context.close()
    if args.external:
        context=browser.new_context();page=context.new_page()
        for url in sorted(destinations):
            try:
                response=page.goto(url,wait_until='domcontentloaded',timeout=18000)
                external.append({'url':url,'status':response.status if response else None,'final_url':page.url,'title':page.title(),'method':'read-only browser GET; no forms, sign-in, calls or orders'})
            except Exception as e:external.append({'url':url,'error':str(e)[:250]})
        context.close()
    check('No uncaught errors or HTTP asset failures',lambda:require(not console and not http,str(console+http)))
    browser.close()

report={'base_url':BASE,'passed':sum(r['status']=='PASS' for r in results),'failed':sum(r['status']=='FAIL' for r in results),'checks':results,'observations':observations,'axe_scans':axe,'console':console,'http_errors':http,'external_destinations':external}
(OUT/'owner-audit.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print('RESULT:',report['passed'],'passed;',report['failed'],'failed;',len(axe),'axe scans',flush=True)
sys.exit(1 if report['failed'] else 0)
