import json
from pathlib import Path

from generators.image_generator import generate_images
from generators.image_prompt_generator import generate_image_prompts
from generators.scene_generator import generate_scenes
from generators.subtitle_generator import generate_subtitles
from generators.video_generator import generate_video
from generators.voice_generator import generate_voice
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
        print(f"{label} konnte nicht erstellt werden: {error}")
        return None

    if result is None:
        print(f"{label} konnte nicht erstellt werden.")
        return None

    print(f"{label} erstellt.")
    print(result.resolve())
    return result


def resume_generation(generation):
    output_folder = Path(generation.output_folder)
    voice_file = output_folder / "voice.mp3"
    subtitles_file = output_folder / "subtitles.ass"
    scenes_file = output_folder / "scenes.txt"
    image_prompts_file = output_folder / "image_prompts.txt"
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

    if image_prompts_file.exists():
        print(f"Bereits vorhanden, wird übersprungen:\n{image_prompts_file.resolve()}")
    elif run_step("Bildprompts", generate_image_prompts, generation) is None:
        return

    if images_folder.exists() and any(images_folder.glob("*.png")):
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
