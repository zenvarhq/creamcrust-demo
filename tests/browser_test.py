"""Real Chromium QA. Every failed check exits nonzero; evidence is written to qa/.
Run: python tests/browser_test.py --url http://localhost:8000 --output .qa/browser
"""
from pathlib import Path
from urllib.parse import urlparse,urljoin
from playwright.sync_api import sync_playwright,expect
import argparse,json,sys,time

parser=argparse.ArgumentParser()
parser.add_argument('--url',default='http://127.0.0.1:8766')
parser.add_argument('--output',default='../qa/after')
parser.add_argument('--smoke-only',action='store_true')
parser.add_argument('--self-test-failure',action='store_true')
parser.add_argument('--performance-only',action='store_true')
args=parser.parse_args()
OUT=Path(args.output).resolve();OUT.mkdir(parents=True,exist_ok=True)
BASE=args.url.rstrip('/')
results=[];console=[];requests=[];pages=[]

def check(name,action):
    try: action();results.append({'test':name,'status':'PASS'})
    except Exception as error: results.append({'test':name,'status':'FAIL','error':str(error)[:1800]})
    print(results[-1]['status'],name,flush=True)

def require(value,message):
    assert value,message

def open_page(context,route):
    page=context.new_page()
    page.on('pageerror',lambda error:console.append({'type':'pageerror','route':page.url,'message':str(error)}))
    page.on('console',lambda msg:console.append({'type':msg.type,'route':page.url,'message':msg.text}) if msg.type in ['warning','error'] else None)
    page.on('requestfailed',lambda request:requests.append({'url':request.url,'error':request.failure}))
    response=page.goto(BASE+route,wait_until='networkidle',timeout=20000)
    require(response is not None and response.status==200,f'Expected HTTP 200: {response.status if response else "no response"}')
    page.evaluate('document.fonts.ready')
    return page

if args.self_test_failure:
    check('Intentional failed assertion',lambda:require(False,'Expected failure: exit-code verification'))
    (OUT/'failure-contract.json').write_text(json.dumps(results,indent=2))
    sys.exit(1 if results[0]['status']=='FAIL' else 0)

def measure_mobile(browser):
    for route in ['/','/menu/']:
        context=browser.new_context(viewport={'width':390,'height':844},reduced_motion='reduce')
        context.add_init_script("window.qaVitals={lcp:0,cls:0};new PerformanceObserver(l=>{for(const e of l.getEntries())window.qaVitals.lcp=e.startTime}).observe({type:'largest-contentful-paint',buffered:true});new PerformanceObserver(l=>{for(const e of l.getEntries())if(!e.hadRecentInput)window.qaVitals.cls+=e.value}).observe({type:'layout-shift',buffered:true})")
        p=context.new_page();p.bring_to_front();cdp=context.new_cdp_session(p)
        cdp.send('Network.enable');cdp.send('Network.setCacheDisabled',{'cacheDisabled':True});cdp.send('Network.emulateNetworkConditions',{'offline':False,'latency':150,'downloadThroughput':200000,'uploadThroughput':100000})
        cdp.send('Emulation.setCPUThrottlingRate',{'rate':4})
        started=time.monotonic();p.goto(BASE+route,wait_until='networkidle',timeout=30000)
        p.screenshot(path=str(OUT/('mobile-constrained-home.png' if route=='/' else 'mobile-constrained-menu.png')))
        metrics=p.evaluate('''()=>({navigation:performance.getEntriesByType('navigation')[0].toJSON(),paints:performance.getEntriesByType('paint').map(p=>({name:p.name,startTime:p.startTime})),bytes:performance.getEntriesByType('resource').reduce((n,r)=>n+r.transferSize,0),external:performance.getEntriesByType('resource').filter(r=>!r.name.startsWith(location.origin)).map(r=>r.name),animated:[...document.querySelectorAll('*')].filter(e=>getComputedStyle(e).animationName!=='none').length,vitals:window.qaVitals})''')
        metrics['elapsed_seconds']=round(time.monotonic()-started,2)
        require(not metrics['external'],'Unexpected remote asset dependency');require(metrics['animated']==0,'Decorative motion remains with reduced-motion enabled')
        (OUT/('performance-home.json' if route=='/' else 'performance-menu.json')).write_text(json.dumps(metrics,indent=2),encoding='utf-8')
        print(route,metrics['vitals'],metrics['bytes'],'bytes',flush=True)
        context.close()

if args.performance_only:
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        check('Cold constrained mobile performance and reduced motion',lambda:measure_mobile(browser))
        browser.close()
    sys.exit(1 if any(r['status']=='FAIL' for r in results) else 0)

