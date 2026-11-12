# Tests the actual standalone JS/HTML browser prototype using a local data URL.
# Requires: pip install playwright pillow; playwright install chromium
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/'v010'/'index.html').read_text()
HTML=HTML.replace('function renderArchitecture(b){','function renderArchitecture(b){window.__exteriors=(window.__exteriors||0)+1;')
HTML=HTML.replace('function interiorEnvelope(b){','function interiorEnvelope(b){window.__cutaways=(window.__cutaways||0)+1;')
HTML=HTML.replace('window.HollowCounty={getBuildingVisibility', 'window.__qa={get game(){return game},render:()=>renderWorld()};window.HollowCounty={getBuildingVisibility')
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    for label,w,h in [('desktop',1280,800),('mobile',390,844)]:
        page=browser.new_page(viewport={'width':w,'height':h},has_touch=label=='mobile',is_mobile=label=='mobile')
        errors=[]
        page.on('pageerror',lambda e: errors.append(str(e)))
        page.evaluate('Object.defineProperty(window,"localStorage",{value:{getItem:k=>window._mem?.[k]||null,setItem:(k,v)=>(window._mem??={})[k]=v}})')
        page.set_content(HTML,wait_until='load')
        page.locator('#newGame').click(timeout=18000)
        assert page.evaluate('HollowCounty.state')=='play'
        b=page.evaluate('HollowCounty.getBuildingData()[0]')
        cases=[
            (b['x']+b['w']*.5,b['y']+b['h']+1.15,'OUTSIDE'),
            (b['x']+b['w']*.5,b['y']+b['h']-.68,'EDGE'),
            (b['x']+b['w']*.5,b['y']+b['h']*.35,'INSIDE'),
            (b['x']+b['w']+1.3,b['y']+b['h']*.5,'OUTSIDE'),
        ]
        for x,y,expected in cases:
            state=page.evaluate('([id,x,y])=>HollowCounty.getBuildingVisibility(id,x,y)',[b['id'],x,y])
            assert state==expected,(label,expected,state,x,y)
            page.evaluate('([x,y])=>{window.__qa.game.p.x=x;window.__qa.game.p.y=y;window.__exteriors=0;window.__cutaways=0;window.__qa.render()}',[x,y])
            drawn=page.evaluate('({exteriors:window.__exteriors,cutaways:window.__cutaways,error:window.__hcLastError||null})')
            assert (drawn['cutaways']>0)==(expected=='INSIDE'),(label,expected,drawn)
            assert drawn['error'] is None
        if label=='mobile':
            page.locator('#touchBag').click(force=True)
        else:
            page.keyboard.press('i')
        assert page.evaluate('HollowCounty.state')=='inventory'
        assert not errors,errors
        print(label,'PASS: outside roof remains, only interior cutaway, inventory')
        page.close()
    browser.close()
