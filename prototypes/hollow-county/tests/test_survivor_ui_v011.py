"""Hollow County V0.11 browser smoke / UI regression tests.
Install Playwright + Chromium. Run with:
python -m pip install playwright
python -m playwright install chromium
python prototypes/hollow-county/tests/test_survivor_ui_v011.py
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "v011" / "index.html").read_text()
HTML = HTML.replace(
    "window.HollowCounty={",
    "window.__uiQA={get game(){return game},setContainer(id){containerID=id}};window.HollowCounty={",
    1,
)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    for label, width, height in [("desktop", 1280, 820), ("touch-mobile", 390, 844)]:
        page = browser.new_page(
            viewport={"width": width, "height": height},
            has_touch=label == "touch-mobile",
            is_mobile=label == "touch-mobile",
        )
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto("about:blank")
        page.evaluate(
            'Object.defineProperty(window,"localStorage",{value:{getItem:k=>window._mem?.[k]||null,setItem:(k,v)=>(window._mem??={})[k]=v}})'
        )
        page.set_content(HTML, wait_until="load")
        page.locator("#newGame").click()
        assert page.evaluate("HollowCounty.state") == "play"
        assert page.locator("#moodleRail .moodle-icon").count() == 12
        assert page.locator("#pvpSafety").is_disabled()
        page.evaluate("HollowCounty.openInventory()")
        assert page.locator("#inventoryScreen").is_visible()
        page.locator("#inventoryClose").click()
        assert not page.locator("#inventoryScreen").is_visible()
        assert page.evaluate("HollowCounty.state") == "play"
        page.evaluate("HollowCounty.openCharacter('health')")
        assert page.locator(".body-zone").count() == 11
        page.locator("#skillsClose").click()
        page.evaluate("HollowCounty.openFullMap()")
        page.locator("#mapCanvasFull").click(position={"x": 100, "y": 100})
        assert page.evaluate("HollowCounty.ui.mapMarkers") == 1
        page.locator("#mapClose").click()
        page.evaluate("HollowCounty.setTimeRate(2)")
        assert page.evaluate("HollowCounty.ui.rate") == 2
        page.evaluate("HollowCounty.setTimeRate(1)")
        page.evaluate("HollowCounty.openFurnitureMenu()")
        assert page.locator("#furniturePanel").is_visible()
        page.locator("#furnitureClose").click()
        # Touch double-click transfers the full searched stack, not just one item.
        page.evaluate("""() => {
           const g=__uiQA.game,c=g.containers[0];
           g.p.bag={pipe:1,axe:1,bandage:1,torch:1,watch:1};
           c.items={can:4};
           g.p.x=c.x+.4;g.p.y=c.y+.4;
           __uiQA.setContainer(c.id)
        }""")
        page.evaluate("HollowCounty.openInventory()")
        target=page.locator('[data-item="can"][data-side="container"]')
        target.click()
        page.wait_for_timeout(80)
        target=page.locator('[data-item="can"][data-side="container"]')
        target.click()
        assert page.evaluate("__uiQA.game.p.bag.can") == 4
        page.locator('[data-item="axe"][data-side="pack"]').click()
        page.locator('#inventoryEquipment [data-equip-slot="primary"]').click()
        assert page.evaluate("HollowCounty.ui.equipment.primary") == "axe"
        page.locator('[data-item="axe"][data-side="pack"]').click()
        page.locator('#inventoryHotbar [data-hotbar-index="4"]').click()
        assert page.evaluate("HollowCounty.ui.hotbar[4]") == "axe"
        page.locator("#inventoryClose").click()
        page.evaluate("HollowCounty.save()")
        page.evaluate("HollowCounty.load()")
        assert page.evaluate("HollowCounty.ui.mapMarkers") == 1
        assert page.evaluate("HollowCounty.ui.hotbar[4]") == "axe"
        assert page.evaluate("HollowCounty.state") == "play"
        assert not errors, errors
        print(label, "PASS")
        page.close()
    browser.close()
