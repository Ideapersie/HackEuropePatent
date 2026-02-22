import json


def is_readable(text, threshold=0.3):
    if not text:
        return False
    unicode_chars = sum(1 for c in text if ord(c) > 127)
    return (unicode_chars / len(text)) < threshold


with open("patent_results_descriptions.json", "r") as f:
    all_patents = json.load(f)

filtered = {}
total_before = 0
total_after = 0

for company, patents in all_patents.items():
    total_before += len(patents)
    kept = []
    for patent in patents:
        description = patent.get("description") or []
        claims = patent.get("claims") or []
        description_text = " ".join(p for p in description if p)
        claims_text = " ".join(c for c in claims if c)
        if is_readable(description_text) and is_readable(claims_text):
            kept.append(patent)
        else:
            print(f"  Removing {patent.get('doc_id')} — unreadable description or claims")
    filtered[company] = kept
    total_after += len(kept)
    print(f"{company}: {len(patents)} → {len(kept)} patents")

print(f"\nTotal: {total_before} → {total_after} patents")

with open("patent_results_descriptions.json", "w") as f:
    json.dump(filtered, f, indent=2)

print("Saved filtered results to patent_results_descriptions.json")
