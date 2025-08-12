#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV -> JSON (Array) für Darija-Konjugationen.
- 'root' wird aus 'howa' genommen.
- Nur Felder root, ana, nta, nti, howa, hia, 7na, ntoma, homa.
- Dateinamen sind fest im Script gesetzt.
"""

import csv
import json
from pathlib import Path

# <<< HIER festlegen >>>
INPUT_CSV = "grammer/conjug_past.csv"     # Pfad zu deiner CSV-Datei
OUTPUT_JSON = "conjug_past.json"  # Pfad zur fertigen JSON-Datei
ENCODING = "utf-8-sig"       # CSV-Encoding
DELIMITER = None             # z.B. "," oder ";" oder None für Auto-Erkennung

COLUMNS = ["ana", "nta", "nti", "howa", "hia", "7na", "ntoma", "homa"]

def main():
    in_path = Path(INPUT_CSV)
    out_path = Path(OUTPUT_JSON)

    with open(in_path, "r", encoding=ENCODING, newline="") as f_in:
        sample = f_in.read(65536)
        f_in.seek(0)
        if DELIMITER:
            dialect = csv.excel
            dialect.delimiter = DELIMITER
        else:
            try:
                dialect = csv.Sniffer().sniff(sample)
            except csv.Error:
                dialect = csv.excel

        reader = csv.DictReader(f_in, dialect=dialect)

        missing = [c for c in COLUMNS if c not in reader.fieldnames]
        if missing:
            raise SystemExit(f"Fehler: Spalten fehlen: {missing}")

        data = []
        for row in reader:
            root_value = (row.get("howa") or "").strip()
            if not root_value:
                continue
            obj = {"root": root_value}
            for col in COLUMNS:
                obj[col] = row.get(col, "")
            data.append(obj)

    with open(out_path, "w", encoding="utf-8") as f_out:
        json.dump(data, f_out, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
