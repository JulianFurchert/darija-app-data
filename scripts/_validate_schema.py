import json
import sys
from jsonschema import Draft7Validator

SCHEMA_FILE = "schema.json"
DATA_FILE = "data/dataset-v01-merged.json"

with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
    schema = json.load(f)

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

validator = Draft7Validator(schema)

errors = list(validator.iter_errors(data))

if not errors:
    print("Alle Daten sind schema-konform.")
    sys.exit(0)

print(f"{len(errors)} Fehler gefunden:")
for err in errors:
    print(f"- Pfad: {list(err.path)}")
    print(f"  Fehler: {err.message}")
    print()
