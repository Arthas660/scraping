from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from article_parser import parse_html
from storage import create_output, save_articles

FEED_URL = "https://www.ukrinform.ua/rubric-world/block-lastnews"
POST_SELECTOR = ".infinite-scroll article[data-id]"


def ask_count():
    while True:
        value = input("Скільки останніх статей зберегти? ").strip()
        try:
            count = int(value)
            if count > 0:
                return count
        except ValueError:
            pass
        print("Введи ціле число більше нуля.")


def get_topics(page, limit):
    posts = page.locator(POST_SELECTOR)
    posts.first.wait_for(state="visible", timeout=60_000)
    topics = []
    seen = set()

    while len(topics) < limit:
        soup = BeautifulSoup(page.content(), "html.parser")
        for post in soup.select(POST_SELECTOR):
            link = post.select_one("h2 a[href]")
            if link is None:
                continue
            url = urljoin(page.url, link["href"])
            if urlparse(url).hostname != "www.ukrinform.ua" or url in seen:
                continue
            title = link.get_text(" ", strip=True)
            if not title:
                continue
            seen.add(url)
            topics.append({"title": title, "url": url})
            if len(topics) >= limit:
                return topics

        before = posts.count()
        if before == 0:
            break
        loaded = False
        for _ in range(3):
            posts.last.scroll_into_view_if_needed()
            page.evaluate("window.scrollBy(0, window.innerHeight)")
            try:
                page.wait_for_function(
                    "args => document.querySelectorAll(args.selector).length > args.count",
                    arg={"selector": POST_SELECTOR, "count": before},
                    timeout=10_000,
                )
                loaded = True
                print(f"Довантажено записів у стрічці: {posts.count()}")
                break
            except PlaywrightTimeoutError:
                pass
        if not loaded:
            print("Нові записи більше не завантажуються.")
            break

    return topics


def scrape_articles(requested):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        try:
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(FEED_URL, wait_until="domcontentloaded", timeout=60_000)
            topics = get_topics(page, requested)
            if not topics:
                raise RuntimeError("Новини не знайдено.")

            if len(topics) < requested:
                print(f"Доступно {len(topics)} статей із запитаних {requested}.")

            output = create_output()
            articles = []
            failed = 0

            for index, topic in enumerate(topics, 1):
                print(f'[{index}/{len(topics)}] {topic["title"]}')
                try:
                    response = page.goto(
                        topic["url"],
                        wait_until="domcontentloaded",
                        timeout=60_000,
                    )
                    if response and response.status >= 400:
                        raise RuntimeError(f"HTTP {response.status}")
                    page.locator("article.news h1.newsTitle").wait_for(
                        state="visible", timeout=30_000
                    )
                    articles.append(parse_html(page.content(), page.url))
                    save_articles(output, articles)
                except Exception as error:
                    failed += 1
                    print(f'Не вдалося зібрати {topic["url"]}: {error}')
                if index < len(topics):
                    page.wait_for_timeout(1000)

            print(f"\nЗбережено статей: {len(articles)} із запитаних {requested}")
            if failed:
                print(f"Не вдалося зібрати: {failed}")
            return output
        finally:
            browser.close()
