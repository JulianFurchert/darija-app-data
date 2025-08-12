#!/usr/bin/env python3
"""
Kategorisiert Wörter nach semantischen Kategorien und bewertet deren Häufigkeit
in der alltäglichen marokkanischen Darija.
"""

import json
import time
import os
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv

# Lade .env Datei
load_dotenv()

# OpenAI API Setup
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def load_dataset(dataset_path):
    """Lädt das Dataset aus JSON"""
    with open(dataset_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_batch_categorization_prompt(word_batch):
    """Erstellt den Prompt für Batch-Kategorisierung und Häufigkeitsbewertung"""
    
    # Alle Kategorien zusammensammeln
    all_categories = {
        'noun': [
            "people_professions", "places_environment", "animals_plants", "objects_tools",
            "food_drink", "culture_leisure", "religion_belief", "abstract_concepts"
        ],
        'verb': [
            "movement", "communication", "feelings_emotions", "perception",
            "thinking_planning", "change_transformation", "creation_work", "religious_actions"
        ],
        'adjective': [
            "colors", "size_shape", "condition_state", "feelings_mood",
            "evaluation_quality", "temperature", "quantity_intensity", "religious_descriptions"
        ]
    }
    
    # Erstelle Wörter-Liste
    words_data = []
    for i, word_data in enumerate(word_batch, 1):
        darija_latin = ', '.join(word_data.get('darija_latin', []))
        darija_ar = word_data.get('darija_ar', '')
        word_class = word_data.get('class', '')
        en_translations = ', '.join(word_data.get('en', []))
        de_translations = ', '.join(word_data.get('de', []))
        
        relevant_categories = all_categories.get(word_class, ["other"])
        categories_text = ", ".join(relevant_categories)
        
        word_entry = f"""
WORT {i}:
- ID: {word_data['id']}
- Darija (lateinisch): {darija_latin}
- Darija (arabisch): {darija_ar}
- Wortart: {word_class}
- Englisch: {en_translations}
- Deutsch: {de_translations}
- Mögliche Kategorien: {categories_text}
"""
        words_data.append(word_entry)
    
    words_text = "\n".join(words_data)
    
    prompt = f"""
Du bist ein Experte für marokkanische Darija (marokkanisches Arabisch).
Analysiere diese {len(word_batch)} Wörter und antworte AUSSCHLIESSLICH mit gültigem JSON-Array.

{words_text}

AUFGABEN FÜR JEDES WORT:

1. KATEGORISIERUNG: Wähle die passendste Kategorie aus den angegebenen Möglichkeiten, oder "other".

2. HÄUFIGKEIT IM ALLTAG (0-100):
0 = praktisch nie (nur Hocharabisch/formal)
25 = selten, spezielle Kontexte  
50 = gelegentlich, bekannt aber nicht alltäglich
75 = häufig, wichtig für Lernende
100 = sehr häufig, essentiell im Alltag

3. HOCHARABISCH-ERKENNUNG:
- true = primär Hocharabisch, selten in alltäglicher Darija
- false = echtes, alltägliches Darija

4. BENUTZER-SUMMARY:

Schreibe je EINEN kurzen, informativen Satz in Deutsch und Englisch 
für ein Online-Wörterbuch für Darija-Wörter.

Regeln:
- Maximal 20 Wörter pro Satz.
- WICHTIG: Erwähne NICHT das Wort selbst noch die Übersetzung.
- Satz muss je nach Fall Folgendes enthalten:

1. Falls nicht alltäglich UND aus dem Hocharabischen:
   → Hinweis einfügen („stammt aus dem Hocharabischen“ / „from Standard Arabic“).

2. Falls nicht alltäglich:
   → sagen, wo es hauptsächlich verwendet wird (z. B. „in religiösen Texten“, „in formellen Reden“, „bei speziellen Anlässen“).

3. Falls oft verwendet:
   → deutlich machen, dass es ein wichtiges oder zentrales Wort für den Alltag ist.

4. Falls kein relevanter oder plausibler Kontext vorhanden ist, 
   KEINEN künstlichen oder abstrakten Kontext erfinden. 
   Abstrakte Phrasen wie "Gespräche über Einflüsse"  
   machen keinen Sinn und müssen vermieden werden.

Beispiele Deutsch:
- Es wird selten verwendet, stammt aus dem Hocharabischen und wird in religiösen Texten genutzt.
- Es wird vor allem in formellen Reden verwendet und ist im Alltag weniger wichtig.
- Es wird häufig beim Einkaufen benutzt und ist ein wichtiges Wort für den Alltag.
- Es wird häufig in landwirtschaftlichen Kontexten verwendet, ist jedoch im Alltag weniger wichtig.
- Es wird oft in Familiengesprächen genutzt und ist zentral im täglichen Sprachgebrauch.
- Es wird sehr häufig in Gesprächen genutzt und ist essentiell im Alltag.

Beispiele Englisch:
- It is rarely used, comes from Standard Arabic and is used in religious texts.
- It is mainly used in formal speeches and is less relevant in daily life.
- It is common when shopping and is an important word for daily life.
- It is often used in agricultural contexts but is less important in daily life.
- It is often used in family conversations and is central in everyday language.
- It is very frequently used in conversations and is essential in daily life.


Wenn es zentral ist brauchst du keine 



Antworte NUR mit JSON-Array in dieser Reihenfolge:
[
  {{
    "id": "wort_id_1",
    "category": "gewählte_kategorie",
    "category_confidence": 0.8,
    "frequency_score": 75,
    "is_daily_darija": true,
    "is_standard_arabic": false,
    "user_summary_de": "Kurzer Satz mit Häufigkeit und Lernwert",
    "user_summary_en": "Short sentence with frequency and learning value"
  }},
  ...
]
"""
    
    return prompt

def get_batch_categorization_from_openai(word_batch, max_retries=3):
    """Holt Kategorisierung für ganzen Batch von OpenAI mit Retry-Logik"""
    
    prompt = create_batch_categorization_prompt(word_batch)
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": "Du bist ein Experte für marokkanische Darija. Antworte immer mit gültigem JSON-Array."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,  # Mehr Tokens für Batch
                temperature=0.3
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Versuche JSON zu parsen mit verschiedenen Strategien
            try:
                # Direkt parsen
                result = json.loads(response_text)
                
                # Validiere dass es ein Array ist und die richtige Anzahl hat
                if isinstance(result, list) and len(result) == len(word_batch):
                    return result
                else:
                    raise ValueError(f"Falsche Array-Länge: erwartet {len(word_batch)}, erhalten {len(result) if isinstance(result, list) else 'kein Array'}")
                    
            except json.JSONDecodeError:
                # JSON aus Text extrahieren
                import re
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    if isinstance(result, list) and len(result) == len(word_batch):
                        return result
                    else:
                        raise ValueError(f"Falsche Array-Länge: erwartet {len(word_batch)}, erhalten {len(result) if isinstance(result, list) else 'kein Array'}")
                else:
                    raise ValueError("Kein JSON-Array gefunden")
                    
        except Exception as e:
            print(f"Fehler bei Batch-Attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                # Fallback: Erstelle Standard-Antworten für alle Wörter im Batch
                fallback_results = []
                for word_data in word_batch:
                    fallback_results.append({
                        "id": word_data['id'],
                        "category": "other",
                        "category_confidence": 0.0,
                        "frequency_score": 50,
                        "is_daily_darija": False,
                        "is_standard_arabic": True,
                        "user_summary_de": "Automatische Bewertung - bitte manuell überprüfen",
                        "user_summary_en": "Automatic assessment - please check manually"
                    })
                return fallback_results

def process_words(dataset, output_path, batch_size=5):
    """Verarbeitet alle Wörter und speichert Ergebnisse"""
    
    total_words = len(dataset)
    processed = 0
    
    # Lade existierende Ergebnisse falls vorhanden
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            existing_results = [json.loads(line) for line in f if line.strip()]
        existing_ids = {result['id'] for result in existing_results}
        print(f"📂 {len(existing_results)} bereits verarbeitete Wörter gefunden")
    else:
        existing_ids = set()
    
    with open(output_path, 'a', encoding='utf-8') as f:
        for i in range(0, total_words, batch_size):
            batch = dataset[i:i + batch_size]
            
            # Filtere bereits verarbeitete Wörter aus dem Batch
            unprocessed_batch = []
            batch_start_count = processed
            
            for word_data in batch:
                word_id = word_data['id']
                if word_id in existing_ids:
                    processed += 1
                    continue
                unprocessed_batch.append(word_data)
            
            # Skip leeren Batch
            if not unprocessed_batch:
                continue
            
            # Zeige Batch-Info
            batch_words = [', '.join(word.get('darija_latin', ['?'])) for word in unprocessed_batch]
            print(f"🔄 Batch {i//batch_size + 1}: Verarbeite {len(unprocessed_batch)} Wörter: {' | '.join(batch_words[:3])}")
            if len(batch_words) > 3:
                print(f"    ... und {len(batch_words) - 3} weitere")
            
            # EINEN API-Call für den ganzen Batch
            categorizations = get_batch_categorization_from_openai(unprocessed_batch)
            
            # Erstelle Ergebnis-Einträge
            batch_results = []
            for word_data, categorization in zip(unprocessed_batch, categorizations):
                result = {
                    "id": word_data['id'],
                    "timestamp": datetime.now().isoformat(),
                    **categorization
                }
                batch_results.append(result)
                processed += 1
            
            # Speichere ganzen Batch auf einmal
            for result in batch_results:
                f.write(json.dumps(result, ensure_ascii=False) + '\n')
            f.flush()  # Batch-flush
            
            print(f"✅ Batch {i//batch_size + 1} abgeschlossen. {processed}/{total_words} verarbeitet")
    
    print(f"🎉 Kategorisierung abgeschlossen! {processed} Wörter verarbeitet.")

def create_summary_report(categorization_path, dataset_path, output_path):
    """Erstellt einen zusammenfassenden Bericht"""
    
    # Lade Daten
    with open(categorization_path, 'r', encoding='utf-8') as f:
        categorizations = [json.loads(line) for line in f if line.strip()]
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    # ID-Mapping erstellen
    id_to_word = {word['id']: word for word in dataset}
    
    # Statistiken sammeln
    category_stats = {}
    frequency_stats = {'0-25': 0, '26-50': 0, '51-75': 0, '76-100': 0}
    daily_darija_count = 0
    
    for cat in categorizations:
        # Kategorie-Statistiken
        category = cat.get('category', 'unknown')
        if category not in category_stats:
            category_stats[category] = 0
        category_stats[category] += 1
        
        # Häufigkeits-Statistiken
        freq = cat.get('frequency_score', 0)
        if freq <= 25:
            frequency_stats['0-25'] += 1
        elif freq <= 50:
            frequency_stats['26-50'] += 1
        elif freq <= 75:
            frequency_stats['51-75'] += 1
        else:
            frequency_stats['76-100'] += 1
        
        # Daily Darija count
        if cat.get('is_daily_darija', False):
            daily_darija_count += 1
    
    # Bericht erstellen
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("DARIJA KATEGORISIERUNG & HÄUFIGKEITS-ANALYSE\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
        f.write(f"Analysierte Wörter: {len(categorizations)}\n\n")
        
        f.write("KATEGORIEN-VERTEILUNG:\n")
        f.write("-" * 30 + "\n")
        for category, count in sorted(category_stats.items()):
            percentage = (count / len(categorizations)) * 100
            f.write(f"{category:<25}: {count:>4} ({percentage:5.1f}%)\n")
        
        f.write(f"\nHÄUFIGKEITS-VERTEILUNG:\n")
        f.write("-" * 30 + "\n")
        total = len(categorizations)
        for range_name, count in frequency_stats.items():
            percentage = (count / total) * 100
            f.write(f"{range_name:<10}: {count:>4} ({percentage:5.1f}%)\n")
        
        f.write(f"\nALLTÄGLICHE DARIJA:\n")
        f.write("-" * 30 + "\n")
        daily_percentage = (daily_darija_count / len(categorizations)) * 100
        f.write(f"Alltäglich: {daily_darija_count} ({daily_percentage:.1f}%)\n")
        f.write(f"Nicht alltäglich: {len(categorizations) - daily_darija_count} ({100 - daily_percentage:.1f}%)\n")
        
        f.write(f"\nHOCH-BEWERTETE WÖRTER (Häufigkeit ≥ 75):\n")
        f.write("-" * 50 + "\n")
        high_freq_words = [cat for cat in categorizations if cat.get('frequency_score', 0) >= 75]
        for cat in sorted(high_freq_words, key=lambda x: x.get('frequency_score', 0), reverse=True)[:20]:
            word = id_to_word.get(cat['id'], {})
            darija = ', '.join(word.get('darija_latin', ['?']))
            freq = cat.get('frequency_score', 0)
            category = cat.get('category', '?')
            f.write(f"{darija:<20} | {freq:>3} | {category}\n")
    
    print(f"📊 Bericht erstellt: {output_path}")

def main():
    # Dateipfade - FESTE Namen für Fortsetzung nach Abbruch
    dataset_path = "dataset-v01.json"
    output_path = "categorization_log.jsonl"  # OHNE Timestamp!
    summary_path = f"categorization_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    
    print("🚀 Starte Kategorisierung und Häufigkeitsanalyse...")
    print(f"📂 Input: {dataset_path}")
    print(f"📝 Output: {output_path}")
    
    # Lade Dataset
    print("📥 Lade Dataset...")
    dataset = load_dataset(dataset_path)
    print(f"✅ {len(dataset)} Wörter geladen")
    
    # Verarbeite Wörter (mit automatischer Fortsetzung)
    print("🔄 Starte Verarbeitung...")
    process_words(dataset, output_path)
    
    # Erstelle Zusammenfassung
    print("📊 Erstelle Bericht...")
    create_summary_report(output_path, dataset_path, summary_path)
    
    print(f"🎉 Fertig! Ergebnisse in:")
    print(f"   📋 Kategorisierungen: {output_path}")
    print(f"   📊 Zusammenfassung: {summary_path}")

if __name__ == "__main__":
    main()
