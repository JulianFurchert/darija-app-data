# Dictionary-Data

This repository contains datasets and scripts for processing and analyzing Darija (Moroccan Arabic) dictionary data. The project is organized as follows:

## Directory Structure

- `data/` — Contains processed datasets and logs in JSON and JSONL formats.
- `orginal_data/` — Contains original data files, organized by semantic and syntactic categories, as well as sentences.
  - `semantic categories/` — CSV files for various semantic groups (e.g., animals, food, professions).
  - `sentences/` — CSV file with example sentences.
  - `syntactic categories/` — CSV files for grammatical categories (e.g., verbs, nouns, adjectives).
- `scripts/` — Python scripts for data conversion, categorization, and review.

## Getting Started

1. Clone the repository:
   ```zsh
   git clone <repo-url>
   ```
2. Explore the `data/` and `orginal_data/` folders for datasets.
3. Use the scripts in `scripts/` for data processing tasks.

## Scripts

- `_chatgpt_categorize_and_frequency.py` — Categorizes data and computes frequency statistics.
- `_chatgpt_review.py` — Reviews and validates data entries.
- `_conjug_past_to_jsoh.py` — Converts past tense conjugation data to JSON format.
- `_convert_to_typescript.py` — Converts data to TypeScript format.

## License

Specify your license here (e.g., MIT, GPL, etc.).

## Contact

For questions or contributions, please open an issue or contact the repository maintainer.


## Schema

```
check-jsonschema --schemafile schema.json data/dataset-v01.json
```