from playwright.sync_api import sync_playwright


def first_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        context = browser.new_context()

        page = context.new_page()

        page.goto("https://www.facebook.com")

        print("請手動登入 Facebook")

        input("登入完成後按 Enter...")

        context.storage_state(path="facebook.json")

        print("登入資訊已儲存到 facebook.json")

        browser.close()

def second_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        context = browser.new_context(
            storage_state="facebook.json"
        )

        page = context.new_page()

        group = "/groups/628916884757960"

        page.goto("https://www.facebook.com"+group)

        input("Press Enter...")

        browser.close()

if __name__ == "__main__":
    second_login()