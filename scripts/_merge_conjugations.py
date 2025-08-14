# tools/merge_conjugations.py
import json
import csv
import sys
import pathlib

DATA_JSON = pathlib.Path("data/dataset-v01.json")
PRESENT_CSV = pathlib.Path("orginal_data/syntactic categories/conjug_present.csv")
PAST_CSV = pathlib.Path("orginal_data/syntactic categories/conjug_past.csv")

PRONOUNS = ["ana","nta","nti","howa","hia","7na","ntoma","homa"]

def normalize(s: str) -> str:
    return (s or "").strip().lower()

def load_json_array(path: pathlib.Path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"{path} muss ein JSON-Array sein.")
        return data
    except FileNotFoundError:
        print(f"[ERROR] Datei fehlt: {path}")
        sys.exit(1)

def read_present_by_root(path: pathlib.Path):
    """Erwartet: root, ana, nta, ..., homa  -> Index: root -> {pronoun:form}"""
    out = {}
    if not path.exists():
        print(f"[ERROR] CSV fehlt: {path}")
        sys.exit(1)
    with path.open(encoding="utf-8") as f:
        r = csv.DictReader(f)
        headers = r.fieldnames or []
        if "root" not in headers:
            raise ValueError(f"present CSV braucht eine 'root'-Spalte. Gefunden: {headers}")
        for row in r:
            root = normalize(row.get("root"))
            if not root:
                continue
            out[root] = {p: (row.get(p) or "").strip() for p in PRONOUNS if p in headers and row.get(p)}
    return out

def read_past_by_howa(path: pathlib.Path):
    """
    Erwartet KEIN 'root'. Wir indexieren über die howa-Form:
    Index: howa -> {pronoun:form}
    """
    out = {}
    if not path.exists():
        print(f"[ERROR] CSV fehlt: {path}")
        sys.exit(1)
    with path.open(encoding="utf-8") as f:
        r = csv.DictReader(f)
        headers = r.fieldnames or []
        if "howa" not in headers:
            raise ValueError(f"past CSV braucht eine 'howa'-Spalte. Gefunden: {headers}")
        for row in r:
            howa = normalize(row.get("howa"))
            if not howa:
                # Zeile ohne howa-Form überspringen
                continue
            out[howa] = {p: (row.get(p) or "").strip() for p in PRONOUNS if p in headers and row.get(p)}
    return out

def main():
    entries = load_json_array(DATA_JSON)
    present_by_root = read_present_by_root(PRESENT_CSV)
    past_by_howa    = read_past_by_howa(PAST_CSV)

    used_second_variant = []   # bisher: wenn 2. Variante gebraucht wurde
    not_found = []             # bisher: weder present noch past gefunden
    present_missing = []       # NEU: past gefunden, present fehlt
    past_missing = []          # NEU: present gefunden, past fehlt
    updated = 0

    for entry in entries:
        if entry.get("class") != "verb":
            continue

        variants = entry.get("darija_latin") or []
        v1 = normalize(variants[0]) if len(variants) >= 1 else ""
        v2 = normalize(variants[1]) if len(variants) >= 2 else ""

        conj_present = {}
        conj_past = {}
        matched_with_second = False

        # 1) Erstes darija_latin: present via root, past via howa
        if v1:
            if v1 in present_by_root:
                conj_present = present_by_root[v1]
            if v1 in past_by_howa:
                conj_past = past_by_howa[v1]

        # 2) Wenn beides leer, versuche zweites darija_latin
        if not conj_present and not conj_past and v2:
            if v2 in present_by_root:
                conj_present = present_by_root[v2]
                matched_with_second = True
            if v2 in past_by_howa:
                conj_past = past_by_howa[v2]
                matched_with_second = True

        # 3) Warnen, wenn past gefunden, aber keine howa-Key (sollte durch Reader schon verhindert sein)
        if conj_past and "howa" not in conj_past:
            print(f"[WARN] 'past' gefunden aber ohne howa-Form: id={entry.get('id')}")

        # 4) conjugations setzen (future immer leeres Objekt)
        entry["conjugations"] = {
            "present": conj_present,
            "past": conj_past,
            "future": entry.get("conjugations", {}).get("future", {})  # falls schon was existiert
        }
        if not entry["conjugations"]["future"]:
            entry["conjugations"]["future"] = {}

        # 5) Logging / Zählung
        if conj_present or conj_past:
            updated += 1
            if matched_with_second:
                used_second_variant.append({
                    "id": entry.get("id"),
                    "first": variants[0] if variants else "",
                    "second": variants[1] if len(variants) > 1 else ""
                })
            # NEU: Teiltreffer erfassen
            if conj_present and not conj_past:
                past_missing.append({
                    "id": entry.get("id"),
                    "first": variants[0] if variants else "",
                    "second": variants[1] if len(variants) > 1 else ""
                })
            elif conj_past and not conj_present:
                present_missing.append({
                    "id": entry.get("id"),
                    "first": variants[0] if variants else "",
                    "second": variants[1] if len(variants) > 1 else ""
                })
        else:
            not_found.append({
                "id": entry.get("id"),
                "first": variants[0] if variants else "",
                "second": variants[1] if len(variants) > 1 else ""
            })

    # Ausgabe schreiben
    out_path = DATA_JSON.with_name(DATA_JSON.stem + "-with-conj.json")
    out_path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")

    # Logs / Zusammenfassung
    print(f"[INFO] Verben mit Konjugationen aktualisiert: {updated}")

    if used_second_variant:
        print(f"[INFO] Treffer mit zweitem darija_latin: {len(used_second_variant)}")
        for it in used_second_variant[:20]:
            print(f"  - id={it['id']} | first='{it['first']}' → second benutzt='{it['second']}'")
        if len(used_second_variant) > 20:
            print(f"  ... und {len(used_second_variant)-20} weitere")

    # NEU: Teiltreffer-Logs
    if past_missing:
        print(f"[PARTIAL] Nur present gefunden (past fehlt): {len(past_missing)}")
        for it in past_missing[:20]:
            print(f"  - id={it['id']} | first='{it['first']}' | second='{it['second']}'")
        if len(past_missing) > 20:
            print(f"  ... und {len(past_missing)-20} weitere")

    if present_missing:
        print(f"[PARTIAL] Nur past gefunden (present fehlt): {len(present_missing)}")
        for it in present_missing[:20]:
            print(f"  - id={it['id']} | first='{it['first']}' | second='{it['second']}'")
        if len(present_missing) > 20:
            print(f"  ... und {len(present_missing)-20} weitere")

    if not_found:
        print(f"[INFO] Keine Konjugationen gefunden für: {len(not_found)}")
        for it in not_found[:20]:
            print(f"  - id={it['id']} | first='{it['first']}' | second='{it['second']}'")
        if len(not_found) > 20:
            print(f"  ... und {len(not_found)-20} weitere")

    print(f"[OK] geschrieben: {out_path}")

if __name__ == "__main__":
    main()
