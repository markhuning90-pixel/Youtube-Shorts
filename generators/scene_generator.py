import json
from pathlib import Path

from openai import OpenAI

from config import load_api_key
from utils.cost_tracker import record_gpt_cost


def load_scene_settings():
    defaults = {
        "target_scene_count_min": 8,
        "target_scene_count_max": 12,
        "openai_model": "gpt-5-mini",
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


def get_scene_count(audio_duration, settings):
    minimum = int(settings["target_scene_count_min"])
    maximum = int(settings["target_scene_count_max"])
    return max(minimum, min(maximum, round(audio_duration / 5)))


def parse_scenes(response_text, expected_count):
    try:
        scenes = json.loads(response_text)
    except json.JSONDecodeError:
        print("Die AI-Antwort enthält kein gültiges Szenen-JSON.")
        return None

    if not isinstance(scenes, list) or len(scenes) != expected_count:
        print(f"Die AI-Antwort enthält nicht genau {expected_count} Szenen.")
        return None

    parsed_scenes = []
    try:
        for number, scene in enumerate(scenes, start=1):
            spoken_text = str(scene["spoken_text"]).strip()
            query_de = str(scene["stock_search_query_de"]).strip()
            query_en = str(scene["stock_search_query_en"]).strip()

            if (
                not spoken_text
                or not query_de
                or not query_en
                or scene.get("media_type") != "stock_video"
            ):
                raise ValueError

            parsed_scenes.append(
                {
                    "scene_number": number,
                    "spoken_text": spoken_text,
                    "stock_search_query_de": query_de,
                    "stock_search_query_en": query_en,
                    "selected_provider": "",
                    "selected_video_path": "",
                    "media_type": "stock_video",
                }
            )
    except (KeyError, TypeError, ValueError):
        print("Die AI-Antwort enthält unvollständige Szenendaten.")
        return None

    return parsed_scenes


def assign_timings(scenes, audio_duration):
    weights = [max(1, len(scene["spoken_text"].split())) for scene in scenes]
    total_weight = sum(weights)
    current_time = 0.0

    for index, (scene, weight) in enumerate(zip(scenes, weights)):
        if index == len(scenes) - 1:
            end_time = audio_duration
        else:
            end_time = current_time + audio_duration * weight / total_weight

        scene["start_time"] = round(current_time, 3)
        scene["end_time"] = round(end_time, 3)
        scene["duration"] = round(end_time - current_time, 3)
        current_time = end_time

    return scenes


def generate_scenes(generation):
    if not generation.output_folder:
        print("Kein Output-Ordner für die Generierung gefunden.")
        return None

    if generation.audio_duration <= 0:
        print("Die echte Sprachlänge fehlt für den Szenenplan.")
        return None

    prompt_file = Path("prompts/scene_prompt.txt")
    if not prompt_file.exists():
        print("Die Prompt-Datei prompts/scene_prompt.txt wurde nicht gefunden.")
        return None

    api_key = load_api_key()
    if not api_key:
        raise RuntimeError("Kein API-Key gefunden.")

    settings = load_scene_settings()
    scene_count = get_scene_count(generation.audio_duration, settings)
    prompt = prompt_file.read_text(encoding="utf-8").format(script=generation.script)
    prompt += f"""

Erstelle genau {scene_count} Szenen für {generation.audio_duration:.3f} Sekunden Sprache.
Die ersten zwei Sekunden müssen den stärksten visuellen Moment enthalten. Teile das
gesprochene Skript sinnvoll auf; jede Szene zeigt einen neuen Sinnabschnitt.

Neue Videos verwenden ausschließlich echte Stockvideos. Jede Szene muss daher
"media_type": "stock_video" enthalten. Keine Bilder, keine KI-Bilder und keine
Bildprompts. Gib präzise, kurze Suchbegriffe auf Deutsch und Englisch an.

Format:
[
  {{
    "spoken_text": "Der gesprochene Abschnitt dieser Szene.",
    "stock_search_query_de": "deutscher Suchbegriff",
    "stock_search_query_en": "englischer Suchbegriff",
    "media_type": "stock_video"
  }}
]
"""

    response = OpenAI(api_key=api_key).responses.create(
        model=settings["openai_model"],
        input=prompt,
    )
    record_gpt_cost()
    scenes = parse_scenes(response.output_text, scene_count)

    if scenes is None:
        return None

    scenes = assign_timings(scenes, generation.audio_duration)
    output_file = Path(generation.output_folder) / "scenes.json"
    output_file.write_text(
        json.dumps(scenes, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"{len(scenes)} Stockvideo-Szenen geplant.")
    return output_file
