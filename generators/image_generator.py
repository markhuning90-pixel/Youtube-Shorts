import base64
import re
from pathlib import Path

from openai import OpenAI

from config import load_api_key


def get_scenes(scenes_text):
    return [
        scene.strip()
        for scene in re.findall(
            r"^SCENE\s+\d+:\s*(.*?)(?=^SCENE\s+\d+:|\Z)",
            scenes_text,
            flags=re.MULTILINE | re.DOTALL,
        )
        if scene.strip()
    ]


def generate_images(generation):
    if not generation.output_folder:
        print("Kein Output-Ordner für die Generierung gefunden.")
        return None

    output_folder = Path(generation.output_folder)
    scenes_file = output_folder / "scenes.txt"

    if not scenes_file.exists():
        print("Die Datei scenes.txt wurde nicht gefunden.")
        return None

    api_key = load_api_key()

    if not api_key:
        raise RuntimeError("Kein API-Key gefunden.")

    images_folder = output_folder / "images"
    images_folder.mkdir(exist_ok=True)

    client = OpenAI(api_key=api_key)
    scenes = get_scenes(scenes_file.read_text(encoding="utf-8"))

    for number, scene in enumerate(scenes, start=1):
        response = client.images.generate(
            model="gpt-image-1",
            prompt=scene,
            size="1024x1024",
        )
        image_file = images_folder / f"scene_{number:02d}.png"
        image_file.write_bytes(base64.b64decode(response.data[0].b64_json))

    return images_folder
