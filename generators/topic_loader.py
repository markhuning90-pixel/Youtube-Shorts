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


def remove_topic(topic, file_path="topics.txt"):
    topics_file = Path(file_path)

    if not topics_file.exists():
        return False

    lines = topics_file.read_text(encoding="utf-8").splitlines()
    removed = False
    remaining_lines = []

    for line in lines:
        if not removed and line.strip() == topic:
            removed = True
            continue

        if line.strip():
            remaining_lines.append(line)

    if removed:
        content = "\n".join(remaining_lines)
        topics_file.write_text(
            f"{content}\n" if content else "",
            encoding="utf-8",
        )

    return removed


def save_used_topic(topic, file_path="used_topics.txt"):
    used_topics_file = Path(file_path)

    if used_topics_file.exists():
        existing_topics = {
            line.strip()
            for line in used_topics_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
        if topic in existing_topics:
            return False

    with used_topics_file.open("a", encoding="utf-8") as file:
        file.write(f"{topic}\n")

    return True
