import json
from pathlib import Path

# Input/Output Dateien
input_path = Path("data/dataset-v02.json")
output_path = Path("data/dataset-v02-fixed.json")

# JSON laden
with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Topics fixen: "." → "_"
for entry in data:
    if "topics" in entry and isinstance(entry["topics"], list):
        entry["topics"] = [t.replace(".", "_") for t in entry["topics"]]

# Neues JSON schreiben
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"✅ Topics ersetzt. Neue Datei gespeichert unter: {output_path}")