with sync_playwright() as playwright:
    browser=playwright.chromium.launch(headless=True)
    try:
        for width,height in [(360,800),(390,844),(768,1024),(1440,900)]:
            context=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1)
            for route in ['/','/story/','/gallery/','/visit/','/menu/','/studio/']:
                def smoke(route=route,width=width):
                    page=open_page(context,route);pages.append(page)
                    require(page.locator('h1').count()==1,'Exactly one h1 required')
                    require(not page.evaluate('document.documentElement.scrollWidth>innerWidth+1'),'Horizontal overflow')
                    require('noindex' in page.locator('meta[name=robots]').get_attribute('content'),'Demo must remain noindex')
                    require('unofficial' in page.locator('body').inner_text().lower() or 'local demonstration' in page.locator('body').inner_text().lower(),'Missing demonstration notice')
                    broken=page.evaluate('''async()=>{const images=[...document.images].filter(i=>i.getAttribute('src'));images.forEach(i=>i.loading='eager');await Promise.race([Promise.all(images.map(i=>i.decode().catch(()=>{}))),new Promise(r=>setTimeout(r,10000))]);return images.filter(i=>!i.naturalWidth).map(i=>i.src)}''')
                    require(not broken,'Broken images: '+str(broken))
                    if route=='/':
                        cta=page.locator('.hero-actions a').first.bounding_box();require(cta['y']+cta['height']<844,'Hero CTA below mobile fold')
                        image=page.locator('.hero-main-photo').bounding_box();require(image['y']<700,'Food image below first view')
                    if route=='/menu/' and not args.smoke_only:
                        require(page.locator('.product-card').count()==40,'Expected 40 listed items')
                        require(page.locator('#menu-search').bounding_box()['y']<650,'Search must be visible in first view')
                    if route in ['/','/menu/','/gallery/','/visit/']:
                        name='home' if route=='/' else route.strip('/')
                        page.screenshot(path=str(OUT/f'{name}-{width}.png'),animations='disabled',full_page=False)
                        if width in [390,1440]:page.screenshot(path=str(OUT/f'{name}-{width}-full.png'),animations='disabled',full_page=True)
                    page.close()
                check(f'{width}px {route} route, assets, layout and demo labels',smoke)
            context.close()

        if not args.smoke_only:
            for width in [360,390,768,1440]:
                context=browser.new_context(viewport={'width':width,'height':844 if width==390 else 900})
                page=open_page(context,'/menu/')
                def menu_flow():
                    page.locator('#menu-search').fill('waffle');expect(page.locator('.product-card')).to_have_count(6)
                    require(all('waffle' in t.lower() for t in page.locator('.product-title').all_text_contents()),'Incorrect search match')
                    page.locator('#clear-search').click();expect(page.locator('.product-card')).to_have_count(40)
                    page.locator('#menu-search').fill('zz-no-such-food');expect(page.locator('#empty-state')).to_be_visible()
                    page.locator('#reset-filters').click();expect(page.locator('.product-card')).to_have_count(40)
                    expect(page.locator('#clear-search')).to_be_hidden()
                    page.locator('[data-cat=burgers]').click();expect(page.locator('.product-card')).to_have_count(3)
                    page.locator('#menu-sort').select_option('price-asc')
                    import re
                    values=page.locator('.product-price').all_text_contents();numbers=[int(re.search(r'₹([\d,]+)',v).group(1).replace(',','')) for v in values]
                    require(numbers==sorted(numbers),'Price order incorrect')
                    page.locator('#menu-sort').select_option('price-desc')
                    values=page.locator('.product-price').all_text_contents();numbers=[int(re.search(r'₹([\d,]+)',v).group(1).replace(',','')) for v in values]
                    require(numbers==sorted(numbers,reverse=True),'Descending price order incorrect')
                    page.locator('#menu-sort').select_option('name')
                    names=page.locator('.product-title').all_text_contents();require(names==sorted(names),'Name order incorrect')
                    page.locator('#menu-sort').select_option('default')
                    trigger=page.locator('.details-button').first;trigger.click();expect(page.locator('#item-dialog')).to_be_visible()
                    expect(page.locator('#item-close')).to_be_focused()
                    page.keyboard.press('Escape');expect(page.locator('#item-dialog')).not_to_be_visible();expect(trigger).to_be_focused()
                    trigger.press('Enter');expect(page.locator('#item-dialog')).to_be_visible();page.locator('#item-close').click();expect(trigger).to_be_focused()
                    heart=page.locator('.heart').first;heart.press('Enter');expect(page.locator('.heart').first).to_be_focused()
                    page.locator('#faves-toggle').click();expect(page.locator('.product-card')).to_have_count(1)
                    page.reload(wait_until='networkidle');expect(page.locator('.product-card')).to_have_count(1)
                    page.locator('.heart').first.click();expect(page.locator('#empty-state')).to_be_visible();expect(page.locator('#faves-toggle')).to_be_focused()
                check(f'{width}px menu search, clear, empty, category, sort, keyboard dialogs, focus, saved reload',menu_flow)
                def deep_links():
                    page.goto(BASE+'/menu/#category-fried-chicken');expect(page.locator('[data-cat=fried-chicken]')).to_have_attribute('aria-pressed','true')
                    page.reload();expect(page.locator('[data-cat=fried-chicken]')).to_have_attribute('aria-pressed','true')
                    page.locator('[data-cat=burgers]').click();page.go_back();expect(page.locator('[data-cat=fried-chicken]')).to_have_attribute('aria-pressed','true')
                    page.locator('[data-cat=all]').click();page.go_back();expect(page.locator('[data-cat=fried-chicken]')).to_have_attribute('aria-pressed','true')
                    page.goto(BASE+'/menu/?item=biscoff-belgian-waffle');expect(page.locator('#item-dialog')).to_be_visible();expect(page.locator('#item-title')).to_contain_text('Biscoff');page.keyboard.press('Escape')
                    page.goto(BASE+'/');page.locator('.craving-card.sweet').click();expect(page.locator('[data-cat=sundaes]')).to_have_attribute('aria-pressed','true')
                    page.goto(BASE+'/');page.locator('.craving-card.crispy').click();expect(page.locator('[data-cat=fried-chicken]')).to_have_attribute('aria-pressed','true')
                check(f'{width}px homepage category links, fresh load, refresh, Back and item links',deep_links)
                def navigation():
                    page.goto(BASE+'/')
                    if width<=760:
                        page.locator('.menu-toggle').press('Enter');expect(page.locator('.nav-mobile')).to_be_visible()
                        page.keyboard.press('Escape');expect(page.locator('.menu-toggle')).to_be_focused();expect(page.locator('.menu-toggle')).to_have_attribute('aria-expanded','false')
                        page.locator('.menu-toggle').click();page.locator('.nav-mobile').get_by_role('link',name='The Concept',exact=True).click();require(page.url.endswith('/story/'),'Mobile route failed')
                    page.goto(BASE+'/gallery/');photo=page.locator('.gallery-photo').first;photo.press('Enter');expect(page.locator('.gallery-dialog')).to_be_visible()
                    for _ in range(3):
                        page.keyboard.press('Tab');require(page.evaluate('document.activeElement.closest(".gallery-dialog")!==null'),'Tab escaped the gallery viewer')
                    page.keyboard.press('Escape');expect(photo).to_be_focused()
                check(f'{width}px navigation and gallery keyboard dialog',navigation)
                page.close();context.close()

            context=browser.new_context(viewport={'width':1440,'height':900});page=open_page(context,'/studio/')
            def studio():
                name='Classic Crunch Chicken Burger [Regular]'
                # Exact source name is read from the retained catalogue rather than guessed display copy.
                item=page.evaluate('window.CREAMCRUST_CATALOG.items.find(i=>i.id==="classic-crunch-chicken-burger-regular")')
                name=item['name'];page.get_by_label('Price for '+name,exact=True).fill('321');page.get_by_label('Price for '+name,exact=True).press('Tab')
                expect(page.get_by_label('Owner approval pending for '+name,exact=True)).to_be_disabled()
                page.locator('#save').click();expect(page.locator('#status')).to_contain_text('Saved in this browser only')
                page.goto(BASE+'/menu/#category-burgers');require('321' in page.locator('.product-price').all_text_contents()[0],'Studio price missing in menu')
                require('Owner-confirmed' not in page.locator('body').inner_text(),'False owner verification')
                page.goto(BASE+'/');expect(page.locator('[data-featured="classic-crunch-chicken-burger-regular"] .price-text')).to_have_text('₹321*')
                other=browser.new_context();fresh=open_page(other,'/menu/#category-burgers');require('321' not in fresh.locator('.product-price').all_text_contents()[0],'Local edits leaked to another browser context');fresh.close();other.close()
                page.goto(BASE+'/studio/');expect(page.get_by_label('Price for '+name,exact=True)).to_have_value('321')
                page.get_by_label('Price for '+name,exact=True).fill('-1');page.get_by_label('Price for '+name,exact=True).press('Tab');page.locator('#save').click();expect(page.locator('#status')).to_contain_text('Fix invalid prices')
                page.get_by_label('Price for '+name,exact=True).fill('321');page.get_by_label('Price for '+name,exact=True).press('Tab')
                with page.expect_download() as event:page.locator('#export').click()
                download=event.value;download.save_as(str(OUT/'studio-export.json'))
                require(json.loads((OUT/'studio-export.json').read_text())['items'],'Export is not a catalogue')
                page.locator('#import').set_input_files({'name':'invalid.json','mimeType':'application/json','buffer':b'{"items":[],"categories":null}'})
                expect(page.locator('#status')).to_contain_text('Import failed')
                page.locator('#import').set_input_files(str(OUT/'studio-export.json'))
                expect(page.locator('#status')).to_contain_text('Imported locally')
                page.get_by_label('Availability preview for '+name,exact=True).select_option('no')
                page.locator('#save').click();page.goto(BASE+'/menu/#category-burgers')
                expect(page.locator('.product-card').first.locator('.availability')).to_contain_text('Unavailable in local preview')
                page.goto(BASE+'/studio/')
                page.on('dialog',lambda dialog:dialog.accept());page.locator('#reset').click();expect(page.locator('#status')).to_contain_text('reset')
            check('Studio local persistence, shared homepage, isolated contexts, validation and JSON export/import',studio)
            def link_audit():
                all_links=set()
                for route in ['/','/story/','/gallery/','/visit/','/menu/','/studio/']:
                    page.goto(BASE+route);all_links.update(page.locator('a[href]').evaluate_all('(els)=>els.map(a=>a.href)'))
                    unsafe=page.locator('a[target=_blank]').evaluate_all('(els)=>els.filter(a=>!a.rel.includes("noopener")||!a.rel.includes("noreferrer")).map(a=>a.href)')
                    require(not unsafe,'Unsafe external link attributes')
                for url in sorted(all_links):
                    if url.startswith(BASE):require(context.request.get(url).status==200,'Broken internal link: '+url)
                external=sorted(u for u in all_links if not u.startswith(BASE))
                require(not any(u.startswith('tel:') for u in external),'Phone actions must remain disabled during the no-contact sprint')
                for host in ['www.google.com','www.swiggy.com','www.zomato.com']:
                    require(any(urlparse(u).netloc==host for u in external),'Missing provider: '+host)
                (OUT/'external-links.json').write_text(json.dumps({'destinations':external,'note':'Destination structure checked; calls, orders, forms and login were not performed.'},indent=2),encoding='utf-8')
            check('Internal links return 200; Maps/call/provider destinations and safe link attributes',link_audit)
            context.close()
            def no_js():
                context=browser.new_context(java_script_enabled=False,viewport={'width':390,'height':844});p=open_page(context,'/menu/');p.get_by_role('link',name='Read the complete 40-item text preview').click();require(p.locator('tbody tr').count()==40,'No-JS menu missing');context.close()
            check('JavaScript-disabled text menu contains all 40 sample items',no_js)
            def defensive_storage():
                context=browser.new_context();context.add_init_script("Object.defineProperty(Storage.prototype,'setItem',{value(){throw new Error('Storage disabled for QA')}});Object.defineProperty(Storage.prototype,'getItem',{value(){throw new Error('Storage disabled for QA')}})")
                p=open_page(context,'/menu/');require(p.locator('.product-card').count()==40,'Blocked storage prevents menu rendering');p.locator('.heart').first.click();expect(p.locator('#storage-status')).to_contain_text('unavailable');context.close()
                context=browser.new_context();context.add_init_script("localStorage.setItem('cc_catalog_override_v1','{broken-json');localStorage.setItem('cc_saved_items_v1','{}')")
                p=open_page(context,'/menu/#category-%');require(p.locator('.product-card').count()==40,'Malformed state prevents fallback');context.close()
            check('Blocked storage, malformed stored data and malformed category links degrade safely',defensive_storage)
            def constrained():
                measure_mobile(browser)
            check('Cold mobile at 1.6Mbps/150ms/4x CPU, no external assets and reduced motion',constrained)
        check('No uncaught JavaScript or console errors',lambda:require(not [e for e in console if e['type'] in ['pageerror','error']],str(console)))
        check('No failed asset requests',lambda:require(not requests,str(requests)))
    finally:browser.close()

report={'passed':sum(r['status']=='PASS' for r in results),'failed':sum(r['status']=='FAIL' for r in results),'base_url':BASE,'browser':'Playwright Chromium','results':results,'console':console,'failed_requests':requests}
(OUT/'results.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
(OUT/'console.json').write_text(json.dumps(console,indent=2),encoding='utf-8')
print(f"RESULT: {report['passed']} passed; {report['failed']} failed. Evidence: {OUT}")
sys.exit(1 if report['failed'] else 0)
