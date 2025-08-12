import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# .env laden
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# OpenAI SDK
try:
    from openai import OpenAI
    client = OpenAI()
except Exception:
    print("Fehler: OpenAI SDK nicht installiert.\nInstalliere mit: pip install openai python-dotenv")
    sys.exit(1)

# ==== DEFAULTS ====
DEFAULT_INPUT = "dataset-v01.json"
DEFAULT_OUTPUT = "validation_log.jsonl"
DEFAULT_MODEL = "gpt-4o"
DEFAULT_BATCH_SIZE = 10
DEFAULT_RESUME = True

# ==== Preise USD pro 1M Tokens ====
PRICES = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 5.00, "output": 15.00},
}

# ==== PROMPTS ====
SYSTEM_PROMPT = (
    "Du bist Experte für marokkanisches Darija, Arabisch, Englisch und Deutsch. "
    "Antworte ausschließlich mit gültigem JSON (keine Erklärtexte, keine Markdown-Code-Blöcke, keine ```json wrapper). "
    "Gib nur die reine JSON-Liste zurück, beginnend mit [ und endend mit ]."
)

USER_INSTRUCTIONS = """
Prüfe die folgenden Wörterbuch-Einträge. Für JEDES Item liefere genau EIN Objekt im Schema unten.
Stell dir vor, du erstellst ein kompaktes, qualitativ hochwertiges Darija-Wörterbuch
mit nur etwa ca. 3000 Einträgen. Nur relevante, gebräuchliche oder wichtige Wörter
sollen aufgenommen werden.

Aufgaben:
1) include (true/false): Soll der Eintrag in ein seriöses Darija-Wörterbuch?
2) reason: kurze Begründung.
3) main_form_ok: Ist die erste Form in "darija_latin" die meistgenutzte? Wenn nein, gib main_form_suggestion (String).
4) en_ok/de_ok: Passen die Übersetzungen? Wenn nein, gib Alternativen in en_suggestions/de_suggestions (Liste kurzer Strings).
5) notes (optional, max 1–2 Sätze) und confidence (0..1).

WICHTIG: Antworte NUR mit einer JSON-LISTE ([]) aus Objekten gemäß Schema.
KEINE Markdown-Code-Blöcke (```json), KEINE Erklärungen, NUR die reine JSON-Liste!

Schema eines Objekts:
{
  "id": "…",
  "include": true/false,
  "reason": "…",
  "main_form_ok": true/false,
  "main_form_suggestion": "… oder null",
  "en_ok": true/false,
  "en_suggestions": ["…"],
  "de_ok": true/false,
  "de_suggestions": ["…"],
  "notes": "",
  "confidence": 0.0
}

Hier sind die Items:
"""

# ==== Hilfsfunktionen ====
def load_json(path: Path) -> List[Dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(data, list), "Eingabe-JSON muss eine Liste sein."
    return data

JSON_RE = re.compile(r"\[.*\]", re.DOTALL)

def extract_json_list(text: str) -> List[Dict[str, Any]]:
    if isinstance(text, list):
        return text
    if isinstance(text, dict):
        return [text]
    if not isinstance(text, str):
        raise ValueError("Unerwarteter Antworttyp.")

    # Versuche verschiedene JSON-Extraktionsstrategien
    try:
        # Strategie 1: Direkte JSON-Parsing
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    try:
        # Strategie 2: Markdown Code-Block entfernen
        # Entferne ```json ... ``` wrapper
        cleaned = re.sub(r'^```json\s*\n?', '', text, flags=re.MULTILINE)
        cleaned = re.sub(r'\n?```\s*$', '', cleaned, flags=re.MULTILINE)
        return json.loads(cleaned.strip())
    except json.JSONDecodeError:
        pass
    
    try:
        # Strategie 3: RegEx-basierte Extraktion
        m = JSON_RE.search(text)
        if m:
            return json.loads(m.group(0))
    except json.JSONDecodeError:
        pass
    
    try:
        # Strategie 4: Text säubern und nochmal versuchen
        cleaned = text.strip()
        if cleaned.startswith("{") and cleaned.endswith("}"):
            return [json.loads(cleaned)]
        elif cleaned.startswith("[") and cleaned.endswith("]"):
            return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    try:
        # Strategie 5: JSON-Reparatur für häufige Fehler
        # Entferne trailing commas
        fixed_text = re.sub(r',(\s*[}\]])', r'\1', text)
        # Füge fehlende Anführungszeichen hinzu
        fixed_text = re.sub(r'(\w+):', r'"\1":', fixed_text)
        return json.loads(fixed_text)
    except json.JSONDecodeError:
        pass
    
    # Wenn alles fehlschlägt, gib eine Fehlermeldung aus
    print(f"⚠️  JSON-Parsing fehlgeschlagen. Antwort-Text:")
    print(f"--- START ---")
    print(text[:500] + "..." if len(text) > 500 else text)
    print(f"--- END ---")
    
    raise ValueError("Konnte keine gültige JSON-Liste in der Antwort finden.")

def ensure_schema(obj: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": obj.get("id"),
        "include": bool(obj.get("include", False)),
        "reason": obj.get("reason") or "",
        "main_form_ok": bool(obj.get("main_form_ok", False)),
        "main_form_suggestion": obj.get("main_form_suggestion") if obj.get("main_form_ok") is False else None,
        "en_ok": bool(obj.get("en_ok", False)),
        "en_suggestions": obj.get("en_suggestions") or [],
        "de_ok": bool(obj.get("de_ok", False)),
        "de_suggestions": obj.get("de_suggestions") or [],
        "notes": obj.get("notes") or "",
        "confidence": float(obj.get("confidence", 0.0)),
    }

def batched(iterable, n):
    batch = []
    for x in iterable:
        batch.append(x)
        if len(batch) == n:
            yield batch
            batch = []
    if batch:
        yield batch

def summarize_batch(items: List[Dict[str, Any]]) -> str:
    ids = [it.get("id", "?") for it in items]
    return f"{len(items)} items: " + ", ".join(ids[:3]) + (" ..." if len(ids) > 3 else "")

# ==== API Call ====
def call_api(model: str, items: List[Dict[str, Any]], temperature: float = 0.2, max_output_tokens: int = 3000) -> (List[Dict[str, Any]], int, int):
    user_content = USER_INSTRUCTIONS + "\n```json\n" + json.dumps(items, ensure_ascii=False, indent=2) + "\n```"
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_tokens=max_output_tokens,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
    )

    try:
        text = resp.choices[0].message.content
    except Exception:
        text = str(resp)

    out = extract_json_list(text)

    # Tokenverbrauch holen
    usage = getattr(resp, "usage", None)
    in_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
    out_tokens = getattr(usage, "completion_tokens", 0) if usage else 0

    return out, in_tokens, out_tokens

