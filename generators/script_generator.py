from pathlib import Path

from openai import OpenAI

from config import load_api_key


def generate_script(topic):
    prompt_file = Path("prompts/script_prompt.txt")

    if not prompt_file.exists():
        print("Die Prompt-Datei prompts/script_prompt.txt wurde nicht gefunden.")
        return None

    api_key = load_api_key()

    if not api_key:
        raise RuntimeError("Kein API-Key gefunden.")

    prompt = prompt_file.read_text(encoding="utf-8").format(topic=topic)

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
    )

    return response.output_text
