import json
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

def find_metadata(soup):
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(script.get_text())
        except (ValueError, TypeError):
            continue
        queue = data if isinstance(data, list) else [data]
        while queue:
            item = queue.pop(0)
            if not isinstance(item, dict):
                continue
            types = item.get("@type", [])
            types = [types] if isinstance(types, str) else types
            if "NewsArticle" in types or "Article" in types:
                return item
            graph = item.get("@graph", [])
            if isinstance(graph, list):
                queue.extend(graph)
    return {}

def format_date(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, TypeError, AttributeError):
        return value

    if "T" not in value and " " not in value:
        return parsed.strftime("%d.%m.%Y")

    result = parsed.strftime("%d.%m.%Y %H:%M")
    offset = parsed.utcoffset()
    if offset is None:
        return result
    minutes = int(offset.total_seconds() / 60)
    if minutes == 0:
        return result + " UTC"
    sign = "+" if minutes > 0 else "-"
    hours, remainder = divmod(abs(minutes), 60)
    return f"{result} UTC{sign}{hours:02d}:{remainder:02d}"


def article_id(url):
    filename = urlparse(url).path.rstrip("/").rsplit("/", 1)[-1]
    value = filename.split("-", 1)[0]
    return int(value) if value.isdecimal() else None


def parse_html(html, url):
    soup = BeautifulSoup(html, "html.parser")
    article = soup.select_one("article.news")
    if article is None:
        raise RuntimeError("Не знайдено статтю. Можливо, розмітка сайту змінилася.")
    title_node = article.select_one("h1.newsTitle")
    metadata = find_metadata(soup)
    author_data = metadata.get("author")
    authors = author_data if isinstance(author_data, list) else [author_data]
    names = []
    for author in authors:
        name = author.get("name") if isinstance(author, dict) else author
        if isinstance(name, str) and name.strip():
            names.append(name.strip())

    image_url = None
    for image in article.select("figure img, .newsText img"):
        src = image.get("data-src") or image.get("src")
        if src:
            candidate = urljoin(url, src)
            if urlparse(candidate).scheme in ("http", "https"):
                image_url = candidate
                break

    time_node = article.select_one("time[datetime]")
    return {
        "id": article_id(url),
        "url": url,
        "title": title_node.get_text(" ", strip=True) if title_node else metadata.get("headline"),
        "author": ", ".join(names) if names else None,
        "date": format_date(time_node.get("datetime") if time_node else metadata.get("datePublished")),
        "image": image_url,
    }
