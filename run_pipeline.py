import json
from pathlib import Path

from approve import approve_script
from console import show_generation
from generators.content_generator import generate_content, validate_content
from generators.file_writer import save_script
from generators.image_generator import generate_images
from generators.scene_generator import generate_scenes
from generators.status_manager import update_status
from generators.subtitle_generator import generate_subtitles
from generators.topic_picker import get_all_topics
from generators.video_generator import generate_video
from generators.voice_generator import generate_voice
from models.generation import Generation


def is_test_mode():
    settings_file = Path("config/settings.json")

    if not settings_file.exists():
        return False

    try:
        return json.loads(settings_file.read_text(encoding="utf-8")).get(
            "test_mode",
            False,
        ) is True
    except json.JSONDecodeError:
        return False


def run_test_mode():
    print("Testmodus aktiviert. Nutze resume_pipeline.py zum Neu-Rendern vorhandener Videos.")


def continue_approved_generation(generation):
    output_folder = Path(generation.output_folder)
    metadata_file = output_folder / "metadata.json"

    voice_file = generate_voice(generation)
    if voice_file is None:
        return
    update_status(metadata_file, "voice_created")

    subtitle_file = generate_subtitles(generation)
    if subtitle_file is None:
        return
    update_status(metadata_file, "subtitles_created")

    scene_file = generate_scenes(generation)
    if scene_file is None:
        return
    update_status(metadata_file, "scenes_created")

    images_folder = generate_images(generation)
    if images_folder is None:
        return
    update_status(metadata_file, "images_created")

    video_file = generate_video(generation)
    if video_file is None:
        return

    update_status(metadata_file, "video_created")
    generation.status = "video_created"
    show_generation(generation)
    print("Video erstellt. Nutze review_videos.py und upload_ready.py.")
    print(video_file.resolve())


def run():
    if is_test_mode():
        run_test_mode()
        return

    topics = get_all_topics()

    if not topics:
        print("Keine Themen gefunden.")
        return

    for topic in topics:
        content = generate_content(topic)

        if not validate_content(content):
            continue

        generation = Generation(
            topic=topic,
            title=content["title"],
            description=content["description"],
            hashtags=content["hashtags"],
            script=content["script"],
            status="script_created",
        )
        saved_file = save_script(generation)
        show_generation(generation)
        print("Script erfolgreich gespeichert.")
        print(saved_file.resolve())

        source_folder = saved_file.parent
        approved_folder = Path("approval") / source_folder.name
        approve_script(saved_file)

        if not approved_folder.exists():
            print("Skript wurde nicht freigegeben. Keine weiteren Schritte werden ausgeführt.")
            continue

        generation.output_folder = str(approved_folder)
        generation.status = "script_approved"
        continue_approved_generation(generation)
