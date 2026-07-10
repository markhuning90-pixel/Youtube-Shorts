from pathlib import Path

from openai import OpenAI

from config import load_api_key


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

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
    )

    output_file = Path(generation.output_folder) / "scenes.txt"
    output_file.write_text(response.output_text, encoding="utf-8")

    return output_file
