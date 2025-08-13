#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json, csv, re
from collections import Counter

# ===== Pfade (bei Bedarf anpassen) =====
INPUT_PATH          = "data/dataset-v01.json"
OUT_SUMMARY_JSON    = "data/dataset_stats.json"
OUT_FORMS34_JSON    = "data/nouns_with_3_or_4_forms.json"
OUT_FORMS34_CSV     = "data/nouns_with_3_or_4_forms.csv"
# =======================================

def norm(s: str) -> str:
    return re.sub(r"\s+", "", (s or "")).lower()

def form_key(f):
    """Eindeutigkeit einer Form: (latin, gender, number)."""
    if not isinstance(f, dict):
        return ("", "", "")
    latin  = f.get("latin") or ""
    gender = f.get("gender") or ""
    number = f.get("number") or ""
    return (latin, gender, number)

def unique_forms(forms):
    """Liefert eine Liste eindeutiger Forms (nach form_key) in Originalreihenfolge."""
    seen = set()
    out = []
    for f in (forms or []):
        k = form_key(f)
        if k not in seen and k != ("", "", ""):
            seen.add(k)
            out.append(f)
    return out

def main():
    with open(INPUT_PATH, encoding="utf-8") as f:
        data = json.load(f)

    nouns = [e for e in data if str(e.get("class", "")).lower() == "noun"]

    total_nouns = len(nouns)
    with_gender_number = sum(1 for e in nouns if e.get("gender") and e.get("number"))

    # Verteilung der Forms-Anzahl (eindeutig gezählt)
    dist_counter = Counter()
    nouns_3_or_4 = []  # vollständige Einträge mit genau 3 oder 4 forms

    for e in nouns:
        forms = unique_forms(e.get("forms") or [])
        n = len(forms)
        # Buckets 0..4, 5+
        if n >= 5:
            dist_counter["5_plus"] += 1
        else:
            dist_counter[str(n)] += 1

        if n in (3, 4):
            nouns_3_or_4.append(e)

    # Zusätzliche Übersicht (explizit 0..5+)
    dist_full = {
        "0": dist_counter.get("0", 0),
        "1": dist_counter.get("1", 0),
        "2": dist_counter.get("2", 0),
        "3": dist_counter.get("3", 0),
        "4": dist_counter.get("4", 0),
        "5_plus": dist_counter.get("5_plus", 0),
    }

    summary = {
        "total_nouns": total_nouns,
        "nouns_with_gender_and_number": with_gender_number,
        "forms_count_distribution": dist_full,
        "nouns_with_3_forms": dist_full["3"],
        "nouns_with_4_forms": dist_full["4"],
    }

    # Schreiben: Summary
    with open(OUT_SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # Schreiben: vollständige Einträge (3 oder 4 Forms)
    with open(OUT_FORMS34_JSON, "w", encoding="utf-8") as f:
        json.dump(nouns_3_or_4, f, ensure_ascii=False, indent=2)

    # Schreiben: CSV für die 3/4-Fälle (kurze tabellarische Übersicht)
    with open(OUT_FORMS34_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "darija_ar", "darija_latin", "gender", "number", "forms_count", "forms_preview"])
        for e in nouns_3_or_4:
            forms = unique_forms(e.get("forms") or [])
            preview = " | ".join(
                f"{(f.get('latin') or '')}:{(f.get('gender') or '')}:{(f.get('number') or '')}{' (L)' if f.get('isLemma') else ''}"
                for f in forms
            )
            writer.writerow([
                e.get("id", ""),
                e.get("darija_ar", ""),
                ", ".join(e.get("darija_latin") or []),
                e.get("gender", ""),
                e.get("number", ""),
                len(forms),
                preview
            ])

    # Konsole: kurze Zusammenfassung
    print("=== DATASET STATISTIK ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\nDetails gespeichert in:")
    print(f"- {OUT_SUMMARY_JSON}")
    print(f"- {OUT_FORMS34_JSON}  (vollständige Einträge mit genau 3 oder 4 forms)")
    print(f"- {OUT_FORMS34_CSV}   (tabellarische Übersicht)")

if __name__ == "__main__":
    main()
