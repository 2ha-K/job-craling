from playwright.sync_api import sync_playwright
import random

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

def inspect():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        context = browser.new_context(
            storage_state="facebook.json"
        )

        page = context.new_page()

        group = "/groups/628916884757960"

        page.goto("https://www.facebook.com"+group)

        page.pause()

        input("Press Enter...")
        browser.close()


import re


def clean_lines(text: str):
    blacklist = {
        "Facebook",
        "公開留言……",
        "回覆",
        "分享",
        "查看更多留言",
        "查看更多回答",
        "顯示更多",
    }

    result = []

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        if line in blacklist:
            continue

        if len(line) == 1:
            continue

        # 移除影片時間
        line = re.sub(
            r"\d+:\d+\s*/\s*\d+:\d+",
            "",
            line
        ).strip()

        if not line:
            continue

        result.append(line)

    return result


def service():

    keywords = [
        "求老師",
        "徵老師",
        "找家教",
        "徵家教",
        "徵學生",
        "找老師",
    ]

    results = []
    seen = set()

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        context = browser.new_context(
            storage_state="facebook.json"
        )

        page = context.new_page()

        page.goto(
            "https://www.facebook.com/groups/628916884757960"
        )

        input("確認登入後按 Enter...")

        for scroll_round in range(30):

            print(f"掃描第 {scroll_round + 1} 次")

            posts = page.locator(
                '[role="feed"] > div'
            )

            for i in range(posts.count()):

                try:

                    text = posts.nth(i).inner_text()

                    if len(text) < 20:
                        continue

                    lines = clean_lines(text)

                    if len(lines) < 2:
                        continue

                    clean_text = "\n".join(lines)

                    if not any(
                        keyword in clean_text
                        for keyword in keywords
                    ):
                        continue

                    # 作者
                    author = lines[0]

                    # 前五行當特徵
                    signature = "\n".join(
                        lines[:5]
                    )

                    post_key = (
                        author + "|" + signature
                    )

                    if post_key in seen:
                        continue

                    seen.add(post_key)

                    results.append({
                        "author": author,
                        "content": clean_text
                    })

                    print(
                        f"新增: {author}"
                    )

                except Exception as e:
                    print(e)

            page.mouse.wheel(
                0,
                random.randint(300, 500)
            )

            page.wait_for_timeout(
                random.randint(1000, 1500)
            )

        browser.close()

    print("\n")
    print("=" * 80)
    print(f"共找到 {len(results)} 篇")
    print("=" * 80)

    for idx, post in enumerate(
            results,
            start=1
    ):
        print("\n")
        print(f"貼文 {idx}")
        print("-" * 80)
        print(post["content"][:1500])

if __name__ == "__main__":
    service()