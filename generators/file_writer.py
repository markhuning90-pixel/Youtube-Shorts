import json
from datetime import datetime
from pathlib import Path


def save_script(topic, script, title=None, description=None, hashtags=None):
    output_folder = Path("output")
    output_folder.mkdir(exist_ok=True)

    created_at = datetime.now()
    folder_name = created_at.strftime("%Y%m%d_%H%M%S")
    generation_folder = output_folder / folder_name
    generation_folder.mkdir(exist_ok=True)

    output_file = generation_folder / "script.txt"
    output_file.write_text(
        f"Thema:\n{topic}\n\nScript:\n{script}",
        encoding="utf-8",
    )

    metadata = {
        "topic": topic,
        "title": title,
        "description": description,
        "hashtags": hashtags,
        "script": script,
        "created_at": created_at.isoformat(),
        "status": "pending",
    }
    metadata_file = generation_folder / "metadata.json"
    metadata_file.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return output_file
