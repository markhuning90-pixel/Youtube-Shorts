from pathlib import Path


ENV_FILE = Path(".env")


def has_env_file():
    return ENV_FILE.exists()
