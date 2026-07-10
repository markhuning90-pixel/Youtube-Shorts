from openai import OpenAI
from pathlib import Path


def load_api_key():
    env_file = Path(".env")

    if not env_file.exists():
        return None

    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENAI_API_KEY="):
            return line.split("=", 1)[1].strip()

    return None


api_key = load_api_key()

if not api_key:
    print("Kein API-Key gefunden.")
    raise SystemExit

client = OpenAI(api_key=api_key)

response = client.responses.create(
    model="gpt-5-mini",
    input="Antworte nur mit: Hallo!"
)

print(response.output_text)
