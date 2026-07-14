import json
from pathlib import Path

from openai import OpenAI

from config import load_api_key


QUALITY_LIMITS = {
    "low": 4,
    "normal": 5,
    "high": 8,
}


def get_max_scenes():
    settings_file = Path("config/settings.json")

    if not settings_file.exists():
        return QUALITY_LIMITS["normal"]

    try:
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return QUALITY_LIMITS["normal"]

    if settings.get("production_mode") == "low_cost_pro":
        return 5

    return QUALITY_LIMITS.get(settings.get("quality_mode"), QUALITY_LIMITS["normal"])


def parse_scenes(response_text):
    try:
        scene_data = json.loads(response_text)
    except json.JSONDecodeError:
        print("Die AI-Antwort enthält kein gültiges Szenen-JSON.")
        return None

    if not isinstance(scene_data, list):
        print("Die AI-Antwort enthält keine Szenenliste.")
        return None

    try:
        scenes = []

        for scene in scene_data:
            media_type = str(scene["media_type"]).strip()

            if media_type not in {"ai_image", "stock"}:
                raise ValueError

            scenes.append(
                {
                    "scene_number": int(scene["scene_number"]),
                    "text": str(scene["text"]).strip(),
                    "media_type": media_type,
                    "stock_keyword": str(scene["stock_keyword"]).strip(),
                    "image_prompt": str(scene["image_prompt"]).strip(),
                    "duration": int(scene["duration"]),
                }
            )
    except (KeyError, TypeError, ValueError):
        print("Die AI-Antwort enthält unvollständige Szenendaten.")
        return None

    if not 4 <= len(scenes) <= 5:
        print("Die AI-Antwort enthält nicht 4 bis 5 Szenen.")
        return None

    if sum(scene["media_type"] == "ai_image" for scene in scenes) > 2:
        print("Die AI-Antwort enthält zu viele KI-Bildszenen.")
        return None

    if any(
        not scene["text"]
        or not scene["stock_keyword"]
        or not scene["image_prompt"]
        or scene["duration"] <= 0
        for scene in scenes
    ):
        print("Die AI-Antwort enthält ungültige Szenendaten.")
        return None

    return scenes


def generate_scenes(generation):
    if not generation.output_folder:
        print("Kein Output-Ordner für die Generierung gefunden.")
        return None

    prompt_file = Path("prompts/scene_prompt.txt")

    if not prompt_file.exists():
        print("Die Prompt-Datei prompts/scene_prompt.txt wurde nicht gefunden.")
        return None

    api_key = load_api_key()

    if not api_key:
        raise RuntimeError("Kein API-Key gefunden.")

    prompt = prompt_file.read_text(encoding="utf-8").format(
        script=generation.script
    )
    max_scenes = get_max_scenes()
    prompt += f"""

Wichtig: Erstelle 4 bis 5 Szenen und höchstens {max_scenes} Szenen. Behalte alle
wichtigen Informationen bei und beschreibe jede Szene inhaltlich ausreichend.
Verwende höchstens 2 Szenen mit \"media_type\": \"ai_image\" für die wichtigsten
visuellen Momente. Alle übrigen Szenen müssen \"media_type\": \"stock\" verwenden.
Gib für jede Szene einen passenden englischen \"stock_keyword\" und einen englischen
\"image_prompt\" an.

Antworte ausschließlich mit gültigem JSON. Verwende keine Markdown-Codeblöcke und
keine Erklärungen außerhalb des JSON.

Das JSON muss eine Liste in diesem Format sein:
[
  {{
    \"scene_number\": 1,
    \"text\": \"Beschreibung dessen, was in der Szene zu sehen ist.\",
    \"media_type\": \"stock\",
    \"stock_keyword\": \"relevanter Suchbegriff für Stock-Medien\",
    \"image_prompt\": \"Detaillierter Bildprompt für diese Szene.\",
    \"duration\": 5
  }}
]
"""

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
    )
    scenes = parse_scenes(response.output_text)

    if scenes is None:
        return None

    output_file = Path(generation.output_folder) / "scenes.json"
    output_file.write_text(
        json.dumps(scenes, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return output_file
