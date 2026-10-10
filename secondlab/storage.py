import json
from pathlib import Path

def create_output():
    directory = Path("results")
    directory.mkdir(exist_ok=True)
    output = directory / "ukrinform.json"
    save_articles(output, [])
    return output

def save_articles(output, articles):
    output.write_text(
        json.dumps(articles, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
