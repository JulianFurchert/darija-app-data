#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv, json, re
from collections import defaultdict

# ===== Pfade (bei Bedarf anpassen) =====
CSV_PATH    = "orginal_data/syntactic categories/masculine_feminine_plural.csv"
JSON_PATH   = "data/dataset-v01.json"
OUTPUT_PATH = "data/dataset-v01.updated.json"

# Logs (nur das Gewünschte):
LOG_UPDATED_PATH     = "data/updated_entries.log.json"     # vollständige, aktualisierte Einträge (JSON-Array)
LOG_MULTIMATCH_PATH  = "data/multi_matches.log.json"       # Mehrfachtreffer (JSON-Array)
# =======================================

def norm(s: str) -> str:
    return re.sub(r"\s+", "", (s or "")).lower()

def load_dataset(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def form_key(f):
    return (f.get("latin") or "", f.get("gender") or "", f.get("number") or "")

def add_form(entry, latin, gender, number, isLemma):
    """Fügt eine Form (latin+gender+number) zu entry.forms hinzu, ohne Dubletten."""
    if not latin:
        return
    entry.setdefault("forms", [])
    k = (latin, gender or "", number or "")
    have = {form_key(f) for f in entry["forms"]}
    if k not in have:
        entry["forms"].append({
            "latin": latin,
            **({"gender": gender} if gender else {}),
            **({"number": number} if number else {}),
            "isLemma": bool(isLemma),
        })
    elif isLemma:
        # existierende Form zum Lemma hochstufen
        for f in entry["forms"]:
            if form_key(f) == k:
                f["isLemma"] = True

def main():
    # 1) CSV indexieren: latin(normalisiert) -> Liste von Treffern (row, column_name)
    index = defaultdict(list)
    with open(CSV_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            for col in ("masculine", "feminine", "masc_plural", "fem_plural"):
                val = (row.get(col) or "").strip()
                if val:
                    index[norm(val)].append((row, col))

    data = load_dataset(JSON_PATH)

    updated_entries = []    # volle aktualisierte Einträge
    multimatches = []       # Infos zu Mehrfachtreffern

    updated_count = 0
    skipped_no_match = 0

    for entry in data:
        # nur Nomen bearbeiten
        if str(entry.get("class", "")).lower() != "noun":
            # optional: altes plural_latin entfernen
            entry.pop("plural_latin", None)
            continue

        # vorhandenes plural_latin konsequent entfernen
        entry.pop("plural_latin", None)

        latin_list = entry.get("darija_latin") or []
        if not latin_list:
            skipped_no_match += 1
            continue

        primary = latin_list[0]
        matches = index.get(norm(primary), [])

        if not matches:
            # NO_MATCH wird NICHT geloggt (dein Wunsch)
            skipped_no_match += 1
            continue

        if len(matches) > 1:
            # Mehrfachtreffer protokollieren (ohne Abbruch)
            multimatches.append({
                "id": entry.get("id"),
                "primary": primary,
                "columns": [c for _, c in matches],
                # damit es nicht riesig wird, loggen wir nur die Zeilen-Info schlank
                "rows": [
                    {
                        "masculine": (r.get("masculine") or "").strip(),
                        "feminine": (r.get("feminine") or "").strip(),
                        "masc_plural": (r.get("masc_plural") or "").strip(),
                        "fem_plural": (r.get("fem_plural") or "").strip()
                    } for r, _ in matches
                ]
            })

        # Den ersten Treffer verwenden
        row, col = matches[0]

        # Gender/Number aus der Spalte ableiten + Gegenform
        if col == "masculine":
            gender, number = "masculine", "singular"
            counterpart = (row.get("masc_plural") or "").strip()
            counterpart_gender, counterpart_number = "masculine", "plural"
        elif col == "feminine":
            gender, number = "feminine", "singular"
            counterpart = (row.get("fem_plural") or "").strip()
            counterpart_gender, counterpart_number = "feminine", "plural"
        elif col == "masc_plural":
            gender, number = "masculine", "plural"
            counterpart = (row.get("masculine") or "").strip()
            counterpart_gender, counterpart_number = "masculine", "singular"
        elif col == "fem_plural":
            gender, number = "feminine", "plural"
            counterpart = (row.get("feminine") or "").strip()
            counterpart_gender, counterpart_number = "feminine", "singular"
        else:
            gender, number = None, None
            counterpart, counterpart_gender, counterpart_number = "", None, None

        # Entry-Level-Merkmale setzen (exakt nach Fundstelle)
        if gender: entry["gender"] = gender
        else: entry.pop("gender", None)

        if number: entry["number"] = number
        else: entry.pop("number", None)

        # FORMS pflegen:
        add_form(entry, primary, gender, number, True)  # Lemma
        if counterpart:
            add_form(entry, counterpart, counterpart_gender, counterpart_number, False)

        # Vollständigen aktualisierten Eintrag für’s Log aufnehmen
        updated_entries.append(entry.copy())
        updated_count += 1

    # Ausgaben
    save_json(OUTPUT_PATH, data)
    save_json(LOG_UPDATED_PATH, updated_entries)
    save_json(LOG_MULTIMATCH_PATH, multimatches)

    print(f"Aktualisiert: {updated_count} Nomen. Ohne Match übersprungen: {skipped_no_match}.")
    print(f"Output:            {OUTPUT_PATH}")
    print(f"Updated-Log:       {LOG_UPDATED_PATH} (vollständige Einträge)")
    print(f"Multi-Match-Log:   {LOG_MULTIMATCH_PATH}")

if __name__ == "__main__":
    main()
