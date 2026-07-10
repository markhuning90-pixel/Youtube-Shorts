import base64
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from openai import OpenAI

from config import load_api_key


QUALITY_LIMITS = {
    "low": 4,
    "normal": 5,
    "high": 8,
}


def get_max_images():
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


def generate_single_image(client, image_prompt, image_file):
    response = client.images.generate(
        model="gpt-image-1",
        prompt=image_prompt,
        size="1024x1536",
    )
    image_file.write_bytes(base64.b64decode(response.data[0].b64_json))

    return image_file


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
    image_prompts = get_image_prompts(
        prompts_file.read_text(encoding="utf-8")
    )[:get_max_images()]

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(
                generate_single_image,
                client,
                image_prompt,
                images_folder / f"scene_{number:02d}.png",
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

    if failed:
        return None

    return images_folder
