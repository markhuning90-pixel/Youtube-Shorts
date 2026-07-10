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


def extract_image_prompt(response_text):
    if "IMAGE PROMPT:" in response_text:
        return response_text.split("IMAGE PROMPT:", 1)[1].strip()

    return response_text.strip()


def generate_image_prompts(generation):
    if not generation.output_folder:
        print("Kein Output-Ordner für die Generierung gefunden.")
        return None

    output_folder = Path(generation.output_folder)
    scenes_file = output_folder / "scenes.txt"
    prompt_file = Path("prompts/image_prompt.txt")

    if not scenes_file.exists():
        print("Die Datei scenes.txt wurde nicht gefunden.")
        return None

    if not prompt_file.exists():
        print("Die Prompt-Datei prompts/image_prompt.txt wurde nicht gefunden.")
        return None

    api_key = load_api_key()

    if not api_key:
        raise RuntimeError("Kein API-Key gefunden.")

    scenes = get_scenes(scenes_file.read_text(encoding="utf-8"))

    if not scenes:
        print("In scenes.txt wurden keine Szenen gefunden.")
        return None

    prompt_template = prompt_file.read_text(encoding="utf-8")
    client = OpenAI(api_key=api_key)
    image_prompts = []

    for number, scene in enumerate(scenes, start=1):
        response = client.responses.create(
            model="gpt-5",
            input=prompt_template.format(scene=scene),
        )
        image_prompts.append(
            f"PROMPT {number}:\n{extract_image_prompt(response.output_text)}"
        )

    output_file = output_folder / "image_prompts.txt"
    output_file.write_text("\n\n".join(image_prompts) + "\n", encoding="utf-8")

    return output_file
