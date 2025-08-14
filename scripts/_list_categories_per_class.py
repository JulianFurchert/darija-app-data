import json
from collections import defaultdict

filename = "data/dataset-v01-merged.json"

with open(filename, "r", encoding="utf-8") as f:
    data = json.load(f)

class_categories = defaultdict(set)

for entry in data:
    cls = entry.get("class")
    cat = entry.get("category")
    if cls and cat:
        class_categories[cls].add(cat)

for cls in sorted(class_categories):
    print(f"class: {cls}")
    for cat in sorted(class_categories[cls]):
        print(f"  - {cat}")
    print()
