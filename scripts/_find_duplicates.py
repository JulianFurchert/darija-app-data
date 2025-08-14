import json
from itertools import combinations

# Datei laden (Liste mit 3500 Einträgen)
with open("data/dataset-v01.json", "r", encoding="utf-8") as f:
    entries = json.load(f)

matches = []

def normset(vs):
    return set(v.strip().lower() for v in (vs or []) if isinstance(v, str) and v.strip())

for e1, e2 in combinations(entries, 2):
    # Neue Regel: Wortart gleich?
    same_pos = e1.get("class") == e2.get("class")

    same_arabic = (e1.get("darija_ar") == e2.get("darija_ar")) and same_pos
    same_first_latin = (e1["darija_latin"] or [None])[0] == (e2["darija_latin"] or [None])[0]

    en_overlap = normset(e1.get("en")) & normset(e2.get("en"))
    de_overlap = normset(e1.get("de")) & normset(e2.get("de"))

    # Neue Regel: mindestens 1 EN + 1 DE gemeinsam UND gleiche Wortart
    same_translation = same_pos and bool(en_overlap) and bool(de_overlap)

    if same_arabic or same_first_latin or same_translation:
        matches.append({
            "id1": e1["id"],
            "id2": e2["id"],
            "criteria": {
                "arabic": same_arabic,
                "first_latin": same_first_latin,
                "translation": same_translation
            },
            "word1": e1,
            "word2": e2
        })

# Log schreiben
with open("data/duplicate_log.json", "w", encoding="utf-8") as f:
    json.dump(matches, f, ensure_ascii=False, indent=2)

print(f"{len(matches)} mögliche Duplikate gefunden und in duplicate_log.json gespeichert.")
