import json
from google import genai
from google.genai import types

client = genai.Client(api_key="AIzaSyBNqD6wiFlwlocPyd0itHqiaDlQjE-JjzU")

COMPANY_URLS = {
    "LOCKHEED CORP": "https://www.lockheedmartin.com/en-us/capabilities.html",
    "RTX CORP":      "https://www.rtx.com/what-we-do",
    "BAE Systems":   "https://www.baesystems.com/en/products-and-services",
    "BOEING CO":     "https://www.boeing.com/defense",
    "SAAB AB":       "https://www.saab.com/products",
}


def is_readable(text, threshold=0.3):
    if not text:
        return False
    unicode_chars = sum(1 for c in text if ord(c) > 127)
    return (unicode_chars / len(text)) < threshold


def match_patent_to_product(patent, company, company_url):
    abstract = patent.get("abstract", "")[:500]
    prompt = f"""
You are a defence industry analyst. Visit the {company} products website at {company_url} and extract a list of products and their descriptions.

Then, given the following patent abstract, identify which {company} defence product is most similar to the patent.

First, check if the abstract is readable English text. If it consists mostly of unicode symbols, garbled characters, or is otherwise unreadable, treat it as having no matching product.

Patent abstract:
{abstract}

If a similar product exists, respond in this exact JSON format:
{{
  "product_name": "<name of the {company} product>",
  "product_description": "<description of the {company} product>"
}}

If no product is sufficiently similar, or the abstract is unreadable, respond with:
{{
  "product_name": "",
  "product_description": ""
}}

Respond with JSON only, no extra text.
"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())]
        ),
    )

    if not response.text:
        return {"product_name": "", "product_description": ""}
    text = response.text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return {"product_name": "", "product_description": ""}


with open("patent_results_descriptions.json", "r") as f:
    all_patents = json.load(f)

all_results = {}
for company, patents in all_patents.items():
    company_url = COMPANY_URLS.get(company, "")
    print(f"\n=== Enriching {company} ({len(patents)} patents) ===")
    matched = []
    for i, patent in enumerate(patents, 1):
        abstract = patent.get("abstract", "")
        if not is_readable(abstract):
            print(f"[{i}/{len(patents)}] Skipping {patent.get('doc_id')} — unreadable abstract")
            continue
        print(f"[{i}/{len(patents)}] Matching: {patent.get('doc_id')}...")
        match = match_patent_to_product(patent, company, company_url)
        if match.get("product_name"):
            patent["matched_product_name"] = match["product_name"]
            patent["matched_product_description"] = match["product_description"]
            matched.append(patent)
            print(f"  Matched: {match['product_name']}")
        else:
            print(f"  No match found")
    all_results[company] = matched
    print(f"Got {len(matched)} matched patents for {company}")

with open("patent_results_enriched.json", "w") as f:
    json.dump(all_results, f, indent=2)

total = sum(len(v) for v in all_results.values())
print(f"\nSaved {total} matched patents to patent_results_enriched.json")