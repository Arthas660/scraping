import csv
import re
import time
from urllib.parse import quote
from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

QUERY = "пральна машина"
BASE_URL = "https://www.olx.ua/uk/list/q-" + quote(QUERY.replace(" ", "-")) + "/"
MAX_PAGES = 5
CSV_FILE = "washing_machines.csv"

CITY_FIX = {
    "Киев": "Київ",
    "Львов": "Львів",
    "Харьков": "Харків",
    "Днепр": "Дніпро",
    "Одесса": "Одеса",
    "Запорожье": "Запоріжжя",
    "Николаев": "Миколаїв",
    "Винница": "Вінниця",
    "Черкассы": "Черкаси",
    "Сумы": "Суми",
    "Ровно": "Рівне",
    "Луцк": "Луцьк",
    "Тернополь": "Тернопіль",
    "Черновцы": "Чернівці",
    "Хмельницкий": "Хмельницький",
    "Кропивницкий": "Кропивницький",
    "Чернигов": "Чернігів",
    "Кременчуг": "Кременчук",
    "Каменец-Подольский": "Кам'янець-Подільський",
    "Нововолынск": "Нововолинськ",
    "Белая Церковь": "Біла Церква",
    "Кривой Рог": "Кривий Ріг",
    "Ивано-Франковск": "Івано-Франківськ",
    "Мариуполь": "Маріуполь",
    "Александрия": "Олександрія",
    "Коломыя": "Коломия",
    "Бровары": "Бровари",
    "Пивденное": "Південне",
    "Васильков": "Васильків",
    "Смела": "Сміла",
    "Ирпень": "Ірпінь",
    "Сарны": "Сарни",
    "Маневичи": "Маневичі",
    "Шепетовка": "Шепетівка",
}


def parse_price(text):
    if not text or "грн" not in text:
        return None
    digits = re.sub(r"[^\d]", "", text.split("грн")[0])
    return int(digits) if digits else None


def parse_city(text):
    place = re.split(r"\s[-–—]\s", text.strip())[0]
    city = place.split(",")[0].strip()
    return CITY_FIX.get(city, city)


def scrape():
    rows, seen = [], set()
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--deny-permission-prompts", "--disable-notifications"],
        )
        ctx = browser.new_context(locale="uk-UA", viewport={"width": 1366, "height": 900})
        page = ctx.new_page()

        for n in range(1, MAX_PAGES + 1):
            page.goto(f"{BASE_URL}?page={n}", wait_until="domcontentloaded")
            try:
                page.wait_for_selector('div[data-cy="l-card"]', timeout=10000)
            except PWTimeout:
                break

            for _ in range(4):
                page.mouse.wheel(0, 2000)
                time.sleep(0.2)

            added = 0
            for c in page.query_selector_all('div[data-cy="l-card"]'):
                link = c.query_selector("a")
                href = link.get_attribute("href") if link else None
                if not href or href in seen:
                    continue
                seen.add(href)

                title_el = c.query_selector("h4, h6")
                price_el = c.query_selector('[data-testid="ad-price"]')
                loc_el = c.query_selector('[data-testid="location-date"]')
                if not (title_el and price_el and loc_el):
                    continue

                price = parse_price(price_el.inner_text())
                if price is None:
                    continue
                rows.append({
                    "model": title_el.inner_text().strip(),
                    "price": price,
                    "city": parse_city(loc_el.inner_text()),
                })
                added += 1
            print(f"Сторінка {n}: +{added}")
            time.sleep(0.5)
        browser.close()
    return rows


def save_csv(rows):
    with open(CSV_FILE, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["model", "price", "city"], delimiter=";")
        w.writeheader()
        w.writerows(rows)
    print(f"Збережено {len(rows)} рядків у {CSV_FILE}")


if __name__ == "__main__":
    save_csv(scrape())
