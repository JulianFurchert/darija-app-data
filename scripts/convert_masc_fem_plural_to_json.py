import csv
import json
from collections import defaultdict

# Pfade
CSV_PATH = "../orginal_data/syntactic categories/masculine_feminine_plural.csv"
JSON_PATH = "../data/dataset-v01.json"
OUTPUT_PATH = "../data/masculine_feminine_plural.json"
LOG_PATH = "../data/masculine_feminine_plural.log.txt"

# Hilfsfunktion: Lade das JSON und baue ein Lookup
with open(JSON_PATH, encoding="utf-8") as f:
    dataset = json.load(f)
latin_to_id = defaultdict(list)
for entry in dataset:
    for latin in entry.get("darija_latin", []):
        latin_to_id[latin].append(entry["id"])

def find_entry_ids(word):
    return latin_to_id.get(word, [])

results = []
logs = []
with open(CSV_PATH, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        for col, gender, number, isLemma in [
            ("masculine", "masculine", "singular", True),
            ("feminine", "feminine", "singular", True),
            ("masc_plural", "masculine", "plural", False),
            ("fem_plural", "feminine", "plural", False),
        ]:
            latin = row[col].strip()
            if latin:
                entry_ids = find_entry_ids(latin)
                if len(entry_ids) == 0:
                    logs.append(f"No entry for '{latin}' in dataset")
                elif len(entry_ids) > 1:
                    logs.append(f"Multiple entries for '{latin}': {entry_ids}")
                for eid in entry_ids:
                    results.append({
                        "entry": eid,
                        "gender": gender,
                        "number": number,
                        "isLemma": isLemma,
                        "latin": latin
                    })

# Schreibe die Ergebnisse
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
# Schreibe die Logs
with open(LOG_PATH, "w", encoding="utf-8") as f:
    for log in logs:
        f.write(log + "\n")

print(f"Fertig. {len(results)} Einträge, {len(logs)} Logs.")
