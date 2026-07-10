import base64
import re
from pathlib import Path

from openai import OpenAI

from config import load_api_key


def get_image_prompts(prompts_text):
    return [
        prompt.strip()
        for prompt in re.findall(
            r"^PROMPT\s+\d+:\s*(.*?)(?=^PROMPT\s+\d+:|\Z)",
            prompts_text,
            flags=re.MULTILINE | re.DOTALL,
        )
        if prompt.strip()
    ]


def generate_images(generation):
    if not generation.output_folder:
        print("Kein Output-Ordner für die Generierung gefunden.")
        return None

    output_folder = Path(generation.output_folder)
    prompts_file = output_folder / "image_prompts.txt"

    if not prompts_file.exists():
        print("Die Datei image_prompts.txt wurde nicht gefunden.")
        return None

    api_key = load_api_key()

    if not api_key:
        raise RuntimeError("Kein API-Key gefunden.")

    images_folder = output_folder / "images"
    images_folder.mkdir(exist_ok=True)

    client = OpenAI(api_key=api_key)
    image_prompts = get_image_prompts(prompts_file.read_text(encoding="utf-8"))

    for number, image_prompt in enumerate(image_prompts, start=1):
        response = client.images.generate(
            model="gpt-image-1",
            prompt=image_prompt,
            size="1024x1024",
        )
        image_file = images_folder / f"scene_{number:02d}.png"
        image_file.write_bytes(base64.b64decode(response.data[0].b64_json))

    return images_folder
