import base64
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI

from config import load_api_key
from utils.cost_tracker import record_image_cost


QUALITY_LIMITS = {
    "low": 4,
    "normal": 5,
    "high": 8,
}


def load_image_settings():
    default_settings = {
        "image_model": "gpt-image-1",
        "image_size": "1024x1536",
        "use_stock_media": False,
    }
    settings_file = Path("config/settings.json")

    if not settings_file.exists():
        return default_settings

    try:
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default_settings

    image_model = settings.get("image_model")
    image_size = settings.get("image_size")

    if not isinstance(image_model, str) or not image_model.strip():
        image_model = default_settings["image_model"]

    if not isinstance(image_size, str) or not image_size.strip():
        image_size = default_settings["image_size"]

    return {
        "image_model": image_model,
        "image_size": image_size,
        "use_stock_media": settings.get("use_stock_media") is True,
    }


def get_max_images():
    settings_file = Path("config/settings.json")

    if not settings_file.exists():
        return QUALITY_LIMITS["normal"]

    try:
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return QUALITY_LIMITS["normal"]

    configured_limit = settings.get("max_ai_images")

    if isinstance(configured_limit, int) and configured_limit >= 0:
        return configured_limit

    return QUALITY_LIMITS.get(settings.get("quality_mode"), QUALITY_LIMITS["normal"])


def load_scene_image_prompts(scenes_file, use_stock_media):
    try:
        scenes = json.loads(scenes_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("Die Datei scenes.json enthält kein gültiges JSON.")
        return None

    if not isinstance(scenes, list):
        print("Die Datei scenes.json enthält keine Szenenliste.")
        return None

    try:
        if use_stock_media:
            image_prompts = [
                str(scene["image_prompt"]).strip()
                for scene in scenes
                if scene["media_type"] == "ai_image"
            ]
        else:
            image_prompts = [
                str(scene["image_prompt"]).strip()
                for scene in scenes
            ]
    except (KeyError, TypeError):
        print("Die Datei scenes.json enthält ungültige Szenendaten.")
        return None

    if any(not image_prompt for image_prompt in image_prompts):
        print("Die Datei scenes.json enthält ungültige KI-Bildprompts.")
        return None

    return image_prompts


def generate_single_image(client, image_prompt, image_file, image_model, image_size):
    response = client.images.generate(
        model=image_model,
        prompt=image_prompt,
        size=image_size,
    )
    image_file.write_bytes(base64.b64decode(response.data[0].b64_json))

    return image_file


def generate_images(generation):
    if not generation.output_folder:
        print("Kein Output-Ordner für die Generierung gefunden.")
        return None

    output_folder = Path(generation.output_folder)
    scenes_file = output_folder / "scenes.json"

    if not scenes_file.exists():
        print("Die Datei scenes.json wurde nicht gefunden.")
        return None

    image_settings = load_image_settings()
    scene_image_prompts = load_scene_image_prompts(
        scenes_file,
        image_settings["use_stock_media"],
    )

    if scene_image_prompts is None:
        return None

    image_prompts = scene_image_prompts[:get_max_images()]

    images_folder = output_folder / "images"
    images_folder.mkdir(exist_ok=True)

    if not image_prompts:
        print("Keine KI-Bildszenen gefunden.")
        return images_folder

    api_key = load_api_key()

    if not api_key:
        raise RuntimeError("Kein API-Key gefunden.")

    client = OpenAI(api_key=api_key)

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(
                generate_single_image,
                client,
                image_prompt,
                images_folder / f"scene_{number:02d}.png",
                image_settings["image_model"],
                image_settings["image_size"],
            ): number
            for number, image_prompt in enumerate(image_prompts, start=1)
        }

        failed = False

        for future in as_completed(futures):
            number = futures[future]

            try:
                future.result()
            except Exception as error:
                print(f"Bild {number} konnte nicht erstellt werden: {error}")
                failed = True

    record_image_cost(output_folder, len(image_prompts))

    if failed:
        return None

    return images_folder
