import csv
import json
from collections import defaultdict

# Pfade
CSV_PATH = "orginal_data/syntactic categories/masculine_feminine_plural.csv"
JSON_PATH = "data/dataset-v01.json"
OUTPUT_PATH = "data/masculine_feminine_plural.json"
LOG_PATH = "data/masculine_feminine_plural.log.txt"

# Hilfsfunktion: Lade das JSON und baue ein Lookup
with open(JSON_PATH, encoding="utf-8") as f:
    dataset = json.load(f)
latin_to_id = defaultdict(list)
for entry in dataset:
    for latin in entry.get("darija_latin", []):
        latin_to_id[latin].append(entry["id"])

def find_entry_ids(word):
    # Nur IDs von Einträgen mit class == 'noun' zurückgeben
    ids = latin_to_id.get(word, [])
    noun_ids = []
    for eid in ids:
        # Finde das passende Entry im Datensatz
        entry = next((e for e in dataset if e["id"] == eid), None)
        if entry and entry.get("class") == "noun":
            noun_ids.append(eid)
    return noun_ids

results = []
logs = []
with open(CSV_PATH, encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        found = []
        found_info = []
        for col, gender, number, isLemma in [
            ("masculine", "masculine", "singular", True),
            ("feminine", "feminine", "singular", True),
            ("masc_plural", "masculine", "plural", False),
            ("fem_plural", "feminine", "plural", False),
        ]:
            value = row.get(col)
            if value is not None:
                latin = value.strip()
                if latin:
                    entry_ids = find_entry_ids(latin)
                    if entry_ids:
                        # Merke alle gefundenen IDs und Infos
                        for eid in entry_ids:
                            found.append(eid)
                            found_info.append({
                                "entry": eid,
                                "gender": gender,
                                "number": number,
                                "isLemma": isLemma,
                                "latin": latin
                            })
        if len(found) == 1:
            # Perfekt, genau eine Referenz
            results.append(found_info[0])
        elif len(found) > 1:
            # Bereite vollständige Einträge für das Log auf
            entries = [next((e for e in dataset if e["id"] == eid), None) for eid in found]
            log_entry = {
                "csv_row": row,
                "matching_entries": entries
            }
            logs.append(json.dumps(log_entry, ensure_ascii=False, indent=2))

# Schreibe die Ergebnisse
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
# Schreibe die Logs
with open(LOG_PATH, "w", encoding="utf-8") as f:
    for log in logs:
        f.write(log + "\n")

print(f"Fertig. {len(results)} Einträge, {len(logs)} Logs.")
