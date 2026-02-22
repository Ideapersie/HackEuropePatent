import json
from ops import get_doc_ids_from_applicant, get_abstract_from_docid, get_description, get_claims


def is_readable(text, threshold=0.3):
    if not text:
        return False
    unicode_chars = sum(1 for c in text if ord(c) > 127)
    return (unicode_chars / len(text)) < threshold


def get_patent_metadata(company, range_start, range_end, skip_ids=None):
    if skip_ids is None:
        skip_ids = set()
    doc_ids = get_doc_ids_from_applicant(company, range_start, range_end)
    print(doc_ids)

    if not doc_ids:
        return None  # API returned no results — signal to stop batching

    results = []
    for doc_id in doc_ids:
        if doc_id in skip_ids:
            print(f"  Skipping {doc_id} — already fetched")
            continue
        print(f"  Fetching {doc_id}...")
        patent_id = doc_id.split(".")[0]
        abstract = get_abstract_from_docid(patent_id)
        if abstract is None:
            continue
        description = get_description(patent_id)
        claims = get_claims(patent_id)
        if description is None or claims is None:
            print(f"  Skipping {doc_id} — missing description or claims")
            continue
        description_text = " ".join(p for p in description["description"] if p)
        claims_text = " ".join(c for c in claims["claims"] if c)
        if not is_readable(description_text) or not is_readable(claims_text):
            print(f"  Skipping {doc_id} — unreadable description or claims")
            continue
        metadata = {
            "doc_id": doc_id,
            **abstract,
            **description,
            **claims,
        }
        results.append(metadata)
        print(f"  Saved {doc_id} [{len(results)} new this batch]")

    return results


companies = ["LOCKHEED CORP", "RTX CORP", "BAE Systems", "BOEING CO", "SAAB AB"]

MAX_BATCHES = 5
BATCH_SIZE = 100

# Load existing results
try:
    with open("patent_results_descriptions.json", "r") as f:
        all_results = json.load(f)
    print("Loaded existing results")
except FileNotFoundError:
    all_results = {}

# Load batch progress tracking
try:
    with open("patent_progress.json", "r") as f:
        progress = json.load(f)
    print("Loaded progress tracking")
except FileNotFoundError:
    progress = {}

for company in companies:
    existing = all_results.get(company, [])
    existing_ids = {p["doc_id"] for p in existing}
    start_batch = progress.get(company, 0)

    if start_batch >= MAX_BATCHES:
        print(f"\n=== {company} already complete, skipping ===")
        continue

    print(f"\n=== Fetching patents for {company} (batch {start_batch + 1} onwards, {len(existing)} already saved) ===")
    combined = list(existing)

    for batch_num in range(start_batch, MAX_BATCHES):
        range_start = batch_num * BATCH_SIZE + 1
        range_end = range_start + BATCH_SIZE - 1
        print(f"  Batch {batch_num + 1}: range {range_start}-{range_end}")

        batch = get_patent_metadata(company, range_start=range_start, range_end=range_end, skip_ids=existing_ids)

        if batch is None:
            print(f"  No more patents from API, stopping early.")
            progress[company] = MAX_BATCHES  # mark complete
            break

        combined.extend(batch)
        for p in batch:
            existing_ids.add(p["doc_id"])

        # Advance progress to next batch
        progress[company] = batch_num + 1
        all_results[company] = combined

        # Save after every batch so progress is never lost
        with open("patent_results_descriptions.json", "w") as f:
            json.dump(all_results, f, indent=2)
        with open("patent_progress.json", "w") as f:
            json.dump(progress, f, indent=2)

        print(f"  {len(combined)} patents for {company} so far")

    print(f"Got {len(all_results[company])} total patents for {company}")

total = sum(len(v) for v in all_results.values())
print(f"\nDone. {total} patents total in patent_results_descriptions.json")