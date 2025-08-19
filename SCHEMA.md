# 📘 Darija Dictionary – Konzept-README

Dieses Projekt ist ein digitales **Darija-Wörterbuch für Lernende**, das speziell für Anfänger:innen entwickelt wird.  
Das Ziel ist nicht nur eine reine Wortliste, sondern eine strukturierte Sammlung, die den Einstieg in die Alltagssprache erleichtert.  

---

## 🎯 Ziel des Schemas
Das Schema beschreibt **wie Wörter im Wörterbuch organisiert werden**.  
Es geht dabei weniger um technische Details, sondern um eine **didaktische Struktur**, die Lernenden hilft, Wörter nach **Relevanz, Kontext und Schwierigkeit** einzuordnen.

---

## 🔑 Grundideen

### 1. Fokus auf Alltagssprache
Nicht jedes Wort ist gleich wichtig.  
Darum bekommt jedes Wort Angaben wie:
- **frequency_level** → Wie häufig ist das Wort im Alltag?  
  - `basic` = elementar, sofort nötig (z. B. essen, trinken, hallo)  
  - `common` = oft gebraucht, aber nicht zwingend für den Einstieg  
  - `rare` = nützlich, aber eher später im Lernprozess  
- **formality_level** → In welchem Register wird das Wort benutzt?  
  - `informal` = Alltagssprache, typische Darija-Nutzung  
  - `neutral` = allgemeinverständlich  
  - `formal` = eher schriftlich oder in offiziellen Kontexten  

---

### 2. Lernfreundliche Kategorien (Topics)

Die Wörter sind nach **Themenfeldern** sortiert, die für Lernende intuitiv sind.  
Die Kategorien sind **Hilfsmittel**, nicht jedes Wort muss eine Kategorie haben.  

---

#### 🟢 Basic Needs (Grundbedürfnisse)

Elementare Wörter für den Alltag – **erste Lernstufe**.

- `basic_needs.social_interactions` → greetings, farewells, politeness, simple questions
- `basic_needs.food_drink` → food, drinks, eating, cooking
- `basic_needs.shopping_money` → shopping, bargaining, prices, money
- `basic_needs.numbers` → numbers, quantities, counting
- `basic_needs.time_date` → weekdays, months, yesterday/tomorrow, clock time
- `basic_needs.colours` → colors
- `basic_needs.weather` → sun, rain, hot/cold
- `basic_needs.nature` → sea, tree, mountain, river

---

#### 👥 People (Menschen & Beziehungen)

Alles, was mit Personen, Eigenschaften und Gefühlen zu tun hat.

- `people.family_relationships` → family, relatives, relationships
- `people.body_health` → body parts, health, illness, doctor
- `people.clothes_fashion` → clothing, accessories, fashion
- `people.personal_qualities` → character, behavior, traits
- `people.physical_appearance` → looks, size, hair, age
- `people.feelings_emotions` → happy, sad, angry, tired

---

#### 🏠 Daily Life (Alltag & Freizeit)

Praktische Wörter für Wohnen, Arbeit, Schule und Freizeit.

- `daily_life.home_buildings` → house, rooms, furniture, objects
- `daily_life.travel_transport` → bus, car, street, travel, directions
- `daily_life.work_school` → jobs, professions, studying, education
- `daily_life.leisure_sport` → hobbies, games, sports
- `daily_life.animals` → domestic and wild animals
- `daily_life.media_entertainment` → books, movies, music, TV

---

#### 📈 Extra Advanced (Fortgeschrittene Themen)

Wörter, die für Alltag weniger nötig sind, aber wichtig für **höheres Sprachniveau**.

- `extra_advanced.politics_society` → politics, society, law
- `extra_advanced.science_technology` → science, technology, computers
- `extra_advanced.environment` → ecology, sustainability, environment
- `extra_advanced.business_economy` → economy, finance, business
- `extra_advanced.culture_art` → art, literature, culture
- `extra_advanced.religion` → religion, beliefs

---

### 3. Grammatik nur wo nötig
- **Gender** und **Number** → nur bei Nomen  
- **Conjugations** → nur bei Verben  
- Andere Wörter (Adverbien, Präpositionen, Partikel) bleiben schlicht.  

---

### 4. Mehrsprachigkeit
Jedes Wort hat mindestens:
- die **Darija-Form in Arabizi**  
- optional die **arabische Schriftform**  
- **Englische** Übersetzungen  
- **Deutsche** Übersetzungen  

---

### 5. Lernhilfe durch Summaries
Zusätzlich zu Übersetzungen können **kurze Lernhilfen** ergänzt werden:  
- Alltagssituation  
- Stolperfallen  
- Beispielnutzung  

---

## 📚 Beispiel-Eintrag

```json
{
  "id": "123",
  "darija": "salam",
  "darija_arabic_script": "سلام",
  "en": ["hello"],
  "de": ["hallo"],
  "class": "expression",
  "frequency_level": "basic",
  "formality_level": "neutral",
  "topics": ["basic_needs.greetings"],
  "user_summary_en": "Common greeting used at any time of the day.",
  "user_summary_de": "Allgemeine Begrüßung, zu jeder Tageszeit."
}
```

---

## 🚀 Fazit
Das Wörterbuch-Schema verbindet:
- **Alltagstauglichkeit** (Fokus auf häufige Wörter)  
- **Systematische Struktur** (Themenfelder + Schwierigkeitsgrad)  
- **Flexibilität** (nicht jedes Wort braucht Kategorie/Grammatik)  

Damit entsteht eine Datenbasis, die **Lernenden Schritt für Schritt** Darija näherbringt – von den allerwichtigsten Wörtern bis zu anspruchsvolleren Themen wie Politik, Kunst oder Religion.  
