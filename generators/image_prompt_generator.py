import json
import time
from pathlib import Path

from openai import APIConnectionError, APITimeoutError, OpenAI

from config import load_api_key


def load_scene_image_prompts(scenes_file):
    try:
        scenes = json.loads(scenes_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("Die Datei scenes.json enthält kein gültiges JSON.")
        return None

    if not isinstance(scenes, list):
        print("Die Datei scenes.json enthält keine Szenenliste.")
        return None

    try:
        image_prompts = [str(scene["image_prompt"]).strip() for scene in scenes]
    except (KeyError, TypeError):
        print("Die Datei scenes.json enthält ungültige Szenendaten.")
        return None

    if not image_prompts or any(not image_prompt for image_prompt in image_prompts):
        print("Die Datei scenes.json enthält keine gültigen Bildprompts.")
        return None

    return image_prompts


def extract_image_prompt(response_text):
    if "IMAGE PROMPT:" in response_text:
        return response_text.split("IMAGE PROMPT:", 1)[1].strip()

    return response_text.strip()


def create_image_prompt(client, model, input_text, scene_number):
    for attempt in range(1, 4):
        try:
            return client.responses.create(model=model, input=input_text)
        except (APIConnectionError, APITimeoutError):
            if attempt == 3:
                print(
                    f"Bildprompt {scene_number} konnte nach 3 Versuchen nicht erstellt werden."
                )
                return None

            next_attempt = attempt + 1
            print(
                f"Verbindungsfehler bei Bildprompt {scene_number}. "
                f"Neuer Versuch {next_attempt} von 3."
            )
            time.sleep(attempt * 2)


def generate_image_prompts(generation):
    if not generation.output_folder:
        print("Kein Output-Ordner für die Generierung gefunden.")
        return None

    output_folder = Path(generation.output_folder)
    scenes_file = output_folder / "scenes.json"
    character_file = output_folder / "character.txt"
    prompt_file = Path("prompts/image_prompt.txt")

    if not scenes_file.exists():
        print("Die Datei scenes.json wurde nicht gefunden.")
        return None

    if not character_file.exists():
        print("Die Datei character.txt wurde nicht gefunden.")
        return None

    if not prompt_file.exists():
        print("Die Prompt-Datei prompts/image_prompt.txt wurde nicht gefunden.")
        return None

    api_key = load_api_key()

    if not api_key:
        raise RuntimeError("Kein API-Key gefunden.")

    scenes = load_scene_image_prompts(scenes_file)

    if scenes is None:
        return None

    prompt_template = prompt_file.read_text(encoding="utf-8")
    character = character_file.read_text(encoding="utf-8").strip()
    client = OpenAI(api_key=api_key)
    image_prompts = []

    for number, scene_prompt in enumerate(scenes, start=1):
        input_text = prompt_template.format(
            scene=(
                "Use exactly the same main character in every image.\n\n"
                f"CHARACTER:\n{character}\n\n"
                f"SCENE:\n{scene_prompt}"
            )
        )
        response = create_image_prompt(
            client,
            "gpt-5",
            input_text,
            number,
        )

        if response is None:
            return None

        image_prompts.append(
            f"PROMPT {number}:\n{extract_image_prompt(response.output_text)}"
        )

    output_file = output_folder / "image_prompts.txt"
    output_file.write_text("\n\n".join(image_prompts) + "\n", encoding="utf-8")

    return output_file
