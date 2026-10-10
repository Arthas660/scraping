import os
import json
import csv
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import urllib3
from config import BASE_URL, DEPUTIES_URL, HEADERS, IMG_FOLDER

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_deputies_and_images():
    print("\n--- ЗАВДАННЯ 4 та 5: Перехід на сторінки депутатів, витягування ПІБ та фото ---")
    os.makedirs(IMG_FOLDER, exist_ok=True)

    response = requests.get(DEPUTIES_URL, headers=HEADERS, verify=False)
    soup = BeautifulSoup(response.text, "html.parser")

    # Очищення header & footer...
    for noisy_tag in soup.find_all(["header", "footer", "nav", "aside"]):
        noisy_tag.decompose()

    deputies = []
    images_data = []
    processed_urls = set()

    content_area = soup.find("main") or soup.find("article") or soup.find("div", class_="content") or soup

    # 1. посилання на персональні сторінки депутатів
    deputy_links = []
    for a in content_area.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        full_url = urljoin(BASE_URL, href)

        text_clean = re.sub(r"\s*1\..*", "", text).strip()

        # Фіксація ПІБ
        if re.search(r"^[А-ЯІЇЄҐ][а-яіїєґ']+\s+[А-ЯІЇЄҐ][а-яіїєґ']+\s+[А-ЯІЇЄҐ][а-яіїєґ']+", text_clean):
            if full_url not in processed_urls and full_url != DEPUTIES_URL:
                processed_urls.add(full_url)
                deputy_links.append((text_clean, full_url))

    print(f"Знайдено посилань на сторінки депутатів: {len(deputy_links)}")

    # 2. Аналіз персональних сторінок депутатів
    for idx, (raw_name, dep_url) in enumerate(deputy_links, start=1):
        try:
            print(f"[{idx}/{len(deputy_links)}] Обробка сторінки: {raw_name}...")
            dep_resp = requests.get(dep_url, headers=HEADERS, verify=False, timeout=10)
            dep_soup = BeautifulSoup(dep_resp.text, "html.parser")

            h1_tag = dep_soup.find("h1")
            if h1_tag:
                clean_name = h1_tag.get_text(strip=True)
                clean_name = re.sub(r"\s*1\..*", "", clean_name).strip()
            else:
                clean_name = raw_name

            deputies.append({"name": clean_name, "department_url": dep_url})

            #персональне фото
            dep_content = dep_soup.find("main") or dep_soup.find("article") or dep_soup.find("div", class_="content") or dep_soup
            img_tag = dep_content.find("img") if dep_content else None
            img_url = ""
            if img_tag:
                src = img_tag.get("src") or img_tag.get("data-src")
                if src and not any(x in src.lower() for x in ["logo", "icon", "banner", "header", "герб"]):
                    img_url = urljoin(BASE_URL, src)

            # Завантажуємо фотографію
            if img_url:
                ext = os.path.splitext(img_url.split("?")[0])[1]
                if not ext or len(ext) > 5:
                    ext = ".jpg"

                safe_filename = re.sub(r'[\\/*?:"<>|]', "", clean_name).replace(" ", "_")
                img_name = f"deputy_{idx}_{safe_filename}{ext}"
                local_path = os.path.join(IMG_FOLDER, img_name)

                images_data.append({"name": clean_name, "url": img_url, "local_path": local_path})

                if not os.path.exists(local_path):
                    img_bytes = requests.get(img_url, headers=HEADERS, verify=False, timeout=10).content
                    with open(local_path, "wb") as f:
                        f.write(img_bytes)

        except Exception as e:
            print(f"Помилка обробки {dep_url}: {e}")

    # Збереження у TXT та JSON
    with open("deputies.txt", "w", encoding="utf-8") as f:
        for person in deputies:
            f.write(f"Депутат: {person['name']}\n")

    with open("deputies.json", "w", encoding="utf-8") as f:
        json.dump(deputies, f, ensure_ascii=False, indent=4)

    # Збереження зображень у TXT та CSV
    with open("images_info.txt", "w", encoding="utf-8") as f:
        for img in images_data:
            f.write(f"Особа: {img['name']} | URL: {img['url']} | Шлях: {img['local_path']}\n")

    with open("images_info.csv", "w", encoding="utf-8", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["name", "url", "local_path"])
        writer.writeheader()
        writer.writerows(images_data)

    print(f"\nУспішно опрацьовано {len(deputies)} депутатів та завантажено {len(images_data)} фотографій.")
    return deputies, images_data
