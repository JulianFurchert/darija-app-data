#!/usr/bin/env python3
"""
Merge categorization data into a Darija dictionary dataset without overwriting existing fields.

- Reads a dataset JSON array (data/dataset-v01.json).
- Reads a categorization JSONL file (data/log-categorization-v01.jsonl).
- Transfers only whitelisted fields that exist in the schema:
    frequency_score (int)
    is_daily_darija (bool)
    is_standard_arabic (bool)
    user_summary_de (str)
    user_summary_en (str)

- NEVER overwrites an existing non-null/non-empty value in the dataset.
- Logs all "skipped overwrites" and "added fields" to a JSONL log file.
- Writes the merged dataset to a new file by default (does NOT overwrite input).
"""

DATASET_PATH = "data/dataset-v01.json"
VALIDATION_LOGS_PATH = "data/log-validation-v01.jsonl"
OUT_PATH = "data/dataset-v01-merged.json"
LOG_OUT_PATH = "data/dataset-v01-merge-log.jsonl"
DRY_RUN = False  # Set to True for dry-run mode
import json
import os
from datetime import datetime
from typing import Dict, Any, List


VALIDATION_FIELDS = [
    "include",
    "reason",
    "main_form_ok",
    "main_form_suggestion",
    "en_ok",
    "en_suggestions",
    "de_ok",
    "de_suggestions",
    "notes",
    "confidence",
]
def load_validation_logs(path: str) -> Dict[str, Dict[str, Any]]:
    """
    Returns a mapping id -> validation_record (last one wins if duplicate ids)
    """
    by_id: Dict[str, Dict[str, Any]] = {}
    with open(path, "r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSONL at line {lineno}: {e}")
            if "id" not in rec:
                continue
            by_id[rec["id"]] = rec
    return by_id



def load_dataset(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("Dataset must be a JSON array of entries.")
        return data







def merge(dataset: List[Dict[str, Any]], validation_by_id: Dict[str, Dict[str, Any]]):
    """
    Returns (merged_dataset, log_records, stats)
    """
    log_records = []
    stats = {
        "entries_total": len(dataset),
        "validation_fields_added": 0,
        "validation_entries_with_log": 0,
        "entries_unmatched": 0,
    }


    for entry in dataset:
        entry_id = entry.get("id")
        if not entry_id:
            continue
        validation = validation_by_id.get(entry_id)
        if validation:
            stats["validation_entries_with_log"] += 1
            # include immer vor validation setzen
            if "include" in validation:
                entry_items = [("include", validation["include"]), ("validation", {field: validation[field] for field in VALIDATION_FIELDS if field in validation})]
                entry.update({k: v for k, v in entry_items})
            else:
                entry["validation"] = {field: validation[field] for field in VALIDATION_FIELDS if field in validation}
            stats["validation_fields_added"] += len(entry["validation"])
            log_records.append({
                "id": entry_id,
                "action": "add_validation_object",
                "fields": list(entry["validation"].keys()),
                "include_top_level": validation.get("include") if "include" in validation else None
            })
        else:
            stats["entries_unmatched"] += 1

    return dataset, log_records, stats

def write_json(path: str, data: Any):
    # Schreibe 'include' immer direkt vor 'validation', aber nach allen anderen Feldern
    def reorder(entry):
        if isinstance(entry, dict):
            keys = list(entry.keys())
            # Alle Keys außer include/validation
            other_keys = [k for k in keys if k not in ("include", "validation")]
            new_keys = other_keys[:]
            if "include" in entry:
                new_keys.append("include")
            if "validation" in entry:
                new_keys.append("validation")
            return {k: reorder(entry[k]) for k in new_keys}
        elif isinstance(entry, list):
            return [reorder(e) for e in entry]
        else:
            return entry
    with open(path, "w", encoding="utf-8") as f:
        json.dump(reorder(data), f, ensure_ascii=False, indent=2)

def write_log_jsonl(path: str, records: List[Dict[str, Any]]):
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")



def main():
    dataset = load_dataset(DATASET_PATH)
    validation_by_id = load_validation_logs(VALIDATION_LOGS_PATH)

    merged, log_records, stats = merge(dataset, validation_by_id)

    out_path, log_out_path = OUT_PATH, LOG_OUT_PATH

    # Print summary to stdout
    print("Merge summary:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
    print(f"Output dataset: {out_path}")
    print(f"Log file: {log_out_path}")

    if DRY_RUN:
        print("\n--dry-run enabled: no files written.")
        return

    write_json(out_path, merged)
    write_log_jsonl(log_out_path, log_records)

if __name__ == "__main__":
    main()
