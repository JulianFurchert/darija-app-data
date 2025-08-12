import pandas as pd
import json
import hashlib

def convert_csv_to_typescript():
    """Convert the CSV dataset to TypeScript format"""
    
    # Load the CSV dataset
    print("Loading CSV dataset...")
    df = pd.read_csv('dataset-v01.csv')
    
    print(f"Converting {len(df)} words to TypeScript...")
    
    # Create TypeScript interface
    typescript_interface = """export interface DictionaryEntry {
  id: string;
  darija_latin: string;
  darija_ar: string;
  eng: string;
  de: string;
  class: string;
  darija_latin_alt?: string;
  n1?: string;
  n2?: string;
  n3?: string;
  n4?: string;
  eng2?: string;
  eng3?: string;
  eng4?: string;
  de2?: string;
  de3?: string;
  de4?: string;
}

export const dictionaryData: DictionaryEntry[] = [
"""
    
    # Convert each row to TypeScript object
    typescript_entries = []
    
    for idx, row in df.iterrows():
        # Create entry object
        entry = {}
        
        # Add required fields
        entry['darija_latin'] = str(row['darija_latin']) if pd.notna(row['darija_latin']) else ''
        entry['darija_ar'] = str(row['darija_ar']) if pd.notna(row['darija_ar']) else ''
        entry['eng'] = str(row['eng']) if pd.notna(row['eng']) else ''
        entry['class'] = str(row['class']) if pd.notna(row['class']) else ''
        
        # Handle German translation with special rule
        if pd.notna(row['de']) and str(row['de']).strip() != '':
            entry['de'] = str(row['de']).strip()
        else:
            # If eng is "zero", set de to "null"
            if entry['eng'].lower() == 'zero':
                entry['de'] = 'null'
            else:
                entry['de'] = ''  # Required field, so we need a value
        
        # Generate unique ID based on darija_latin, darija_ar, and class
        id_string = f"{entry['darija_latin']}|{entry['darija_ar']}|{str(row.get('class', ''))}"
        id_hash = hashlib.md5(id_string.encode('utf-8')).hexdigest()
        # Take first 12 characters for a shorter ID
        entry['id'] = id_hash[:12]
        
        # Add optional fields (only if they have values)
        optional_fields = [
            'darija_latin_alt', 'n1', 'n2', 'n3', 'n4',
            'eng2', 'eng3', 'eng4', 'de2', 'de3', 'de4'
        ]
        
        for field in optional_fields:
            if field in row and pd.notna(row[field]) and str(row[field]).strip() != '':
                entry[field] = str(row[field]).strip()
        
        # Convert to TypeScript object string
        entry_str = "  {\n"
        for key, value in entry.items():
            # Escape quotes in the value
            escaped_value = str(value).replace('"', '\\"').replace("'", "\\'")
            entry_str += f'    {key}: "{escaped_value}",\n'
        entry_str = entry_str.rstrip(',\n') + "\n  }"
        
        typescript_entries.append(entry_str)
    
    # Combine everything
    typescript_content = typescript_interface + ",\n".join(typescript_entries) + "\n];\n"
    
    # Save to TypeScript file
    output_file = 'dataset-v01.ts'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(typescript_content)
    
    print(f"TypeScript file saved to {output_file}")
    print(f"Total entries: {len(typescript_entries)}")
    
    # Show some statistics
    print(f"\nStatistics:")
    print(f"  - Total words: {len(df)}")
    
    # Count words with darija_latin_alt
    alt_count = df['darija_latin_alt'].notna().sum()
    print(f"  - Words with darija_latin_alt: {alt_count}")
    
    # Count words with different classes
    class_counts = df['class'].value_counts()
    print(f"  - Word classes:")
    for class_name, count in class_counts.items():
        print(f"    - {class_name}: {count}")
    
    # Show first few entries as example
    print(f"\nFirst 3 entries in TypeScript format:")
    for i, entry in enumerate(typescript_entries[:3]):
        print(f"\nEntry {i+1}:")
        print(entry)

if __name__ == "__main__":
    convert_csv_to_typescript() 