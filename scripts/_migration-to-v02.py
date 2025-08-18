import json

def migrate_entry(old_entry):
    new_entry = {}

    # IDs
    new_entry["id"] = old_entry.get("id")
    if "originalId" in old_entry:
        new_entry["originalId"] = old_entry["originalId"]

    # Darija Formen
    new_entry["darija_arabic_script"] = old_entry.get("darija_ar", "")
    latin_forms = old_entry.get("darija_latin", [])
    if latin_forms:
        new_entry["darija"] = latin_forms[0]  # Hauptform = erste Latin-Form
        new_entry["darija_alt"] = latin_forms[1:]  # Rest als alternative Schreibungen
    else:
        new_entry["darija"] = ""
        new_entry["darija_alt"] = []

    # Übersetzungen
    new_entry["en"] = old_entry.get("en", [])
    new_entry["de"] = old_entry.get("de", [])

    # Grammatik
    new_entry["class"] = old_entry.get("class")
    new_entry["gender"] = old_entry.get("gender")
    new_entry["number"] = old_entry.get("number")

    # Frequency & Formality (im alten Schema nicht vorhanden → leer)
    new_entry["frequency_level"] = None
    new_entry["formality_level"] = None

    # Topics (im neuen Schema, aber wir migrieren die alten category nur ins validation!)
    new_entry["topics"] = []

    # Conjugations übernehmen falls vorhanden
    if "conjugations" in old_entry:
        new_entry["conjugations"] = old_entry["conjugations"]

    # WordForms übernehmen falls vorhanden
    if "forms" in old_entry:
        new_entry["wordForms"] = [
            {
                "word": f.get("latin"),
                "gender": f.get("gender"),
                "number": f.get("number")
            }
            for f in old_entry["forms"]
        ]

    # Neue Felder für User Summaries (leer setzen)
    new_entry["user_summary_de"] = ""
    new_entry["user_summary_en"] = ""

    # Reviewed / Include etc.
    new_entry["reviewed"] = old_entry.get("reviewed", False)
    new_entry["include"] = old_entry.get("include", True)

    # Validation übernehmen + alte Felder reinschieben
    validation = old_entry.get("validation", {})

    # Migration: category & category_confidence
    if "category" in old_entry:
        validation["old_category"] = old_entry["category"]
    if "category_confidence" in old_entry:
        validation["old_category_confidence"] = old_entry["category_confidence"]

    # Frequenz & Flags
    if "frequency_score" in old_entry:
        validation["old_frequency_score"] = old_entry["frequency_score"]
    if "is_daily_darija" in old_entry:
        validation["old_is_daily_darija"] = old_entry["is_daily_darija"]
    if "is_standard_arabic" in old_entry:
        validation["old_is_standard_arabic"] = old_entry["is_standard_arabic"]

    # User summaries alt sichern
    if "user_summary_de" in old_entry and old_entry["user_summary_de"]:
        validation["old_user_summary_de"] = old_entry["user_summary_de"]
    if "user_summary_en" in old_entry and old_entry["user_summary_en"]:
        validation["old_user_summary_en"] = old_entry["user_summary_en"]

    new_entry["validation"] = validation

    # Notes falls vorhanden
    if "note" in old_entry:
        new_entry["note"] = old_entry["note"]

    return new_entry


def migrate_file(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    migrated = [migrate_entry(entry) for entry in data]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(migrated, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    migrate_file("data/dataset-v01.json", "data/dataset-v02.json")
    print("Migration complete: dataset-v01.json → dataset-v02.json")
