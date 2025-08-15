#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set, Any

def norm_latin(s: str) -> str:
    return s.strip().lower()

def norm_ar(s: str) -> str:
    return s.strip()

def load_csv_category_terms(base_dir: Path) -> Dict[str, Dict[str, Set[str]]]:
    mapping = {
        "economy": base_dir / "economy.csv",
        "humanbody": base_dir / "humanbody.csv",
        "time": base_dir / "time.csv",
    }
    out: Dict[str, Dict[str, Set[str]]] = {}
    for cat, path in mapping.items():
        if not path.exists():
            raise FileNotFoundError(f"CSV nicht gefunden: {path}")
        latin_set: Set[str] = set()
        ar_set: Set[str] = set()
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            headers = {h.lower(): h for h in (reader.fieldnames or [])}
            def get(row, key):
                h = headers.get(key, key)
                return row.get(h, "") if h in row else ""
            for row in reader:
                for i in range(1, 5):
                    n = get(row, f"n{i}")
                    if n and n.strip():
                        latin_set.add(norm_latin(n))
                ar = get(row, "darija_ar")
                if ar and ar.strip():
                    ar_set.add(norm_ar(ar))
        out[cat] = {"latin": latin_set, "ar": ar_set}
    return out

def find_match_category(entry: dict, cat_terms: Dict[str, Dict[str, Set[str]]]) -> Tuple[str, str]:
    if entry.get("class") != "noun":
        return "", ""
    priority = ["economy", "humanbody", "time"]
    ar = norm_ar(entry.get("darija_ar", ""))
    latin_forms = [norm_latin(x) for x in (entry.get("darija_latin") or [])]
    for cat in priority:
        terms = cat_terms[cat]
        ar_hit = ar and ar in terms["ar"]
        latin_hit = any(lf in terms["latin"] for lf in latin_forms)
        if ar_hit or latin_hit:
            return cat, ("darija_ar" if ar_hit else "latin")
    return "", ""

def ensure_parent_dir(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)

def write_csv_log(path: Path, rows: List[dict]):
    ensure_parent_dir(path)
    fieldnames = ["id","darija_ar","darija_latin","en","de","old_category","new_category","match_basis"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def write_markdown_simple(path: Path, rows: List[dict], totals: Dict[str, Any]):
    """
    Dein gewünschtes Format:
    ## darija_latin | DE
    alteKategorie => neueKategorie
    """
    ensure_parent_dir(path)
    # Sortierung: new_category, darija_ar
    rows_sorted = sorted(rows, key=lambda r: (r["new_category"], r["darija_ar"]))
    with path.open("w", encoding="utf-8") as f:
        f.write(f"# Category-Updates\n\n")
        f.write(f"- Zeitpunkt: **{totals['timestamp']}**\n")
        f.write(f"- Geprüfte Nomen: **{totals['total_nouns']}**\n")
        f.write(f"- Aktualisierte Kategorien: **{totals['changes']}**\n\n")
        if not rows_sorted:
            f.write("_Keine Änderungen._\n")
            return
        for r in rows_sorted:
            # Kopfzeile groß: darija_latin | DE
            top = " | ".join([x for x in [
                r["darija_latin"],  # schon als " | " gejoint
                r["de"]             # schon als " | " gejoint
            ] if x])
            f.write(f"## {top}\n")
            # Zweite Zeile: alt => neu
            old_cat = r["old_category"] or ""
            new_cat = r["new_category"] or ""
            f.write(f"{old_cat} => {new_cat}\n\n")

def main():
    parser = argparse.ArgumentParser(description="Update noun categories from semantic CSVs (simple readable logs).")
    parser.add_argument("--dataset", default="data/dataset-v01.json", help="Pfad zur JSON-Datei (Array).")
    parser.add_argument("--base-dir", default="orginal_data/semantic categories", help="Ordner mit CSVs.")
    parser.add_argument("--out", default="data/dataset-v01.json", help="Ziel-Datei (überschreibt per Default).")
    parser.add_argument("--log-prefix", default=None, help="Pfad-Präfix für Logs (ohne Endung).")
    parser.add_argument("--dry-run", action="store_true", help="Nur Logs, keine Schreiboperation am Dataset.")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    out_path = Path(args.out)
    base_dir = Path(args.base_dir)

    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    if args.log_prefix:
        csv_log = Path(args.log_prefix + ".csv")
        md_log  = Path(args.log_prefix + ".md")
    else:
        csv_log = Path(f"logs/category_updates-{ts}.csv")
        md_log  = Path(f"logs/category_updates-{ts}.md")

    cat_terms = load_csv_category_terms(base_dir)

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset nicht gefunden: {dataset_path}")
    with dataset_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise SystemExit("Erwartet: JSON-Array im Dataset.")

    changes = 0
    total_nouns = 0
    log_rows: List[dict] = []

    for entry in data:
        if entry.get("class") != "noun":
            continue
        total_nouns += 1
        new_cat, basis = find_match_category(entry, cat_terms)
        if not new_cat:
            continue
        old_cat = entry.get("category")
        if old_cat != new_cat:
            changes += 1
            entry["category"] = new_cat
            log_rows.append({
                "id": entry.get("id",""),
                "darija_ar": entry.get("darija_ar",""),
                "darija_latin": " | ".join(entry.get("darija_latin") or []),
                "en": " | ".join(entry.get("en") or []),
                "de": " | ".join(entry.get("de") or []),
                "old_category": old_cat if old_cat is not None else "",
                "new_category": new_cat,
                "match_basis": basis,
            })

    write_csv_log(csv_log, log_rows)
    write_markdown_simple(
        md_log,
        log_rows,
        totals={"timestamp": ts, "total_nouns": total_nouns, "changes": changes},
    )

    if not args.dry_run:
        if out_path.resolve() == dataset_path.resolve():
            backup = dataset_path.with_suffix(dataset_path.suffix + f".bak-{ts}")
            backup.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            dataset_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[OK] {changes} Kategorie(n) aktualisiert. Backup: {backup}")
        else:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"[OK] {changes} Kategorie(n) aktualisiert. Output: {out_path}")
    else:
        print(f"[DRY-RUN] {changes} Kategorie(n) würden aktualisiert werden.")

    print(f"[INFO] Geprüfte Nomen: {total_nouns}")
    print(f"[LOG] CSV: {csv_log}")
    print(f"[LOG] Markdown: {md_log}")

if __name__ == "__main__":
    main()
