#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Add Darija future tense ("ghadi + form") to verbs in a dataset JSON,
derived automatically from present tense forms.

Rule:
    future(person) = "ghadi " + remove_prefix("ka", present(person))

Where remove_prefix("ka", s) removes *one* leading "ka" if present:
    "kan3Ti" -> "n3Ti"
    "kat3Ser" -> "t3Ser"
    "kay3Ser" -> "y3Ser"

Why not remove "kay"/"kat"? Because we want to keep the person marker (n/t/y).
By removing only "ka", we retain that marker.
"""

import json
from pathlib import Path
from typing import Dict, Any, List

EXPECTED_PERSONS = ["ana", "nta", "nti", "howa", "hia", "7na", "ntoma", "homa"]

def strip_ka(form: str) -> str:
    s = form.strip()
    # remove *one* leading "ka" if present (handles kan/kat/kay uniformly)
    if s.startswith("ka"):
        return s[2:]
    return s

def build_future_from_present(present: Dict[str, str]) -> Dict[str, str]:
    future: Dict[str, str] = {}
    for person, pres_form in present.items():
        if not isinstance(pres_form, str) or not pres_form.strip():
            continue
        base = strip_ka(pres_form)
        future[person] = f"ghadi {base}"
    return future

def update_entry(entry: Dict[str, Any]) -> bool:
    """
    Returns True if entry was modified.
    """
    if not isinstance(entry, dict):
        return False

    if entry.get("class") != "verb":
        return False

    conj = entry.get("conjugations") or {}
    present = conj.get("present")
    if not isinstance(present, dict) or not present:
        return False

    # compute future
    computed_future = build_future_from_present(present)

    # If future missing or empty or any person missing, merge/overwrite missing ones only
    future = conj.get("future")
    modified = False

    if not isinstance(future, dict):
        conj["future"] = {}
        future = conj["future"]

    for person, value in computed_future.items():
        # Fill if missing, empty, or clearly wrong-type
        if person not in future or not isinstance(future[person], str) or not future[person].strip():
            future[person] = value
            modified = True

    # Write back
    entry["conjugations"] = conj
    return modified

def load_dataset(path: Path):
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def save_dataset(path: Path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def iter_entries(data) -> List[Dict[str, Any]]:
    # Support datasets that are either a list of entries or a dict containing a list under a common key.
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # try common container keys
        for key in ["data", "entries", "items", "dataset"]:
            if key in data and isinstance(data[key], list):
                return data[key]
    # Fallback: return empty list
    return []

def main():
    import argparse
    ap = argparse.ArgumentParser(description="Add Darija future tense to dataset based on present tense.")
    ap.add_argument("input", help="Path to JSON dataset (e.g., data/dataset-v01.json)")
    ap.add_argument("--inplace", action="store_true", help="Modify the input file in place (keeps a .backup)")
    ap.add_argument("-o", "--output", help="Output path for updated dataset (default: <input>.with-future.json)")
    args = ap.parse_args()

    in_path = Path(args.input)
    if not in_path.exists():
        raise SystemExit(f"Input not found: {in_path}")

    data = load_dataset(in_path)
    entries = iter_entries(data)

    modified_count = 0
    for entry in entries:
        if update_entry(entry):
            modified_count += 1

    if args.inplace:
        backup = in_path.with_suffix(in_path.suffix + ".backup")
        save_dataset(backup, data)
        save_dataset(in_path, data)
        print(f"Updated in place. Backup written to: {backup}")
    else:
        out_path = Path(args.output) if args.output else in_path.with_suffix(in_path.suffix.replace(".json","") + ".with-future.json")
        # If suffix didn't contain .json, just append
        if out_path == in_path:
            out_path = in_path.with_name(in_path.name + ".with-future.json")
        save_dataset(out_path, data)
        print(f"Written updated dataset to: {out_path}")

    print(f"Entries modified: {modified_count}")

if __name__ == "__main__":
    main()
