import dotenv
import deepl
import os

# Load environment variables from .env file
dotenv.load_dotenv()

# Get the OpenAI API key from environment variables
DEEPL_TOKEN = os.getenv("DEEPL_TOKEN")
if DEEPL_TOKEN is None:
    raise ValueError(
        "DEEPL_TOKEN environment variable not set. Please set it in the .env file."
    )

DEEPL_URL = os.getenv("DEEPL_URL")
if DEEPL_URL is None:
    raise ValueError(
        "DEEPL_URL environment variable not set. Please set it in the .env file."
    )

LANGUAGES = os.getenv("LANGUAGES")
if LANGUAGES is None:
    raise ValueError(
        "LANGUAGES environment variable not set. Please set it in the .env file."
    )

SOURCE_LANG = os.getenv("SOURCE_LANG")
if SOURCE_LANG is None:
    raise ValueError(
        "SOURCE_LANG environment variable not set. Please set it in the .env file."
    )


# search for all .properties files in the current directory and subdirectories
def find_properties_files():
    properties_files = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".properties") and not is_language_properties_file(file):
                properties_files.append(os.path.join(root, file))
    return properties_files


def is_language_properties_file(file_path):
    # Check if the file contains the language code in its name
    for lang in LANGUAGES.split(","):
        if file_path.endswith(lang + ".properties"):
            return True
    return False


def find_source_lang_properties_files():
    """
    Sucht alle .properties Dateien, die mit der SOURCE_LANG Endung enden,
    z.B. *_de.properties, wenn SOURCE_LANG=de.
    """
    properties_files = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(f"_{SOURCE_LANG}.properties"):
                properties_files.append(os.path.join(root, file))
    return properties_files


def load_translation_store(store_path):
    """
    Lädt den Translation Store aus einer txt Datei.
    Format je Zeile: key|source_text|target_lang|translated_text
    Gibt ein Dictionary zurück: {(key, source_text, target_lang): translated_text}
    """
    store = {}
    if not os.path.exists(store_path):
        return store
    with open(store_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("|", 3)
            if len(parts) == 4:
                store[(parts[0], parts[1], parts[2])] = parts[3]
    return store


def append_to_translation_store(
    store_path, key, source_text, target_lang, translated_text
):
    """
    Fügt eine neue Übersetzung zum Store hinzu.
    """
    with open(store_path, "a", encoding="utf-8") as f:
        f.write(f"{key}|{source_text}|{target_lang}|{translated_text}\n")


# Translate the content of a .properties file and save it back to file
def translate_properties_file(file_path, target_lang):
    # Deepl client initialisieren
    translator = deepl.Translator(DEEPL_TOKEN)
    store_path = "translation_store.txt"
    translation_store = load_translation_store(store_path)

    translated_lines = []
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            # Kommentare und leere Zeilen nicht übersetzen
            if line.strip().startswith("#") or line.strip() == "":
                translated_lines.append(line)
                continue
            # Key und Value trennen
            if "=" in line:
                key, value = line.split("=", 1)
                source_text = value.strip()
                store_key = (key.strip(), source_text, target_lang)
                if store_key in translation_store:
                    # Übersetzung aus dem Store verwenden
                    translated_value = translation_store[store_key]
                else:
                    # Übersetzen und in den Store schreiben
                    try:
                        translated_value = translator.translate_text(
                            source_text,
                            source_lang=SOURCE_LANG,
                            target_lang=target_lang,
                        ).text
                    except Exception as e:
                        print(f"Fehler beim Übersetzen von '{source_text}': {e}")
                        translated_value = source_text
                    append_to_translation_store(
                        store_path,
                        key.strip(),
                        source_text,
                        target_lang,
                        translated_value,
                    )
                translated_lines.append(f"{key}={translated_value}\n")
            else:
                translated_lines.append(line)

    # Neues Dateinamenformat: main_fr.properties
    base, ext = os.path.splitext(file_path)
    if base.endswith(f"_{SOURCE_LANG}"):
        base = base[: -(len(SOURCE_LANG) + 1)]
    new_file_path = f"{base}_{target_lang}{ext}"
    with open(new_file_path, "w", encoding="utf-8") as file:
        file.writelines(translated_lines)
    print(f"Translated {file_path} to {new_file_path}")


# Main function to translate all .properties files
def main():
    # Nur die SOURCE_LANG properties-Dateien finden
    properties_files = find_source_lang_properties_files()

    # Für jede Zielsprache außer SOURCE_LANG übersetzen
    for file_path in properties_files:
        for lang in LANGUAGES.split(","):
            if lang != SOURCE_LANG:
                translate_properties_file(file_path, lang)


if __name__ == "__main__":
    main()
