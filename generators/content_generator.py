import json
from pathlib import Path

from openai import OpenAI

from config import load_api_key
from utils.cost_tracker import record_gpt_cost


def load_content_settings():
    defaults = {
        "openai_model": "gpt-5-mini",
        "target_script_max_words": 160,
    }
    settings_file = Path("config/settings.json")

    if not settings_file.exists():
        return defaults

    try:
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("Die Datei config/settings.json enthält kein gültiges JSON.")
        return defaults

    return {key: settings.get(key, value) for key, value in defaults.items()}


def validate_content(content):
    if content is None or not all(
        content.get(key) for key in ("title", "description", "hashtags", "script")
    ):
        print("Ungültige AI-Antwort.")
        return False

    return True


def parse_content(content):
    sections = {
        "title": [],
        "description": [],
        "hashtags": [],
        "script": [],
    }
    current_section = None

    for line in content.splitlines():
        section_name = line.rstrip(":").lower()

        if section_name in sections and line.endswith(":"):
            current_section = section_name
        elif current_section is not None:
            sections[current_section].append(line)

    return {
        name: "\n".join(lines).strip()
        for name, lines in sections.items()
    }


def generate_content(topic):
    prompt_file = Path("prompts/content_prompt.txt")

    if not prompt_file.exists():
        print("Die Prompt-Datei prompts/content_prompt.txt wurde nicht gefunden.")
        return None

    api_key = load_api_key()

    if not api_key:
        raise RuntimeError("Kein API-Key gefunden.")

    settings = load_content_settings()
    prompt = prompt_file.read_text(encoding="utf-8").format(topic=topic)
    prompt += """

Zusätzliche zwingende Hook-Regeln für das SCRIPT:
- Die ersten 1 bis 2 Sätze müssen innerhalb der ersten 2 Sekunden sofort Neugier
  und Spannung erzeugen.
- Beginne mit einer starken, konkreten Aussage, einer überraschenden Konsequenz
  oder einer zugespitzten Frage zum Thema.
- Der Hook muss wahrheitsgemäß bleiben und darf keine Clickbait-Lüge enthalten.
- Vermeide langsame Einleitungen und Erklärungen vor dem Hook.
"""

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=settings["openai_model"],
        input=prompt,
    )
    record_gpt_cost()

    return parse_content(response.output_text)


def extend_script(topic, script, minimum_words):
    """Erweitert ein zu kurzes Skript ohne vorhandene Aussagen zu wiederholen."""
    api_key = load_api_key()

    if not api_key:
        raise RuntimeError("Kein API-Key gefunden.")

    settings = load_content_settings()
    prompt = f"""Überarbeite dieses deutsche YouTube-Shorts-Skript zum Thema
„{topic}“ so, dass es mindestens {minimum_words} und höchstens {settings["target_script_max_words"]} Wörter hat.

Ergänze nur relevante, plausible Fakten oder Folgen. Wiederhole keine Aussage,
erfinde keine Fakten und behalte den starken, wahrheitsgemäßen Hook am Anfang.
Gib ausschließlich den fertigen Sprechertext aus.

SCRIPT:
{script}
"""
    response = OpenAI(api_key=api_key).responses.create(
        model=settings["openai_model"],
        input=prompt,
    )
    record_gpt_cost()
    return response.output_text.strip()
