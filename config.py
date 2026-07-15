from pathlib import Path


ENV_FILE = Path(".env")


def has_env_file():
    return ENV_FILE.exists()


def load_api_key():
    if not ENV_FILE.exists():
        return None

    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENAI_API_KEY="):
            return line.split("=", 1)[1].strip()

    return None


def load_pexels_api_key():
    if not ENV_FILE.exists():
        return None

    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("PEXELS_API_KEY="):
            return line.split("=", 1)[1].strip()

    return None


def load_pixabay_api_key():
    if not ENV_FILE.exists():
        return None

    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        if line.startswith("PIXABAY_API_KEY="):
            return line.split("=", 1)[1].strip()

    return None
