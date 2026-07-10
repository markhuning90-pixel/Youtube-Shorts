from pathlib import Path

from openai import OpenAI

from config import load_api_key


def validate_content(content):
    if content is None or not all(
        content.get(key) for key in ("title", "description", "hashtags", "script")
    ):
        print("Ungültige AI-Antwort.")
        return False

    return True


def parse_content(content):
    sections = {
        "title": [],
        "description": [],
        "hashtags": [],
        "script": [],
    }
    current_section = None

    for line in content.splitlines():
        section_name = line.rstrip(":").lower()

        if section_name in sections and line.endswith(":"):
            current_section = section_name
        elif current_section is not None:
            sections[current_section].append(line)

    return {
        name: "\n".join(lines).strip()
        for name, lines in sections.items()
    }


def generate_content(topic):
    prompt_file = Path("prompts/content_prompt.txt")

    if not prompt_file.exists():
        print("Die Prompt-Datei prompts/content_prompt.txt wurde nicht gefunden.")
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

    return parse_content(response.output_text)
