from pathlib import Path


def load_topics(file_path="topics.txt"):
    topics_file = Path(file_path)

    if not topics_file.exists():
        return []

    return [
        line.strip()
        for line in topics_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
