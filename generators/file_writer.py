import json
import re
from datetime import datetime
from pathlib import Path


def create_generation_folder_name(timestamp, title):
    replacements = str.maketrans(
        {
            "ä": "ae",
            "ö": "oe",
            "ü": "ue",
            "ß": "ss",
        }
    )
    title_part = str(title or "").lower().translate(replacements).replace(" ", "-")
    title_part = re.sub(r"[^a-z0-9-]", "", title_part)
    title_part = re.sub(r"-{2,}", "-", title_part).strip("-")
    title_part = title_part[:60].rstrip("-")

    return f"{timestamp}_{title_part}" if title_part else timestamp


def save_script(generation):
    output_folder = Path("output")
    output_folder.mkdir(exist_ok=True)

    created_at = datetime.now()
    folder_name = create_generation_folder_name(
        created_at.strftime("%Y%m%d_%H%M%S"),
        generation.title,
    )
    generation_folder = output_folder / folder_name
    suffix = 2

    while generation_folder.exists():
        generation_folder = output_folder / f"{folder_name}_{suffix}"
        suffix += 1

    generation_folder.mkdir()
    generation.output_folder = str(generation_folder)

    output_file = generation_folder / "script.txt"
    output_file.write_text(
        f"Thema:\n{generation.topic}\n\nScript:\n{generation.script}",
        encoding="utf-8",
    )

    generation.status = "generated"
    metadata = {
        "topic": generation.topic,
        "title": generation.title,
        "description": generation.description,
        "hashtags": generation.hashtags,
        "script": generation.script,
        "created_at": created_at.isoformat(),
        "status": generation.status,
    }
    metadata_file = generation_folder / "metadata.json"
    metadata_file.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return output_file


def update_saved_generation(generation):
    """Aktualisiert Script und Metadaten nach einer automatischen Verbesserung."""
    if not generation.output_folder:
        return False

    generation_folder = Path(generation.output_folder)
    metadata_file = generation_folder / "metadata.json"

    if not metadata_file.exists():
        return False

    (generation_folder / "script.txt").write_text(
        f"Thema:\n{generation.topic}\n\nScript:\n{generation.script}",
        encoding="utf-8",
    )
    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    metadata.update(
        {
            "topic": generation.topic,
            "title": generation.title,
            "description": generation.description,
            "hashtags": generation.hashtags,
            "script": generation.script,
            "status": generation.status,
        }
    )
    metadata_file.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return True
