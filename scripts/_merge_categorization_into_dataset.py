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

# Hardcoded file paths
DATASET_PATH = "data/dataset-v01.json"
LOGS_PATH = "data/log-categorization-v01.jsonl"
OUT_PATH = "data/dataset-v01-merged.json"
LOG_OUT_PATH = "data/dataset-v01-merge-log.jsonl"
DRY_RUN = False  # Set to True for dry-run mode
import json
import os
from datetime import datetime
from typing import Dict, Any, List

WHITELIST_FIELDS = [
    "frequency_score",
    "is_daily_darija",
    "is_standard_arabic",
    "user_summary_de",
    "user_summary_en",
    "category_confidence",
    "category",
]



def load_dataset(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if not isinstance(data, list):
            raise ValueError("Dataset must be a JSON array of entries.")
        return data

def load_logs(path: str) -> Dict[str, Dict[str, Any]]:
    """
    Returns a mapping id -> last_record_by_timestamp
    If multiple entries per id exist, keep the one with the latest timestamp.
    """
    best_by_id: Dict[str, Dict[str, Any]] = {}
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
            ts_str = rec.get("timestamp")
            # Parse timestamp if present; otherwise, use line number as fallback order
            try:
                ts = datetime.fromisoformat(ts_str) if ts_str else None
            except Exception:
                ts = None
            prev = best_by_id.get(rec["id"])
            if prev is None:
                best_by_id[rec["id"]] = rec
            else:
                prev_ts_str = prev.get("timestamp")
                try:
                    prev_ts = datetime.fromisoformat(prev_ts_str) if prev_ts_str else None
                except Exception:
                    prev_ts = None
                # Decide which one is later
                if ts and (not prev_ts or ts > prev_ts):
                    best_by_id[rec["id"]] = rec
                elif not ts and not prev_ts:
                    # Fall back to later line wins
                    best_by_id[rec["id"]] = rec
    return best_by_id



def is_meaningful(value: Any) -> bool:
    # Consider None, empty string "", and empty lists as non-meaningful (thus allowed to fill in)
    if value is None:
        return False
    if isinstance(value, str) and value.strip() == "":
        return False
    if isinstance(value, list) and len(value) == 0:
        return False
    return True

def merge(dataset: List[Dict[str, Any]], logs_by_id: Dict[str, Dict[str, Any]]):
    """
    Returns (merged_dataset, log_records, stats)
    """
    log_records = []
    stats = {
        "entries_total": len(dataset),
        "entries_with_log": 0,
        "fields_added": 0,
        "fields_skipped_overwrite": 0,
        "entries_modified": 0,
        "entries_unmatched": 0,
    }

    for entry in dataset:
        entry_id = entry.get("id")
        if not entry_id:
            continue
        src = logs_by_id.get(entry_id)
        if not src:
            stats["entries_unmatched"] += 1
            continue

        stats["entries_with_log"] += 1
        entry_modified = False

        for field in WHITELIST_FIELDS:
            if field not in src:
                continue
            src_val = src[field]
            dst_has = field in entry
            dst_val = entry.get(field)

            if dst_has and is_meaningful(dst_val):
                # Skip overwrite, log this case
                log_records.append({
                    "id": entry_id,
                    "action": "skip_overwrite",
                    "field": field,
                    "existing_value": dst_val,
                    "new_value_ignored": src_val,
                })
                stats["fields_skipped_overwrite"] += 1
                continue

            # Either field not present, or present but empty/None => set it
            entry[field] = src_val
            log_records.append({
                "id": entry_id,
                "action": "add_field",
                "field": field,
                "value": src_val,
            })
            stats["fields_added"] += 1
            entry_modified = True

        if entry_modified:
            stats["entries_modified"] += 1

    return dataset, log_records, stats

def write_json(path: str, data: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def write_log_jsonl(path: str, records: List[Dict[str, Any]]):
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def main():
    dataset = load_dataset(DATASET_PATH)
    logs_by_id = load_logs(LOGS_PATH)

    merged, log_records, stats = merge(dataset, logs_by_id)

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
