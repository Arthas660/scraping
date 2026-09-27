from task_departments import fetch_departments
from task_deputies import fetch_deputies_and_images
from task_db import save_all_to_db

def main():
    print("Запуск парсера...\n")
    departments = fetch_departments()
    deputies, images_data = fetch_deputies_and_images()
    save_all_to_db(departments, deputies, images_data)

    print("\nГотово! Перевірте створені файли TXT, XML, JSON, CSV та Db.")

if __name__ == "__main__":
    main()