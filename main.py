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
    # 建立黑名單
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

        line = line.strip() # 去除空白

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

        # 移除顯示較少為尾部和之後的
        if "顯示較少" in line:
            line = line.split("顯示較少")[0].strip()

            if line:
                result.append(line)

            return result

        # +2 +8 +15
        if re.fullmatch(r"\+\d+", line):
            return result

        # 67 155 31
        if line.isdigit():
            return result

        # 1小時 2天 3週
        if re.fullmatch(r"\d+(分鐘|小時|天|週)", line):
            if len(result) >= 2:
                result.pop()
                result.pop()
            return result


        result.append(line)


    return result


def get_url(post):
    link = post.locator('a[href*="/posts/"]').first

    if link.count() == 0:
        print("找不到 /posts/ 連結")
        return None

    href = link.get_attribute("href")

    if not href:
        print("href 是 None")
        return None

    if href.startswith("/"):
        url = "https://www.facebook.com" + href
    else:
        url = href

    return url.split("?")[0]

def service(group_id, debug=False):

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
            "https://www.facebook.com/groups/"+group_id
        )

        input("按下Enter開始掃描")

        for scroll_round in range(30):
            double_check = False
            print(f"掃描第 {scroll_round + 1} 次")

            posts = page.locator(
                '[role="feed"] > div'
            ) # CSS Selector 語法找出特定的div
            if debug: print(f"count: {posts.count()}")
            for i in range(posts.count()):

                try:
                    post = posts.nth(i)
                    text = post.inner_text()
                    if "…… 查看更多" in text:
                        if debug:
                            print(f"發現{clean_lines(text)[0]}含有查看更多")
                            input(f"Press Enter to open")

                        see_more = post.get_by_text(
                            "查看更多",
                            exact=True
                        )
                        for j in range(see_more.count()):

                            btn = see_more.nth(j)

                            if btn.is_visible():
                                btn.click(timeout=1000)
                                double_check = True
                                break
                        continue
                    elif "顯示更多" in text:
                        if debug:
                            print(f"發現{clean_lines(text)[0]}含有顯示更多")
                            input(f"Press Enter to open")

                        see_more = post.get_by_text(
                            "顯示更多",
                            exact=True
                        )
                        for j in range(see_more.count()):

                            btn = see_more.nth(j)

                            if btn.is_visible():
                                btn.click(timeout=1000)
                                double_check = True
                                break
                        continue


                    # if len(text) < 20:
                    #     continue

                    lines = clean_lines(text)

                    if len(lines) < 2:
                        continue

                    clean_text = "\n".join(lines)

                    # 作者
                    author = lines[0]

                    if not any(
                        keyword in clean_text
                        for keyword in keywords
                    ):
                        continue



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
                        "content": clean_text,
                        "url": get_url(post)
                    })

                    print(
                        f"新增: {author}"
                    )

                except Exception as e:
                    print(e)
            if double_check:
                if debug: print("發現查看更多按鈕準備重新掃描")
                continue

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
        print(f"url: {post['url']}")

if __name__ == "__main__":
    service("628916884757960", debug=False)