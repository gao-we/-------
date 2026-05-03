import argparse
import json
import time
from pathlib import Path

import yaml
from playwright.sync_api import sync_playwright


def _locator_by_text(page, text):
    return page.get_by_text(text, exact=False).first


def run_step(page, step, base_url):
    action = step["action"]
    if action == "goto":
        page.goto(base_url, wait_until="domcontentloaded")
        page.wait_for_timeout(1200)
    elif action == "expect_text":
        _locator_by_text(page, step["value"]).wait_for(timeout=15000)
    elif action == "expect_any_text":
        values = step["values"]
        end = time.time() + 15
        while time.time() < end:
            for v in values:
                if page.get_by_text(v, exact=False).count() > 0:
                    return
            time.sleep(0.3)
        raise AssertionError(f"None of expected texts found: {values}")
    elif action == "click_text":
        _locator_by_text(page, step["value"]).click(timeout=15000)
        page.wait_for_timeout(800)
    elif action == "fill_placeholder":
        page.get_by_placeholder(step["placeholder"]).fill(step["value"])
        page.wait_for_timeout(400)
    elif action == "choose_first_select_option":
        index = int(step["index"])
        sel = page.locator("select").nth(index)
        sel.wait_for(timeout=10000)
        options = sel.locator("option")
        count = options.count()
        chosen = None
        for i in range(count):
            val = options.nth(i).get_attribute("value")
            if val:
                chosen = val
                break
        if not chosen:
            raise AssertionError(f"Select at index {index} has no non-empty option")
        sel.select_option(chosen)
        page.wait_for_timeout(500)
    else:
        raise ValueError(f"Unsupported action: {action}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", default=str(Path(__file__).with_name("awt_scenarios.yaml")))
    args = parser.parse_args()

    data = yaml.safe_load(Path(args.scenario).read_text(encoding="utf-8"))
    base_url = data["base_url"]
    scenarios = data["scenarios"]

    result = {"passed": [], "failed": []}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_default_timeout(15000)
        for sc in scenarios:
            name = sc["name"]
            try:
                for step in sc["steps"]:
                    run_step(page, step, base_url)
                result["passed"].append(name)
                print(f"[PASS] {name}")
            except Exception as e:
                result["failed"].append({"name": name, "error": str(e)})
                print(f"[FAIL] {name}: {e}")
        browser.close()

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
