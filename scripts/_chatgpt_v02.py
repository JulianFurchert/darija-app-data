# enrich_dataset.py
# pip install openai python-dotenv
# .env mit OPENAI_API_KEY=... im Projektordner

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple
from openai import OpenAI
from dotenv import load_dotenv
import os

# --- .env laden & API-Key prüfen ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY fehlt. Bitte in .env setzen oder als Umgebungsvariable exportieren.")

MODEL = "gpt-4o-mini"   # für mehr Qualität: "gpt-4o"
RATE_LIMIT_S = 0.7       # kleine Pause zwischen Calls

# ---- Aktuelle Topics-Liste (AI-taugliche Codes) ----
TOPICS_ENUM = [
    "basic_needs.social_interactions",
    "basic_needs.food_drink",
    "basic_needs.shopping_money",
    "basic_needs.numbers",
    "basic_needs.time_date",
    "basic_needs.colours",
    "basic_needs.weather",
    "basic_needs.nature",

    "people.family_relationships",
    "people.body_health",
    "people.clothes_fashion",
    "people.personal_qualities",
    "people.physical_appearance",
    "people.feelings_emotions",

    "daily_life.home_buildings",
    "daily_life.travel_transport",
    "daily_life.work_school",
    "daily_life.leisure_sport",
    "daily_life.animals",
    "daily_life.media_entertainment",

    "extra_advanced.politics_society",
    "extra_advanced.science_technology",
    "extra_advanced.environment",
    "extra_advanced.business_economy",
    "extra_advanced.culture_art",
    "extra_advanced.religion",
]

FREQ_ENUM = ["basic", "common", "rare"]
FORMAL_ENUM = ["formal", "neutral", "informal"]

SYSTEM_PROMPT = f"""You are enriching entries for a beginner-friendly Darija (Moroccan Arabic) learner's dictionary.
Audience: beginners. Focus: everyday spoken Darija (not MSA), practical communication.

TASK:
Given ONE entry (Darija in Arabizi + optional Arabic script + translations + word class), decide:
- frequency_level ∈ {FREQ_ENUM}
  • basic = essential beginner words used daily
  • common = often used and useful, but not core survival
  • rare = less common or specialized
- formality_level ∈ {FORMAL_ENUM}
- topics: 0–3 items chosen from the list below (strings as-is).

IMPORTANT RULES:
- Topics are THEMATIC; include ANY part of speech (nouns, verbs, adjectives, phrases). Do not restrict topics to nouns.
- Assign topics ONLY if there is a good fit; if uncertain, return an EMPTY ARRAY [].
- Use ONLY items from the provided list; do not invent categories.
- Decide topics first (0–3), then independently set frequency and formality.
- Return ONLY compact JSON. No extra text.

TOPICS LIST:
""" + "\n".join(TOPICS_ENUM) + """
FORMAT:
{"frequency_level":"...", "formality_level":"...", "topics":["...", "..."]}
"""

def call_api(client: OpenAI, entry: Dict[str, Any]) -> Dict[str, Any]:
    """Call OpenAI once for a single entry and parse JSON safely."""
    payload = {
        "darija": entry.get("darija", ""),
        "darija_arabic_script": entry.get("darija_arabic_script", ""),
        "darija_alt": entry.get("darija_alt", []),
        "en": entry.get("en", []),
        "de": entry.get("de", []),
        "class": entry.get("class", ""),
    }

    resp = client.chat.completions.create(
        model=MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}
        ],
    )
    content = resp.choices[0].message.content.strip()
    # Robuste JSON-Extraktion
    start, end = content.find("{"), content.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"Model did not return JSON: {content}")
    return json.loads(content[start:end+1])

