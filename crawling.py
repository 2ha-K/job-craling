from playwright.sync_api import sync_playwright
import random
from datetime import datetime, timedelta
from urllib.parse import parse_qs, unquote, urlparse

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
    'a[href*="/groups/"][href*="/posts/"]',
    'a[href*="/permalink/"]',
    'a[href*="story_fbid"]',
    'a[href*="multi_permalinks"]',
    'a[href*="/photo.php"]',
    'a[href*="/videos/"]',
]

DATE_TEXT_PATTERN = re.compile(
    r"(剛剛|昨天|\d+\s*(分鐘|小時|天|週|周|秒)|"
    r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日|"
    r"\d{1,2}\s*月\s*\d{1,2}\s*日|"
    r"just now|\d+\s*(m|h|d|w|min|hr|day|week)s?\b|"
    r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec))",
    re.IGNORECASE
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
    text = re.sub(r"^[\W_]+|[\W_]+$", "", text)
    text = text.replace("週", "周")
    lower_text = text.lower()

    if text == "剛剛" or lower_text == "just now":
        return now.isoformat(timespec="seconds")

    relative_match = (
        re.search(r"(\d+)\s*(秒|分鐘|小時|天|周)\s*前?", text)
        or re.search(
            r"(\d+)\s*(m|h|d|w|min|hr|day|week)s?\s*(ago)?\b",
            lower_text
        )
    )
    if relative_match:
        amount = int(relative_match.group(1))
        unit = relative_match.group(2)
        if unit == "秒":
            value = now - timedelta(seconds=amount)
        elif unit in {"分鐘", "m", "min"}:
            value = now - timedelta(minutes=amount)
        elif unit in {"小時", "h", "hr"}:
            value = now - timedelta(hours=amount)
        elif unit in {"天", "d", "day"}:
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

    for date_format in (
        "%B %d, %Y at %I:%M %p",
        "%b %d, %Y at %I:%M %p",
    ):
        try:
            value = datetime.strptime(text, date_format)
        except ValueError:
            continue

        return value.isoformat(timespec="seconds")

    for date_format in (
        "%B %d, %Y at %I:%M %p",
        "%b %d, %Y at %I:%M %p",
        "%B %d, %Y",
        "%b %d, %Y",
    ):
        date_text = re.sub(
            r"\s+at\s+",
            f", {now.year} at ",
            text,
            flags=re.IGNORECASE
        )
        if date_text == text:
            date_text = f"{text}, {now.year}"

        try:
            value = datetime.strptime(date_text, date_format)
        except ValueError:
            continue

        return value.isoformat(timespec="seconds")

    return None


def safe_get_attribute(locator, attribute):
    try:
        return locator.get_attribute(attribute, timeout=500)
    except Exception:
        return None


def safe_inner_text(locator):
    try:
        return locator.inner_text(timeout=500)
    except Exception:
        return None


def get_time_candidates(post):
    candidates = []

    try:
        candidates.extend(
            post.evaluate(
                """element => {
                    const values = [];
                    const attrs = [
                        "datetime",
                        "aria-label",
                        "title",
                        "data-tooltip-content",
                        "data-tooltip",
                        "aria-description"
                    ];
                    const nodes = element.querySelectorAll("a, abbr, span, time");

                    for (const node of nodes) {
                        for (const attr of attrs) {
                            const value = node.getAttribute(attr);
                            if (value) values.push(value);
                        }

                        if (node.innerText) values.push(node.innerText);
                        if (node.textContent) values.push(node.textContent);
                    }

                    return values;
                }"""
            )
        )
    except Exception:
        pass

    return candidates


def get_post_links(post):
    links = []

    for selector in POST_LINK_SELECTORS:
        locator = post.locator(selector)
        for i in range(locator.count()):
            links.append(locator.nth(i))

    return links


def normalize_facebook_url(href):
    if not href:
        return None

    href = href.strip()

    if href.startswith("https://l.facebook.com/l.php"):
        query = parse_qs(urlparse(href).query)
        if query.get("u"):
            href = unquote(query["u"][0])

    if href.startswith("/"):
        href = "https://www.facebook.com" + href

    parsed = urlparse(href)
    if not parsed.netloc:
        return None

    host = parsed.netloc.lower()
    if not host.endswith("facebook.com") and not host.endswith("fb.com"):
        return None

    clean_url = parsed._replace(
        scheme="https",
        netloc="www.facebook.com",
        fragment=""
    )

    query = parse_qs(clean_url.query)
    keep_query = {}
    for key in ("story_fbid", "id", "fbid", "multi_permalinks"):
        if key in query:
            keep_query[key] = query[key][0]

    query_text = "&".join(
        f"{key}={value}"
        for key, value in keep_query.items()
    )

    return clean_url._replace(query=query_text).geturl().rstrip("/")


