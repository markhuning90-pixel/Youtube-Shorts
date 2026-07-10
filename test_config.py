import os
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

if api_key:
    print("API-Key gefunden.")
else:
    print("Kein API-Key gefunden.")
