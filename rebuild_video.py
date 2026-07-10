import json
from pathlib import Path

from generators.subtitle_generator import generate_subtitles
from generators.video_generator import generate_video
from models.generation import Generation


def find_generations():
    generation_folders = []

    for folder_name in ("output", "completed", "rejected"):
        base_folder = Path(folder_name)

        if base_folder.exists():
            generation_folders.extend(
                metadata_file.parent for metadata_file in base_folder.rglob("metadata.json")
            )

    return sorted(generation_folders)


def select_generation(generation_folders):
    while True:
        choice = input("Nummer der Generierung auswählen: ").strip()

        try:
            number = int(choice)
        except ValueError:
            print("Bitte eine gültige Nummer eingeben.")
            continue

        if 1 <= number <= len(generation_folders):
            return generation_folders[number - 1]

        print("Die ausgewählte Nummer ist nicht vorhanden.")


def load_generation(generation_folder):
    metadata_file = generation_folder / "metadata.json"

    try:
        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        print("Die metadata.json konnte nicht gelesen werden.")
        return None

    generation = Generation(
        topic=metadata.get("topic", ""),
        title=metadata.get("title", ""),
        description=metadata.get("description", ""),
        hashtags=metadata.get("hashtags", ""),
        script=metadata.get("script", ""),
        status=metadata.get("status", ""),
    )
    generation.output_folder = str(generation_folder)

    return generation


def main():
    generation_folders = find_generations()

    if not generation_folders:
        print("Keine Generierungen mit metadata.json gefunden.")
        return

    for number, generation_folder in enumerate(generation_folders, start=1):
        print(f"{number}. {generation_folder}")

    generation_folder = select_generation(generation_folders)
    generation = load_generation(generation_folder)

    if generation is None:
        return

    subtitle_file = generate_subtitles(generation)

    if subtitle_file is None:
        return

    print("Untertitel neu erstellt.")

    video_file = generate_video(generation)

    if video_file is None:
        return

    print("Video neu erstellt.")
    print("Gespeichert unter:")
    print(video_file.resolve())


if __name__ == "__main__":
    main()