def score_post_url(url, group_id=None):
    if not url:
        return -1

    score = 0
    parsed = urlparse(url)
    path = parsed.path
    query = parse_qs(parsed.query)

    if group_id and f"/groups/{group_id}/" in path:
        score += 50
    if "/groups/" in path and "/posts/" in path:
        score += 45
    if "/permalink/" in path:
        score += 35
    if "story_fbid" in query:
        score += 35
    if "multi_permalinks" in query:
        score += 30
    if re.search(r"/posts/\d+", path):
        score += 25
    if "fbid" in query:
        score += 15
    if "/photo.php" in path or "/videos/" in path:
        score += 10
    if any(
        noise in path
        for noise in (
            "/comment/",
            "/comments/",
            "/reactions/",
            "/shares/",
            "/profile.php",
            "/people/",
        )
    ):
        score -= 40

    return score


def get_url_candidates(post):
    candidates = []

    for link in get_post_links(post):
        href = safe_get_attribute(link, "href")
        if href:
            candidates.append(href)

    try:
        candidates.extend(
            post.evaluate(
                """element => {
                    const values = [];
                    const attrs = ["href", "ajaxify", "data-hovercard", "data-ft"];
                    const nodes = element.querySelectorAll("a, span, div");

                    for (const node of nodes) {
                        for (const attr of attrs) {
                            const value = node.getAttribute(attr);
                            if (value) values.push(value);
                        }

                        const onclick = node.getAttribute("onclick");
                        if (onclick) values.push(onclick);
                    }

                    return values;
                }"""
            )
        )
    except Exception:
        pass

    return candidates


def extract_urls_from_text(text):
    if not text:
        return []

    raw_urls = re.findall(
        r"https?://(?:www\.|m\.|mbasic\.|web\.)?facebook\.com[^\s\"'<>]+|"
        r"/(?:groups|posts|permalink|photo\.php|watch|videos)[^\s\"'<>]+",
        text
    )

    return [normalize_facebook_url(url) for url in raw_urls]


def extract_post_ids_from_text(text):
    if not text:
        return []

    ids = []
    patterns = [
        r'"top_level_post_id"\s*:\s*"(\d+)"',
        r'"post_id"\s*:\s*"(\d+)"',
        r'"story_fbid"\s*:\s*"(\d+)"',
        r'top_level_post_id[=:"\\]+(\d+)',
        r'post_id[=:"\\]+(\d+)',
        r'story_fbid[=:"\\]+(\d+)',
        r'/posts/(\d+)',
        r'/permalink/(\d+)',
        r'[?&]story_fbid=(\d+)',
        r'[?&]multi_permalinks=(\d+)',
    ]

    for pattern in patterns:
        ids.extend(re.findall(pattern, text))

    result = []
    seen_ids = set()
    for post_id in ids:
        if post_id in seen_ids:
            continue
        seen_ids.add(post_id)
        result.append(post_id)

    return result


def get_url(post, group_id=None, debug=False):
    candidates = []

    for candidate in get_url_candidates(post):
        normalized = normalize_facebook_url(candidate)
        if normalized:
            candidates.append(normalized)

        candidates.extend(
            url for url in extract_urls_from_text(candidate) if url
        )

        if group_id:
            candidates.extend(
                f"https://www.facebook.com/groups/{group_id}/posts/{post_id}"
                for post_id in extract_post_ids_from_text(candidate)
            )

    unique_candidates = []
    seen_urls = set()
    for candidate in candidates:
        if candidate in seen_urls:
            continue
        seen_urls.add(candidate)
        unique_candidates.append(candidate)

    scored_candidates = sorted(
        (
            (score_post_url(candidate, group_id), candidate)
            for candidate in unique_candidates
        ),
        reverse=True
    )

    for score, candidate in scored_candidates:
        if score > 0:
            return candidate

    print("找不到貼文連結")
    if debug:
        print("URL 候選:")
        for score, candidate in scored_candidates[:20]:
            print(f"- score={score}: {candidate}")

    return None

def get_timestamp(post, debug=False):
    links = get_post_links(post)
    scanned_candidates = []

    for link in links:
        candidates = [
            safe_get_attribute(link, "datetime"),
            safe_get_attribute(link, "aria-label"),
            safe_get_attribute(link, "title"),
            safe_get_attribute(link, "data-tooltip-content"),
            safe_get_attribute(link, "data-tooltip"),
            safe_inner_text(link),
        ]

        for candidate in candidates:
            if candidate:
                scanned_candidates.append(candidate)
            timestamp = normalize_facebook_time(candidate)
            if timestamp:
                return timestamp

    for candidate in get_time_candidates(post):
        if not candidate or not DATE_TEXT_PATTERN.search(candidate):
            continue

        scanned_candidates.append(candidate)
        timestamp = normalize_facebook_time(candidate)
        if timestamp:
            return timestamp

    post_text = safe_inner_text(post) or ""
    for line in post_text.splitlines():
        line = line.strip()
        if DATE_TEXT_PATTERN.search(line):
            scanned_candidates.append(line)
            timestamp = normalize_facebook_time(line)
            if timestamp:
                return timestamp

    print("找不到時間")
    if debug:
        print("時間候選:")
        for candidate in scanned_candidates[:20]:
            print(f"- {candidate}")
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
            "https://www.facebook.com/groups/"+group_id+"/?sorting_setting=RECENT_ACTIVITY"
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
                        "datetime": get_timestamp(post, debug=debug),
                        "content": clean_text,
                        "url": get_url(post, group_id=group_id, debug=debug),
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
