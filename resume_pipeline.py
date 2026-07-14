import json
from pathlib import Path

from generators.image_generator import generate_images
from generators.scene_generator import generate_scenes
from generators.stock_media_generator import generate_stock_media
from generators.subtitle_generator import generate_subtitles
from generators.video_generator import generate_video
from generators.voice_generator import generate_voice
from models.generation import Generation


def find_generations():
    generation_folders = []

    for folder_name in ("approval", "output", "completed", "rejected"):
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

    if not isinstance(metadata, dict):
        print("Die metadata.json enthält keine gültigen Daten.")
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


def run_step(label, function, generation):
    try:
        result = function(generation)
    except Exception as error:
        print(f"{label} konnten nicht erstellt werden: {error}")
        return None

    if result is None:
        print(f"{label} konnten nicht erstellt werden.")
        return None

    print(f"{label} erstellt.")
    print(result.resolve())
    return result


def load_scene_numbers(scenes_file, media_type):
    try:
        scenes = json.loads(scenes_file.read_text(encoding="utf-8"))
        return [
            int(scene["scene_number"])
            for scene in scenes
            if scene["media_type"] == media_type
        ]
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def has_required_media(scenes_file, media_folder, media_type, extension):
    scene_numbers = load_scene_numbers(scenes_file, media_type)

    if scene_numbers is None:
        return False

    return all(
        (media_folder / f"scene_{scene_number:02d}{extension}").exists()
        for scene_number in scene_numbers
    )


def resume_generation(generation):
    output_folder = Path(generation.output_folder)
    voice_file = output_folder / "voice.mp3"
    subtitles_file = output_folder / "subtitles.ass"
    scenes_file = output_folder / "scenes.json"
    stock_folder = output_folder / "stock"
    images_folder = output_folder / "images"
    video_file = output_folder / "final_video.mp4"

    if voice_file.exists():
        print(f"Bereits vorhanden, wird übersprungen:\n{voice_file.resolve()}")
    elif run_step("Sprachdatei", generate_voice, generation) is None:
        return

    if subtitles_file.exists():
        print(f"Bereits vorhanden, wird übersprungen:\n{subtitles_file.resolve()}")
    elif run_step("Untertitel", generate_subtitles, generation) is None:
        return

    if scenes_file.exists():
        print(f"Bereits vorhanden, wird übersprungen:\n{scenes_file.resolve()}")
    elif run_step("Szenenplan", generate_scenes, generation) is None:
        return

    if has_required_media(scenes_file, stock_folder, "stock", ".mp4"):
        print(f"Bereits vorhanden, wird übersprungen:\n{stock_folder.resolve()}")
    elif run_step("Stock-Medien", generate_stock_media, generation) is None:
        return

    if has_required_media(scenes_file, images_folder, "ai_image", ".png"):
        print(f"Bereits vorhanden, wird übersprungen:\n{images_folder.resolve()}")
    elif run_step("Bilder", generate_images, generation) is None:
        return

    if video_file.exists():
        print(f"Bereits vorhanden, wird übersprungen:\n{video_file.resolve()}")
    elif run_step("Video", generate_video, generation) is None:
        return

    print("Generierung vollständig.")
    print("Video:")
    print(video_file.resolve())


def main():
    generation_folders = find_generations()

    if not generation_folders:
        print("Keine Generierungen mit metadata.json gefunden.")
        return

    for number, generation_folder in enumerate(generation_folders, start=1):
        print(f"{number}. {generation_folder}")

    generation_folder = select_generation(generation_folders)
    generation = load_generation(generation_folder)

    if generation is not None:
        resume_generation(generation)


if __name__ == "__main__":
    main()
