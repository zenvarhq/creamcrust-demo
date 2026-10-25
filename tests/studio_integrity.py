"""Browser-level local editing, import validation and reset regressions."""
import argparse,json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright,expect

p=argparse.ArgumentParser();p.add_argument('--url',required=True);p.add_argument('--output',required=True);a=p.parse_args()
BASE=a.url.rstrip('/');OUT=Path(a.output);OUT.mkdir(parents=True,exist_ok=True)
checks=[];errors=[];writes=[]
def require(condition,message):
    if not condition:raise AssertionError(message)
def check(name,fn):
    try:fn();checks.append({'test':name,'status':'PASS'})
    except Exception as e:checks.append({'test':name,'status':'FAIL','error':str(e)[:1600]})
    print(checks[-1]['status'],name,flush=True)
def import_json(page,data):
    page.locator('#import').set_input_files({'name':'edited.json','mimeType':'application/json','buffer':json.dumps(data).encode()})

with sync_playwright() as pw:
    browser=pw.chromium.launch()
    for width in [360,390,768,1440]:
        ctx=browser.new_context(viewport={'width':width,'height':844 if width<768 else 1024 if width==768 else 900})
        page=ctx.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('request',lambda r:writes.append(r.url) if r.method not in ['GET','HEAD'] else None)
        page.goto(BASE+'/studio/',wait_until='networkidle')
        source=page.evaluate('window.CREAMCRUST_CATALOG');item=source['items'][0];name=item['name'];id=item['id']
        price=page.get_by_label('Price for '+name,exact=True)
        def invalid_filter():
            price.fill('-1');price.press('Tab')
            page.locator('#studio-search').fill('waffle')
            page.locator('#save').click();expect(page.locator('#status')).to_contain_text('Fix invalid prices')
            page.locator('#export').click();expect(page.locator('#status')).to_contain_text('Fix invalid prices')
            page.locator('#studio-search').fill('');expect(price).to_have_value('-1');expect(price).to_have_attribute('aria-invalid','true')
            price.fill('321');price.press('Tab');page.locator('#save').click();expect(page.locator('#status')).to_contain_text('Saved in this browser only')
            page.reload(wait_until='networkidle');expect(price).to_have_value('321')
        check(f'{width}px invalid price survives filtering; save/export blocked; corrected value survives reload',invalid_filter)
        def json_editing():
            with page.expect_download() as event:page.locator('#export').click()
            exported=OUT/f'export-{width}.json';event.value.save_as(str(exported));data=json.loads(exported.read_text())
            data['items'][0]['price']=432;data['items'][0]['available']=False
            data['items'][0]['verified_by_owner']=True;data['approved_for_live_use']=True
            import_json(page,data);expect(page.locator('#status')).to_contain_text('Imported locally')
            other=ctx.new_page();other.goto(BASE+f'/menu/?item={id}',wait_until='networkidle')
            expect(other.locator('.modal-price')).to_contain_text('321');other.close()
            page.locator('#save').click();page.reload(wait_until='networkidle');expect(price).to_have_value('432')
            stored=page.evaluate('window.CC.load()');require(not stored['approved_for_live_use'] and not any(i['verified_by_owner'] for i in stored['items']),'Import falsely granted owner approval')
            page.goto(BASE+f'/menu/?item={id}',wait_until='networkidle');expect(page.locator('.modal-price')).to_contain_text('432');expect(page.locator('#item-dialog')).to_contain_text('Unavailable in this local demonstration')
            page.keyboard.press('Escape');page.locator(f'[data-heart="{id}"]').click();page.locator('#price-toggle').click()
            page.goto(BASE+'/studio/',wait_until='networkidle')
            for variant in ['fraction','availability','duplicate']:
                bad=json.loads(json.dumps(data))
                if variant=='fraction':bad['items'][0]['price']=12.5
                if variant=='availability':bad['items'][0]['available']='confirmed'
                if variant=='duplicate':bad['items'][1]['id']=bad['items'][0]['id']
                import_json(page,bad);expect(page.locator('#status')).to_contain_text('Import failed');expect(price).to_have_value('432')
            page.locator('#import').set_input_files({'name':'broken.json','mimeType':'application/json','buffer':b'{oops'})
            expect(page.locator('#status')).to_contain_text('Import failed');expect(price).to_have_value('432')
        check(f'{width}px edit/export/import JSON, explicit save, approval stripping and invalid import rejection',json_editing)
        def reset():
            page.once('dialog',lambda d:d.dismiss());page.locator('#reset').click();expect(price).to_have_value('432')
            page.once('dialog',lambda d:d.accept());page.locator('#reset').click();expect(page.locator('#status')).to_contain_text('reset')
            page.reload(wait_until='networkidle');expect(price).to_have_value(str(item['price']))
            require(page.evaluate('localStorage.getItem(window.CC.KEY)') is None,'Override key remains')
            require(page.evaluate('JSON.parse(localStorage.getItem("cc_saved_items_v1"))').count(id)==1,'Reset erased saved items')
            require(page.evaluate('localStorage.getItem("cc_hide_prices_v1")')=='1','Reset erased price preference')
            page.goto(BASE+'/menu/',wait_until='networkidle');expect(page.locator('.product-card')).to_have_count(len(source['items']))
            page.locator('#price-toggle').click();expect(page.locator(f'[data-heart="{id}"]')).to_have_attribute('aria-pressed','true')
            page.goto(BASE+f'/menu/?item={id}',wait_until='networkidle');expect(page.locator('.modal-price')).to_contain_text(str(item['price']))
        check(f'{width}px reset cancel, confirm, reload and original menu restoration; favourites/preferences retained',reset)
        ctx.close()
    def metadata_and_alts():
        ctx=browser.new_context();page=ctx.new_page();page.goto(BASE+'/',wait_until='networkidle')
        business=page.evaluate('window.CREAMCRUST_BUSINESS')
        require(business['deployment']['publiclyDeployed'] is True,'Outdated public deployment flag')
        require(business['deployment']['publicUrl']=='https://zenvarhq.github.io/creamcrust-demo/','Wrong public URL')
        require(business['approvedByOwner'] is False and business['menu']['approvedForLiveUse'] is False,'False approval flag')
        for route in ['/','/gallery/','/menu/']:
            page.goto(BASE+route,wait_until='networkidle')
            photos=page.locator('img[src*=".webp"]').evaluate_all('(images)=>images.map(i=>i.alt)')
            require(photos and all('photograph' in alt.lower() and 'not a creamcrust product' in alt.lower() for alt in photos),'Inaccurate photo descriptions: '+str(photos))
        source=page.evaluate('window.CREAMCRUST_CATALOG')
        for item in source['items']:
            page.locator(f'.details-button[data-open="{item["id"]}"]').click()
            img=page.locator('.modal-photo img');alt=img.get_attribute('alt')
            if '.webp' in img.get_attribute('src'):require('illustrative photograph' in alt and 'not a CreamCrust product' in alt,'Photo modal alt is misleading')
            else:require('Original' in alt and 'not a product photograph' in alt,'Artwork modal alt is misleading')
            page.keyboard.press('Escape')
        ctx.close()
    check('Public deployment metadata, unapproved facts and all 40 popup image descriptions',metadata_and_alts)
    check('No uncaught errors or network writes from the Studio',lambda:require(not errors and not writes,str(errors+writes)))
    browser.close()
report={'base_url':BASE,'passed':sum(c['status']=='PASS' for c in checks),'failed':sum(c['status']=='FAIL' for c in checks),'checks':checks,'errors':errors,'network_writes':writes}
(OUT/'studio-integrity.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('RESULT:',report['passed'],'passed;',report['failed'],'failed')
sys.exit(bool(report['failed']))
