from scraper import ask_count, scrape_articles

def main():
    try:
        count = ask_count()
        output = scrape_articles(count)
        print(f"Файл: {output.resolve()}")
    except KeyboardInterrupt:
        print("\nПрограму зупинено.")
    except Exception as error:
        print(f"\nПомилка: {error}")

if __name__ == "__main__":
    main()
