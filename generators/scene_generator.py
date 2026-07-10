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

    return QUALITY_LIMITS.get(
        settings.get("quality_mode"),
        QUALITY_LIMITS["normal"],
    )


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
    prompt += (
        f"\n\nWichtig: Erstelle maximal {max_scenes} Szenen. Behalte alle wichtigen "
        "Informationen bei und beschreibe jede Szene inhaltlich ausreichend ausführlich."
    )

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
    )

    output_file = Path(generation.output_folder) / "scenes.txt"
    output_file.write_text(response.output_text, encoding="utf-8")

    return output_file
