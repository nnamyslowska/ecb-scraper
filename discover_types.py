# Quick script to find all ECB publication type IDs
# Uses the correct field names from the metadata header

import requests
import math

BASE = "https://www.ecb.europa.eu/foedb/dbs/foedb/publications_types/1774253573/j9x6Z5FP"
META_URL = BASE + "/metadata.json"

print("Downloading publications_types metadata...")
r = requests.get(META_URL, timeout=30)
meta = r.json()

header = meta["header"]
print("Header fields:", header)
print("Total records:", meta["total_records"])

num_chunks = math.ceil(meta["total_records"] / meta["chunk_size"])
field_count = len(header)

all_types = []
for i in range(num_chunks):
    chunk_url = f"{BASE}/data/0/chunk_{i}.json"
    resp = requests.get(chunk_url, timeout=30)
    data = resp.json()
    rows = len(data) // field_count
    for row_num in range(rows):
        start = row_num * field_count
        vals = data[start:start + field_count]
        row = dict(zip(header, vals))
        all_types.append(row)

print(f"\nFound {len(all_types)} publication types:\n")
for t in all_types:
    type_id = t.get("id_publication_type", "?")
    type_name = t.get("publication_name", "?")
    print(f"  ID: {str(type_id):>3}  |  {type_name}")