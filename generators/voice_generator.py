import json
from pathlib import Path

from openai import BadRequestError, OpenAI

from config import load_api_key
from utils.cost_tracker import record_voice_cost


def load_voice_settings():
    settings_file = Path("config/settings.json")

    if not settings_file.exists():
        print("Die Datei config/settings.json wurde nicht gefunden.")
        return None

    try:
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("Die Datei config/settings.json enthält kein gültiges JSON.")
        return None

    required_settings = ("voice_model", "voice_name", "voice_instructions")

    if any(not str(settings.get(setting, "")).strip() for setting in required_settings):
        print("Die Voice-Konfiguration ist unvollständig.")
        return None

    return {
        setting: str(settings[setting]).strip()
        for setting in required_settings
    }


def generate_voice(generation):
    if not generation.output_folder:
        print("Kein Output-Ordner für die Generierung gefunden.")
        return None

    voice_settings = load_voice_settings()

    if voice_settings is None:
        return None

    api_key = load_api_key()

    if not api_key:
        raise RuntimeError("Kein API-Key gefunden.")

    output_file = Path(generation.output_folder) / "voice.mp3"
    client = OpenAI(api_key=api_key)

    try:
        with client.audio.speech.with_streaming_response.create(
            model=voice_settings["voice_model"],
            voice=voice_settings["voice_name"],
            input=generation.script,
            instructions=voice_settings["voice_instructions"],
        ) as response:
            response.stream_to_file(output_file)
    except BadRequestError as error:
        print(
            "Die Spracherzeugung wurde abgelehnt. Das gewählte Modell unterstützt "
            f"möglicherweise keine instructions: {error}"
        )
        return None

    record_voice_cost(generation.output_folder, generation.script)

    return output_file
