from pathlib import Path

from openai import OpenAI


def load_api_key():
    env_file = Path(".env")

    if not env_file.exists():
        return None

    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENAI_API_KEY="):
            return line.split("=", 1)[1].strip()

    return None


def generate_script(topic):
    api_key = load_api_key()

    if not api_key:
        raise RuntimeError("Kein API-Key gefunden.")

    prompt = f"""Schreibe ein spannendes YouTube-Shorts-Skript (maximal 120 Wörter) zum Thema:
{topic}

Regeln:
- Starte mit einem starken Hook.
- Kurze Sätze.
- Einfach verständlich.
- Kein Emoji.
- Nur den fertigen Sprechertext ausgeben."""

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
    )

    return response.output_text
