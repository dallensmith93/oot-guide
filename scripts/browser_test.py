"""Browser integration checks against the committed, actual site data.

Run: python scripts/browser_test.py [--browser /path/to/chrome]
Requires the optional Python playwright package and a local Chrome executable.
No dependency is required to run the production website.
"""
import argparse
import functools
import http.server
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
KEY = "hyrule-field-guide.progress.v1"


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def main():
    parser = argparse.ArgumentParser()
    browser_candidates = [os.environ.get("CHROME_PATH")]
    browser_candidates += [shutil.which(name) for name in ["google-chrome", "chromium", "chromium-browser", "chrome"]]
    browser_candidates += [str(Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Google/Chrome/Application/chrome.exe"), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    browser_default = next((candidate for candidate in browser_candidates if candidate and Path(candidate).is_file()), None)
    parser.add_argument("--browser", default=browser_default, help="Local Chromium/Chrome executable; defaults to CHROME_PATH or platform discovery")
    args = parser.parse_args()
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(QuietHandler, directory=str(ROOT / "site")))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}/"
    passed, skipped, errors = [], [], []
    artifacts = ROOT / "test-results"
    artifacts.mkdir(exist_ok=True)
    try:
        with sync_playwright() as p, tempfile.TemporaryDirectory() as temp:
            browser = p.chromium.launch(**({"executable_path":args.browser} if args.browser else {}), headless=True)
            context = browser.new_context(viewport={"width": 1440, "height": 1000}, accept_downloads=True)
            page = context.new_page()
            page.on("pageerror", lambda err: errors.append(str(err)))
            page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
            page.goto(origin)
            page.wait_for_function("window.GUIDE && document.querySelector('h1')")
            data = page.evaluate("({sections:GUIDE.sections.map(s=>s.id), objectives:GUIDE.objectives.map(o=>({id:o.id,section:o.section,region:o.region,age:o.age,type:o.type,name:o.name,optional:o.optional}))})")
            for asset in ["index.html", "app.js", "styles.css", "data.js", "print.html"]:
                assert context.request.get(origin + asset).status == 200, asset
            passed.append("Configured publish-directory HTML and all runtime assets return HTTP 200")
            print_page = context.new_page()
            print_page.goto(origin + "print.html")
            assert print_page.locator("body").inner_text().strip()
            for size in [{"width":1440,"height":1000},{"width":390,"height":844}]:
                print_page.set_viewport_size(size)
                assert print_page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"), ("Full print guide", size)
            print_page.close()
            passed.append("Standalone full print guide renders at desktop and phone widths without overflow")
            views = ["start", "continue", "route", "dungeons", "collectibles", "inventory", "warnings", "cleanup", "controls", "sources"]
            for view in views:
                page.goto(origin + "#" + view)
                assert page.locator("h1").count() == 1, view
                assert page.locator("#main").inner_text().strip(), view
            for sid in data["sections"]:
                page.goto(origin + "#section/" + sid)
                assert "Section unavailable" not in page.locator("h1").inner_text(), sid
            passed.append(f"All {len(views)} main views and {len(data['sections'])} actual route sections render")
            episode_data=page.evaluate('GUIDE.episodes')
            assert len(episode_data)==25
            page.goto(origin+'#route')
            assert page.locator('#main a[href^="#episode/"]').count()==25
            for ep in episode_data:
                page.goto(origin+'#episode/'+ep['id'])
                assert page.locator('h1').count()==1
                assert ep['title'] in page.locator('h1').inner_text()
                expected_ids=page.evaluate('(ep)=>GUIDE.objectives.filter(o=>ep.sections.includes(o.section)).map(o=>o.id)',ep)
                actual_ids=page.locator('[data-objective]').evaluate_all('els=>els.map(el=>el.dataset.objective)')
                assert set(actual_ids)==set(expected_ids) and len(actual_ids)==len(set(actual_ids))
            page.goto(origin+'#episode/ep01')
            page.get_by_role('link',name='Next episode',exact=True).click()
            page.wait_for_function("location.hash==='#episode/ep02'")
            page.wait_for_function("document.querySelector('h1').textContent===GUIDE.episodes[1].title")
            page.get_by_role('link',name='Previous episode',exact=True).click()
            page.wait_for_function("location.hash==='#episode/ep01'")
            passed.append('Exactly 25 episode pages render all assigned objectives once, with working episode navigation')
            page.goto(origin + "#section/%E0%A4%A")
            assert "Section unavailable" in page.locator("h1").inner_text()
            passed.append("Malformed encoded route links fail safely")
            page.goto(origin + "#start")
            page.reload()
            page.keyboard.press("Tab")
            assert page.locator(".skip").evaluate("el=>el===document.activeElement")
            page.keyboard.press("Enter")
            assert page.locator("#main").evaluate("el=>el===document.activeElement")
            assert "Page not found" not in page.locator("#main").inner_text()
            passed.append("Keyboard skip link focuses content without triggering a false route")
            page.locator("#theme").click()
            assert page.locator("body").evaluate("el=>el.classList.contains('dark')")
            page.reload()
            assert page.locator("body").evaluate("el=>el.classList.contains('dark')")
            passed.append("Color theme persists after reload")

            if data["objectives"]:
                objective = data["objectives"][0]
                oid = objective["id"]
                check = f'[data-objective="{oid}"]'
                page.goto(origin + "#collectibles")
                page.locator(check).check()
                assert page.locator(check).is_checked()
                page.reload()
                assert page.locator(check).is_checked()
                saved = page.evaluate("k=>JSON.parse(localStorage.getItem(k))", KEY)
                assert oid in saved["completed"]
                expected_hearts = page.evaluate("k=>{const done=new Set(JSON.parse(localStorage.getItem(k)).completed);return GUIDE.meta.startingHearts+GUIDE.objectives.filter(o=>o.type==='boss'&&done.has(o.id)).length+Math.floor(GUIDE.objectives.filter(o=>o.type==='hp'&&done.has(o.id)).length/4)}", KEY)
                if page.get_by_text("Actual hearts from checked rewards", exact=True).count():
                    assert page.get_by_text("Actual hearts from checked rewards", exact=True).locator("..").locator("strong").inner_text() == str(expected_hearts)
                passed.append("Actual objective checks persist after reload")
                sid = objective.get("section")
                if sid in data["sections"]:
                    page.goto(origin + "#section/" + sid)
                    assert page.locator(check).is_checked()
                    page.locator(check).uncheck()
                    page.goto(origin + "#collectibles")
                    assert not page.locator(check).is_checked()
                    passed.append("Shared objective state synchronizes between route and tracker")
                else:
                    skipped.append("Shared route/tracker synchronization: first objective has no section")
                page.locator(check).check()
                # Search by stable unique ID avoids assumptions about game content.
                page.locator("#search").fill(oid)
                expected_matches = page.evaluate("id=>GUIDE.objectives.filter(o=>JSON.stringify(o).toLowerCase().includes(id.toLowerCase())).length", oid)
                assert page.locator(".objective").count() == expected_matches
                assert page.locator(check).count() == 1
                page.locator("#search").fill("")
                for name in ["region", "age", "type"]:
                    value = objective.get(name)
                    if value:
                        page.locator(f'[name="{name}"]').select_option(value)
                        visible = page.locator(".objective input").evaluate_all("els=>els.map(el=>el.dataset.objective)")
                        assert oid in visible
                        expected = {o["id"] for o in data["objectives"] if o.get(name) == value}
                        assert set(visible) == expected, (name, visible, expected)
                        assert page.locator(f'[name="{name}"]').evaluate("el=>el===document.activeElement")
                        page.locator(f'[name="{name}"]').select_option("")
                page.locator('[name="status"]').select_option("complete")
                assert page.locator(".objective input").evaluate_all("els=>els.every(e=>e.checked)")
                page.locator('[name="status"]').select_option("")
                page.locator('[name="hide"]').check()
                assert page.locator(check).count() == 0
                page.locator('[name="hide"]').uncheck()
                passed.append("Search, region/age/type/status filters, hide-completed, and filter keyboard focus")
                if sid in data["sections"]:
                    page.goto(origin + "#section/" + sid)
                    page.goto(origin + "#continue")
                    assert page.get_by_role("link", name="Resume section").get_attribute("href") == "#section/" + sid
                    target = page.get_by_role("link", name="Go to objective")
                    if target.count():
                        target.click()
                        page.wait_for_selector(".objective")
                        assert page.locator(".objective").count() > 0
                    passed.append("Last-viewed resume and first-incomplete objective navigation")
                page.goto(origin + "#collectibles")
                before = page.evaluate("k=>localStorage.getItem(k)", KEY)
                invalid = Path(temp) / "invalid.json"
                for contents in ['{bad json', json.dumps({"schemaVersion": 999, "completed": []}), json.dumps({"schemaVersion": 1, "gameId": "wrong-game", "completed": []}), json.dumps({"schemaVersion": 1, "gameId": "oot-switch2-remake", "completed": [7]})]:
                    invalid.write_text(contents, encoding="utf-8")
                    page.locator("#import").set_input_files(str(invalid))
                    page.wait_for_function("document.querySelector('#notice').textContent.startsWith('Import rejected:')")
                    assert page.evaluate("k=>localStorage.getItem(k)", KEY) == before
                passed.append("Malformed JSON, wrong schema, wrong game, and invalid IDs reject without overwriting progress")
                with page.expect_download() as event:
                    page.locator("#export").click()
                exported = Path(temp) / "export.json"
                event.value.save_as(str(exported))
                original = json.loads(exported.read_text(encoding="utf-8"))
                page.once("dialog", lambda dialog: dialog.dismiss())
                page.locator("#reset").click()
                assert page.locator(check).is_checked()
                page.once("dialog", lambda dialog: dialog.accept())
                page.locator("#reset").click()
                assert not page.locator(check).is_checked()
                page.locator("#import").set_input_files(str(exported))
                page.wait_for_function("document.querySelector('#notice').textContent.startsWith('Progress imported:')")
                assert page.locator(check).is_checked()
                current = page.evaluate("k=>JSON.parse(localStorage.getItem(k))", KEY)
                assert set(current["completed"]) == set(original["completed"])
                passed.append("JSON export/import round-trip and both reset confirmation choices")
                unknown = "removed-objective-kept-for-compatibility"
                percent_before_unknown = page.locator("#percent").inner_text()
                original["completed"].append(unknown)
                exported.write_text(json.dumps(original), encoding="utf-8")
                page.locator("#import").set_input_files(str(exported))
                page.wait_for_function("document.querySelector('#notice').textContent.includes('unknown IDs preserved')")
                current = page.evaluate("k=>JSON.parse(localStorage.getItem(k))", KEY)
                assert unknown in current["completed"]
                assert page.locator('[data-objective="'+unknown+'"]').count() == 0
                assert page.locator("#percent").inner_text() == percent_before_unknown
                passed.append("Removed/unknown imported objective IDs are retained without creating phantom objectives")
                page.emulate_media(media="print")
                assert not page.locator("#sidebar").is_visible()
                assert not page.locator("header").is_visible()
                assert page.locator(check).is_visible()
                page.emulate_media(media="screen")
                passed.append("Print media hides navigation and preserves checklist content")
                page.pdf(path=str(artifacts / "checklist-print.pdf"), format="A4", print_background=True)
                detail_section = next((sid for sid in data["sections"] if page.evaluate("sid=>GUIDE.sections.find(s=>s.id===sid).details?.length>0", sid)), None)
                if detail_section:
                    page.goto(origin + "#section/" + detail_section)
                    closed_before = page.locator("details:not([open])").count()
                    page.evaluate("window.dispatchEvent(new Event('beforeprint'))")
                    assert page.locator("details:not([open])").count() == 0
                    page.evaluate("window.dispatchEvent(new Event('afterprint'))")
                    assert page.locator("details:not([open])").count() == closed_before
                    page.pdf(path=str(artifacts / "route-print.pdf"), format="A4", print_background=True)
                    assert page.locator("details:not([open])").count() == closed_before
                    passed.append("Route and checklist print PDFs generated; collapsed puzzle states restored after print")
            else:
                skipped.append("Objective interactions, filters, import/export round-trip and route resume: no verified objectives supplied")

            for size in [{"width":1440,"height":1000},{"width":390,"height":844}]:
                page.set_viewport_size(size)
                for view in views:
                    page.goto(origin + "#" + view)
                    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"), (size, view)
            page.set_viewport_size({"width":390,"height":844})
            page.locator("#menu").click()
            assert page.locator("#menu").get_attribute("aria-expanded") == "true"
            assert page.locator("nav").is_visible()
            page.locator('nav a[href="#controls"]').click()
            page.wait_for_function("document.querySelector('#menu').getAttribute('aria-expanded')==='false'")
            assert page.locator("#menu").get_attribute("aria-expanded") == "false"
            passed.append("Desktop and phone view widths avoid horizontal overflow; mobile navigation opens and closes")
            page.goto(origin + "#start")
            page.screenshot(path=str(artifacts / "phone.png"), full_page=True)
            page.set_viewport_size({"width":1440,"height":1000})
            page.screenshot(path=str(artifacts / "desktop.png"), full_page=True)
            assert not errors, errors
            passed.append("No JavaScript page errors or console errors during the checks")
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
    report={"passed":passed,"skipped":skipped,"consoleErrors":errors}
    (artifacts / "browser-results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