def validate_and_normalize(result: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """Enum-Prüfungen, Topic-Filter, Trunkierung auf max. 3 Topics; gibt (result, warnings) zurück."""
    warnings: List[str] = []

    freq = result.get("frequency_level")
    if freq not in FREQ_ENUM:
        warnings.append(f"frequency_level '{freq}' not in enum; set to 'common'.")
        result["frequency_level"] = "common"

    form = result.get("formality_level")
    if form not in FORMAL_ENUM:
        warnings.append(f"formality_level '{form}' not in enum; set to 'neutral'.")
        result["formality_level"] = "neutral"

    topics = result.get("topics", [])
    if not isinstance(topics, list):
        warnings.append("topics was not an array; replaced with [].")
        topics = []

    filtered = [t for t in topics if t in TOPICS_ENUM]
    removed = [t for t in topics if t not in TOPICS_ENUM]
    if removed:
        warnings.append(f"unknown topics removed: {removed}")

    if len(filtered) > 3:
        warnings.append(f"more than 3 topics; truncating to first 3: {filtered[:3]}")
        filtered = filtered[:3]

    result["topics"] = filtered

    # Sanity lint: seltene Kombis markieren (nur Hinweis)
    if any(t.startswith("extra_advanced.") for t in filtered) and result["frequency_level"] == "basic":
        warnings.append("Basic + extra_advanced topic – please double-check.")
    return result, warnings

def enrich_file(input_path: str, output_path: str, log_path: str):
    client = OpenAI(api_key=OPENAI_API_KEY)  # explizit mit Key initialisieren

    # Bereits vorhandene IDs aus Output laden (falls Datei existiert)
    already_done = set()
    out: List[Dict[str, Any]] = []
    logs: List[Dict[str, Any]] = []
    if Path(output_path).exists():
        try:
            out = json.loads(Path(output_path).read_text(encoding="utf-8"))
            already_done = {e.get("id") for e in out if e.get("id")}
        except Exception:
            out = []
            already_done = set()
    if Path(log_path).exists():
        try:
            logs = [json.loads(line) for line in Path(log_path).read_text(encoding="utf-8").splitlines() if line.strip()]
        except Exception:
            logs = []

    data = json.loads(Path(input_path).read_text(encoding="utf-8"))

    # Mapping von ID auf Index in out (für schnelles Überschreiben)
    out_idx = {e.get("id"): i for i, e in enumerate(out) if e.get("id")}

    for idx, entry in enumerate(data):
        entry_id = entry.get("id")
        if entry_id in already_done:
            continue

        needs_enrichment = (
            entry.get("frequency_level") in (None, "", "null") or
            entry.get("formality_level") in (None, "", "null") or
            not isinstance(entry.get("topics"), list) or
            (isinstance(entry.get("topics"), list) and len(entry.get("topics") or []) == 0)
        )

        if not needs_enrichment:
            out.append(entry)
            already_done.add(entry_id)
            continue

        try:
            raw = call_api(client, entry)
            normalized, warns = validate_and_normalize(raw)

            entry["frequency_level"] = normalized.get("frequency_level")
            entry["formality_level"] = normalized.get("formality_level")
            entry["topics"] = normalized.get("topics", [])

            v = entry.get("validation", {}) or {}
            v.setdefault("enrichment", {})
            v["enrichment"]["model"] = MODEL
            v["enrichment"]["result"] = normalized
            if warns:
                v.setdefault("warnings", [])
                v["warnings"].extend(warns)
            entry["validation"] = v

            logs.append({
                "id": entry.get("id"),
                "darija": entry.get("darija"),
                "class": entry.get("class"),
                "api_result": raw,
                "normalized": normalized,
                "warnings": warns
            })

        except Exception as e:
            v = entry.get("validation", {}) or {}
            v.setdefault("errors", [])
            v["errors"].append(f"enrichment_error: {str(e)}")
            entry["validation"] = v

            logs.append({
                "id": entry.get("id"),
                "darija": entry.get("darija"),
                "class": entry.get("class"),
                "error": str(e)
            })

        out.append(entry)
        already_done.add(entry_id)

        # Alle 10 Einträge flushen
        if len(out) % 10 == 0:
            Path(output_path).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
            with Path(log_path).open("w", encoding="utf-8") as f:
                for row in logs:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")

        time.sleep(RATE_LIMIT_S)

    # Am Ende alles nochmal speichern
    Path(output_path).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    with Path(log_path).open("w", encoding="utf-8") as f:
        for row in logs:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Done. Wrote enriched JSON → {output_path}")
    print(f"Log (JSONL) → {log_path}")

if __name__ == "__main__":
    # Pfade nach Bedarf anpassen
    INPUT = "data/dataset-v02.json"                 # deine Eingabedatei
    OUTPUT = "data/dataset-v02.enriched.json"       # neue Datei mit befüllten Feldern
    LOG = "data/dataset-v02.enrichment.log.jsonl"   # Log pro Eintrag (eine Zeile = ein JSON-Objekt)
    enrich_file(INPUT, OUTPUT, LOG)
