import json
from pathlib import Path


def update_status(metadata_file, new_status):
    metadata_path = Path(metadata_file)

    if not metadata_path.exists():
        print("Die metadata.json-Datei wurde nicht gefunden.")
        return None

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["status"] = new_status
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return new_status