# ==== Hauptlogik ====
def main():
    parser = argparse.ArgumentParser(description="Validiere Darija-Wörterbuch-Einträge mit OpenAI und schreibe JSONL-Log.")
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--resume", action="store_true", default=DEFAULT_RESUME)
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Fehler: OPENAI_API_KEY nicht gefunden. Lege .env mit OPENAI_API_KEY=dein_key an.")
        sys.exit(1)

    data = load_json(Path(args.input))
    if args.limit > 0:
        data = data[:args.limit]

    done_ids = set()
    if args.resume and Path(args.output).exists():
        with open(args.output, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    done_ids.add(obj.get("id"))
                except:
                    pass
        print(f"Resume: {len(done_ids)} IDs werden übersprungen.")

    outf = open(args.output, "a", encoding="utf-8")

    total_input_tokens = 0
    total_output_tokens = 0
    total_processed = 0

    try:
        for batch in batched([d for d in data if d.get("id") not in done_ids], args.batch_size):
            print(f"→ Sende Batch ({summarize_batch(batch)}) …")
            tries = 0
            while True:
                tries += 1
                try:
                    results, in_toks, out_toks = call_api(args.model, batch)
                    total_input_tokens += in_toks
                    total_output_tokens += out_toks

                    by_id = {r.get("id"): ensure_schema(r) for r in results if isinstance(r, dict)}
                    missing = [it["id"] for it in batch if it["id"] not in by_id]
                    for mid in missing:
                        by_id[mid] = ensure_schema({
                            "id": mid,
                            "include": False,
                            "reason": "Kein Ergebnis vom Modell.",
                        })

                    for it in batch:
                        outf.write(json.dumps(by_id[it["id"]], ensure_ascii=False) + "\n")
                    outf.flush()

                    total_processed += len(batch)
                    print(f"✓ Batch erledigt ({len(batch)} Items)")
                    break
                except json.JSONDecodeError as e:
                    print(f"⚠️  JSON-Fehler in Versuch {tries}: {e}")
                    if tries >= 3:
                        print(f"✗ Batch nach {tries} Versuchen übersprungen (JSON-Fehler)")
                        # Erstelle Fallback-Einträge für alle Items im Batch
                        for it in batch:
                            fallback = ensure_schema({
                                "id": it["id"],
                                "include": False,
                                "reason": f"JSON-Parsing-Fehler nach {tries} Versuchen.",
                            })
                            outf.write(json.dumps(fallback, ensure_ascii=False) + "\n")
                        outf.flush()
                        total_processed += len(batch)
                        break
                    time.sleep(5 * tries)
                except Exception as e:
                    print(f"⚠️  Allgemeiner Fehler in Versuch {tries}: {e}")
                    if tries >= 3:
                        print(f"✗ Batch nach {tries} Versuchen übersprungen")
                        # Erstelle Fallback-Einträge für alle Items im Batch
                        for it in batch:
                            fallback = ensure_schema({
                                "id": it["id"],
                                "include": False,
                                "reason": f"API-Fehler nach {tries} Versuchen: {str(e)[:100]}",
                            })
                            outf.write(json.dumps(fallback, ensure_ascii=False) + "\n")
                        outf.flush()
                        total_processed += len(batch)
                        break
                    time.sleep(5 * tries)
            time.sleep(0.2)
    finally:
        outf.close()

    # Kostenberechnung
    if args.model in PRICES:
        p_in = PRICES[args.model]["input"]
        p_out = PRICES[args.model]["output"]
        cost = (total_input_tokens / 1e6 * p_in) + (total_output_tokens / 1e6 * p_out)
        print("\n=== Kostenschätzung ===")
        print(f"Input-Tokens:  {total_input_tokens:,} → ${total_input_tokens/1e6 * p_in:.4f}")
        print(f"Output-Tokens: {total_output_tokens:,} → ${total_output_tokens/1e6 * p_out:.4f}")
        print(f"GESAMT geschätzt: ${cost:.4f} USD")
    else:
        print("\n⚠ Preis für Modell nicht bekannt – PRICES dict erweitern.")

    print(f"\nFertig. {total_processed} Items validiert. Ergebnis in: {args.output}")

if __name__ == "__main__":
    main()
