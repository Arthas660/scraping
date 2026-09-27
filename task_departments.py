import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from xml.dom import minidom
from urllib.parse import urljoin, urlparse
import urllib3
from config import BASE_URL, DEPARTMENTS_URL, HEADERS

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_departments():
    print("--- ЗАВДАННЯ 2: Завантаження сторінки підрозділів ---")
    response = requests.get(DEPARTMENTS_URL, headers=HEADERS, verify=False)
    response.raise_for_status()
    print("HTML сторінки успішно завантажено. Перші 300 символів:")
    print(response.text[:300])
    print("-" * 50)

    print("\n--- ЗАВДАННЯ 3: Отримання списку підрозділів (Структурна фільтрація) ---")
    soup = BeautifulSoup(response.text, "html.parser")

    # Очищення header & footer...
    for noisy_tag in soup.find_all(["header", "footer", "nav", "aside", "form"]):
        noisy_tag.decompose()

    # 2. Пошук контейнеру основного контенту
    content_area = (
        soup.find("main") 
        or soup.find("article") 
        or soup.find("div", class_="page-content") 
        or soup.find("div", class_="content")
        or soup.find("div", id="content")
        or soup
    )

    departments = []
    ignored_extensions = ('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar', '.jpg', '.png')

    # 3. Збір посилань з очищеного блоку контенту
    for link in content_area.find_all("a", href=True):
        href = link["href"].strip()
        name = link.get_text(strip=True)
        full_url = urljoin(BASE_URL, href)

        # Перевірка 1:
        if not name or len(name) < 3 or href.startswith("#") or href.startswith(("javascript:", "mailto:", "tel:")):
            continue

        # Перевірка 2:
        parsed_url = urlparse(full_url)
        parsed_base = urlparse(BASE_URL)
        if parsed_url.netloc and parsed_url.netloc != parsed_base.netloc:
            continue

        # Перевірка 3:
        if href.lower().endswith(ignored_extensions):
            continue
        if full_url in [DEPARTMENTS_URL, f"{BASE_URL}/", BASE_URL]:
            continue

        # Перевірка 4:
        if not any(d['url'] == full_url for d in departments):
            departments.append({"name": name, "url": full_url})

    # Збереження у TXT
    with open("departments.txt", "w", encoding="utf-8") as f:
        for dep in departments:
            f.write(f"Підрозділ: {dep['name']} | URL: {dep['url']}\n")

    # Збереження у XML
    root = ET.Element("Departments")
    for dep in departments:
        dep_elem = ET.SubElement(root, "Department")
        ET.SubElement(dep_elem, "Name").text = dep['name']
        ET.SubElement(dep_elem, "URL").text = dep['url']

    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    with open("departments.xml", "w", encoding="utf-8") as f:
        f.write(xml_str)

    print(f"Знайдено чистих підрозділів: {len(departments)}. Файли departments.txt та departments.xml збережено.")
    return departments