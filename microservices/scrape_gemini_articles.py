import json
import trafilatura

with open("gemini_sourced_articles.json", "r") as f:
    articles = json.load(f)

for i, article in enumerate(articles, 1):
    url = article.get("url", "")
    print(f"[{i}/{len(articles)}] Scraping: {url}")
    try:
        downloaded = trafilatura.fetch_url(url)
        content = trafilatura.extract(downloaded)
        article["content"] = content if content else ""
    except Exception as e:
        print(f"  Error: {e}")
        article["content"] = ""

with open("gemini_sourced_articles.json", "w") as f:
    json.dump(articles, f, indent=2)

print(f"\nDone. Scraped content for {sum(1 for a in articles if a.get('content'))} / {len(articles)} articles.")