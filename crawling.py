from playwright.sync_api import sync_playwright
import random
from datetime import datetime, timedelta

def login():
    """
    此功能用於第一次登入，然後紀錄cookie
    """
    with sync_playwright() as p:
        #headless=False：顯示瀏覽器視窗，方便觀察和除錯。
        #如果改成 headless=True，瀏覽器會在背景執行，不會出現任何視窗，但所有操作（開網頁、點擊、抓資料等）仍然會照常進行。
        browser = p.chromium.launch(headless=False)

        #Context：瀏覽器中的一個獨立使用者環境（Profile），保存 Cookie、登入狀態、Local Storage 等。
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

POST_LINK_SELECTORS = [
    'a[href*="/posts/"]',
    'a[href*="/permalink/"]',
    'a[href*="story_fbid"]',
]

DATE_TEXT_PATTERN = re.compile(
    r"(剛剛|昨天|\d+\s*(分鐘|小時|天|週|周)|"
    r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日|"
    r"\d{1,2}\s*月\s*\d{1,2}\s*日)"
)


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


def normalize_facebook_time(text, now=None):
    if not text:
        return None

    now = now or datetime.now()
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace("週", "周")

    if text == "剛剛":
        return now.isoformat(timespec="seconds")

    relative_match = re.search(r"(\d+)\s*(分鐘|小時|天|周)", text)
    if relative_match:
        amount = int(relative_match.group(1))
        unit = relative_match.group(2)
        if unit == "分鐘":
            value = now - timedelta(minutes=amount)
        elif unit == "小時":
            value = now - timedelta(hours=amount)
        elif unit == "天":
            value = now - timedelta(days=amount)
        else:
            value = now - timedelta(weeks=amount)
        return value.isoformat(timespec="seconds")

    time_match = re.search(
        r"(上午|下午)?\s*(\d{1,2})[:：](\d{2})",
        text
    )
    hour = 0
    minute = 0
    if time_match:
        period, hour_text, minute_text = time_match.groups()
        hour = int(hour_text)
        minute = int(minute_text)
        if period == "下午" and hour < 12:
            hour += 12
        elif period == "上午" and hour == 12:
            hour = 0

    if "昨天" in text:
        value = now - timedelta(days=1)
        return value.replace(
            hour=hour,
            minute=minute,
            second=0,
            microsecond=0
        ).isoformat(timespec="seconds")

    full_date_match = re.search(
        r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日",
        text
    )
    if full_date_match:
        year, month, day = map(int, full_date_match.groups())
        return datetime(
            year,
            month,
            day,
            hour,
            minute
        ).isoformat(timespec="seconds")

    month_day_match = re.search(
        r"(\d{1,2})\s*月\s*(\d{1,2})\s*日",
        text
    )
    if month_day_match:
        month, day = map(int, month_day_match.groups())
        return datetime(
            now.year,
            month,
            day,
            hour,
            minute
        ).isoformat(timespec="seconds")

    return None


def get_post_links(post):
    links = []

    for selector in POST_LINK_SELECTORS:
        locator = post.locator(selector)
        for i in range(locator.count()):
            links.append(locator.nth(i))

    return links


def get_url(post):
    links = get_post_links(post)

    if not links:
        print("找不到貼文連結")
        return None

    href = links[0].get_attribute("href")

    if not href:
        print("href 是 None")
        return None

    if href.startswith("/"):
        url = "https://www.facebook.com" + href
    else:
        url = href

    return url.split("?")[0]

def get_timestamp(post):
    links = get_post_links(post)

    for link in links:
        candidates = [
            link.get_attribute("datetime"),
            link.get_attribute("aria-label"),
            link.get_attribute("title"),
            link.inner_text(timeout=1000),
        ]

        for candidate in candidates:
            timestamp = normalize_facebook_time(candidate)
            if timestamp:
                return timestamp

    post_text = post.inner_text(timeout=1000)
    for line in post_text.splitlines():
        line = line.strip()
        if DATE_TEXT_PATTERN.search(line):
            timestamp = normalize_facebook_time(line)
            if timestamp:
                return timestamp

    print("找不到時間")
    return None

import hashlib

def service(
        group_id,
        debug=False,
        keywords=None,  #不是家教
        count=30
):




    if keywords is None:
        keywords = [
            "徵學生",
            "社團動態消息排序方式",
            "回應了這張相片"
        ]

    results = []
    seen = set()

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        context = browser.new_context(
            storage_state="facebook.json"
        )

        page = context.new_page()

        page.goto(
            "https://www.facebook.com/groups/"+group_id
        )
        group_name = page.title()

        input("按下Enter開始掃描")

        for scroll_round in range(count):
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

                    if any(
                        keyword in clean_text
                        for keyword in keywords
                    ):
                        continue


                    post_key = hashlib.sha256(
                        (author+clean_text).encode("utf-8")
                    ).hexdigest()

                    if post_key in seen:
                        continue

                    seen.add(post_key)

                    results.append({
                        "post_key": post_key,
                        "author": author,
                        "datetime": get_timestamp(post),
                        "content": clean_text,
                        "url": get_url(post),
                        "group_url": "https://www.facebook.com/groups/"+group_id,
                        "group_name": group_name
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
        print(f"{post['datetime']}")
        print(post["content"][:1500])
        print(f"url: {post['url']}")


    return results





if __name__ == "__main__":
    service("628916884757960", debug=False)
