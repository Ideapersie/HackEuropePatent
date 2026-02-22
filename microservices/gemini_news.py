import json
import requests
from google import genai
from google.genai import types


def resolve_url(redirect_url):
    try:
        r = requests.get(redirect_url, allow_redirects=True, timeout=5)
        return r.url
    except Exception:
        return redirect_url

client = genai.Client(api_key="AIzaSyBNqD6wiFlwlocPyd0itHqiaDlQjE-JjzU")

ARTICLES_PER_PRODUCT = 3

with open("patent_results_enriched.json", "r") as f:
    all_patents = json.load(f)

products = list({
    p["matched_product_name"]
    for patents in all_patents.values()
    for p in patents
    if p.get("matched_product_name")
})
print(f"Found {len(products)} unique products: {products}\n")

def search_articles_for_product(product, num_results=3):
    prompt = f"""
Search the internet for recent news articles, press releases, and announcements related to the Lockheed Martin defence product: "{product}".

Find up to {num_results} relevant articles. For each article found, extract:
- title
- summary (2-3 sentences describing what the article is about)
- date (if available)
- source (publication or website name)

Return ONLY a JSON array with no extra text, in this format:
[
  {{
    "title": "...",
    "summary": "...",
    "date": "...",
    "source": "...",
    "product": "{product}"
  }}
]

If date is unknown, use "".
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        ),
    )

    # Resolve real URLs by following Vertex AI redirects
    candidate = response.candidates[0]
    grounding = getattr(candidate, "grounding_metadata", None)
    chunks = getattr(grounding, "grounding_chunks", None) or [] if grounding else []
    real_urls = []
    for chunk in chunks:
        web = getattr(chunk, "web", None)
        if not web:
            continue
        uri = getattr(web, "uri", "")
        if uri:
            real_urls.append(resolve_url(uri))

    if not response.text:
        print(f"  No response text for {product}")
        return []
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        articles = json.loads(text.strip())
        for i, article in enumerate(articles):
            article["url"] = real_urls[i] if i < len(real_urls) else ""
        return articles[:num_results]
    except json.JSONDecodeError:
        print(f"  Failed to parse response for {product}")
        return []


# Load existing results to resume from last save point
try:
    with open("gemini_sourced_articles.json", "r") as f:
        all_articles = json.load(f)
    seen_urls = {a["url"] for a in all_articles if a.get("url")}
    done_products = {a["product"] for a in all_articles if a.get("product")}
    print(f"Resuming — {len(all_articles)} articles already saved, {len(done_products)} products already done\n")
except (FileNotFoundError, json.JSONDecodeError):
    all_articles = []
    seen_urls = set()
    done_products = set()

for product in products:
    if product in done_products:
        print(f"Skipping {product} — already done")
        continue
    print(f"Searching articles for: {product}...")
    results = search_articles_for_product(product, num_results=ARTICLES_PER_PRODUCT)
    new = [a for a in results if a.get("url") and a["url"] not in seen_urls]
    for a in new:
        seen_urls.add(a["url"])
    all_articles.extend(new)
    print(f"  Found {len(new)} unique articles (total: {len(all_articles)})")

    with open("gemini_sourced_articles.json", "w") as f:
        json.dump(all_articles, f, indent=2)

print(f"\nDone. Saved {len(all_articles)} total unique articles to gemini_sourced_articles.json")