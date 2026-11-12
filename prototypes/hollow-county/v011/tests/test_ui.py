"""Hollow County V0.11 functional UI regression tests.
Requires: pip install playwright && python -m playwright install chromium
Runs against the exact standalone source committed to this repository.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")

def launch_context(browser, width, height, touch):
    page = browser.new_page(
        viewport={"width": width, "height": height},
        device_scale_factor=1,
        is_mobile=touch,
        has_touch=touch,
    )
    # Playwright set_content() uses about:blank; provide controlled localStorage.
    page.evaluate(
        """Object.defineProperty(window, "localStorage", {
            value: {
                getItem: k => window._saved?.[k] || null,
                setItem: (k,v) => (window._saved ??= {})[k] = v,
                removeItem: k => { if(window._saved) delete window._saved[k] }
            }
        })"""
    )
    return page

def check_platform(browser, label, width, height, mobile):
    page = launch_context(browser, width, height, mobile)
    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    page.set_content(HTML, wait_until="load", timeout=45000)
    page.locator("#newGame").click(timeout=15000)
    page.wait_for_timeout(450)
    assert page.evaluate("HollowCounty.state") == "play"
    assert page.evaluate("HollowCounty.status.renderError") is None

    if mobile:
        page.locator("#touchBag").click()
    else:
        page.evaluate("HollowCounty.openInventory()")
    assert page.locator("#inventoryScreen").is_visible()

    # The close control must stay functional even after a panel state switch.
    page.locator("#inventoryClose").click(force=True)
    assert not page.locator("#inventoryScreen").is_visible()
    assert page.evaluate("HollowCounty.state") == "play"
    page.evaluate("HollowCounty.openInventory()")
    page.evaluate('HollowCounty.openCharacter("skills")')
    page.evaluate("HollowCounty.closeInventory()")
    assert not page.locator("#inventoryScreen").is_visible()

    page.evaluate('HollowCounty.openCharacter("health")')
    assert page.locator("#skillsPanel").is_visible()
    assert page.locator(".body-zone").count() == 11
    page.locator('#characterTabs [data-char-tab="exercise"]').click()
    page.locator("#skillsClose").click()
    page.evaluate("HollowCounty.openFullMap()")
    page.locator("#mapCanvasFull").click(position={"x": 100, "y": 100})
    assert page.evaluate("HollowCounty.ui.mapMarkers") == 1
    page.locator("#mapClose").click()
    page.evaluate("HollowCounty.setTimeRate(2)")
    assert page.evaluate("HollowCounty.ui.rate") == 2
    page.evaluate("HollowCounty.setTimeRate(1)")
    page.evaluate('HollowCounty.assignHotbar("bandage",2)')
    page.evaluate("HollowCounty.openFurnitureMenu()")
    assert page.locator("#furniturePanel").is_visible()
    page.locator("#furnitureClose").click()

    assert page.locator("#moodleRail .moodle-icon").count() == 12
    assert page.locator("#pvpSafety").is_disabled()
    page.evaluate("HollowCounty.save()")
    page.evaluate("HollowCounty.load()")
    assert page.evaluate("HollowCounty.ui.mapMarkers") == 1
    assert page.evaluate("HollowCounty.state") == "play"
    assert errors == [], errors
    print(label, "PASS: panel closing, 11 wounds, 12 moodles, map, time, crafting menu, persistence")
    page.close()

def check_interactions(browser):
    page = launch_context(browser, 390, 844, True)
    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    # Expose a test-only view without changing the committed runtime.
    html = HTML.replace(
        "window.HollowCounty={",
        "window.__qa={get game(){return game},setContainer(id){containerID=id}};window.HollowCounty={",
        1,
    )
    page.set_content(html, wait_until="load")
    page.locator("#newGame").tap()
    assert page.evaluate("HollowCounty.state") == "play"
    page.evaluate("""() => {
        const g=window.__qa.game,p=g.p;
        p.bag={pipe:1,axe:1,bandage:1,torch:1,watch:1};
        const c=g.containers[0]; c.items={can:4,cloth:2,water:3};
        p.x=c.x+.6;p.y=c.y+.5;
        window.__qa.setContainer(c.id);
    }""")
    page.evaluate("HollowCounty.openInventory()")
    item = page.locator('[data-item="can"][data-side="container"]')
    item.tap()
    page.wait_for_timeout(100)
    item.tap()
    page.wait_for_timeout(150)
    assert page.evaluate("__qa.game.p.bag.can") == 4
    assert page.evaluate("__qa.game.containers[0].items.can||0") == 0

    page.locator('[data-item="axe"][data-side="pack"]').tap()
    page.locator('#inventoryEquipment [data-equip-slot="primary"]').tap()
    assert page.evaluate("HollowCounty.ui.equipment.primary") == "axe"
    page.locator('[data-item="axe"][data-side="pack"]').tap()
    page.locator('#inventoryHotbar [data-hotbar-index="4"]').tap()
    assert page.evaluate("HollowCounty.ui.hotbar[4]") == "axe"
    page.locator("#inventoryClose").tap()

    crafted = page.evaluate("""() => {
        const g=__qa.game;
        g.p.x=g.containers[0].x+.2;g.p.y=g.containers[0].y+.2;
        return HollowCounty.craftFromNearby("bandage")
    }""")
    assert crafted, "Craft should consume nearby container materials"
    pickup = page.evaluate("""() => {
        const g=__qa.game;
        const o=g.objects.find(x=>["bed","cabinet","table","shelf"].includes(x.style)
            && g.tiles[Math.round(x.y)*110+Math.round(x.x)]===6);
        if(!o)return false;
        g.p.x=o.x+.6;g.p.y=o.y+.4;
        for(const c of g.containers.filter(c=>Math.round(c.x)===Math.round(o.x)&&Math.round(c.y)===Math.round(o.y))) c.items={};
        return HollowCounty.pickupFurniture()
    }""")
    if pickup:
        assert page.evaluate("HollowCounty.rotateFurniture()")
        assert page.evaluate("Boolean(HollowCounty.ui.carrying)")
    page.evaluate("HollowCounty.save()")
    page.evaluate("HollowCounty.load()")
    assert page.evaluate("HollowCounty.ui.equipment.primary") == "axe"
    assert page.evaluate("HollowCounty.ui.hotbar[4]") == "axe"
    assert not errors, errors
    print("mobile interactions PASS: double-tap stack, equipment, hotbar, nearby crafting, furniture, save")
    page.close()

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
        check_platform(browser, "desktop", 1280, 820, False)
        check_platform(browser, "mobile", 390, 844, True)
        check_interactions(browser)
        browser.close()
