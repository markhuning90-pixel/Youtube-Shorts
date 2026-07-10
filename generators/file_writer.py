import json
from datetime import datetime
from pathlib import Path


def save_script(generation):
    output_folder = Path("output")
    output_folder.mkdir(exist_ok=True)

    created_at = datetime.now()
    folder_name = created_at.strftime("%Y%m%d_%H%M%S")
    generation_folder = output_folder / folder_name
    generation_folder.mkdir(exist_ok=True)
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
