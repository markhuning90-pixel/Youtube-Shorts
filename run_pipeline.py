import json
from pathlib import Path
from time import perf_counter

from approve import approve_script
from console import show_generation
from generators.content_generator import generate_content, validate_content
from generators.file_writer import save_script
from generators.image_generator import generate_images
from generators.scene_generator import generate_scenes
from generators.status_manager import update_status
from generators.stock_media_generator import generate_stock_media
from generators.subtitle_generator import generate_subtitles
from generators.topic_picker import get_all_topics
from generators.topic_loader import remove_topic, save_used_topic
from generators.video_generator import generate_video
from generators.voice_generator import generate_voice
from models.generation import Generation
from utils.progress import finish_step, run_with_progress, start_step


TOTAL_STEPS = 8


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


def generate_valid_content(topic):
    content = generate_content(topic)

    if not validate_content(content):
        return None

    return content


def run_step(step_number, message, function, *args):
    try:
        return run_with_progress(
            step_number,
            TOTAL_STEPS,
            message,
            function,
            *args,
        )
    except Exception:
        return None


def generate_scene_media(generation, metadata_file):
    scene_file = generate_scenes(generation)
    if scene_file is None:
        return None
    update_status(metadata_file, "scenes_created")

    stock_folder = generate_stock_media(generation)
    if stock_folder is None:
        return None
    update_status(metadata_file, "stock_media_created")
    print("Stock-Medien erstellt.", flush=True)

    images_folder = generate_images(generation)
    if images_folder is None:
        return None
    update_status(metadata_file, "images_created")
    print("Bilder erstellt.", flush=True)
    return images_folder


def continue_approved_generation(generation):
    metadata_file = Path(generation.output_folder) / "metadata.json"

    voice_file = run_step(
        4,
        "Stimme wird erzeugt",
        generate_voice,
        generation,
    )
    if voice_file is None:
        return False
    update_status(metadata_file, "voice_created")

    subtitle_file = run_step(
        5,
        "Untertitel werden erstellt",
        generate_subtitles,
        generation,
    )
    if subtitle_file is None:
        return False
    update_status(metadata_file, "subtitles_created")

    images_folder = run_step(
        6,
        "Szenen und Medien werden erstellt",
        generate_scene_media,
        generation,
        metadata_file,
    )
    if images_folder is None:
        return False

    video_file = run_step(
        7,
        "Video wird gerendert",
        generate_video,
        generation,
    )
    if video_file is None:
        return False

    update_status(metadata_file, "video_created")
    generation.status = "video_created"
    show_generation(generation)
    compatibility_file = Path(generation.output_folder) / "final_video.mp4"
    print("Video erstellt.")
    print("\nBenanntes Video:")
    print(video_file.resolve())

    if compatibility_file.exists() and compatibility_file != video_file:
        print("\nKompatibilitätsdatei:")
        print(compatibility_file.resolve())

    print("\nNutze review_videos.py und upload_ready.py.")

    if remove_topic(generation.topic):
        save_used_topic(generation.topic)
        print("Thema aus topics.txt entfernt.")
        print("Thema in used_topics.txt gespeichert.")

    return True


def run():
    if is_test_mode():
        run_test_mode()
        return

    pipeline_start = perf_counter()
    topics = run_step(
        1,
        "Thema wird geladen",
        get_all_topics,
    )

    if not topics:
        print("Pipeline beendet. Keine weiteren Kosten entstanden.")
        return

    for topic in topics:
        content = run_step(
            2,
            "Skript wird erstellt",
            generate_valid_content,
            topic,
        )
        if content is None:
            print("Pipeline beendet. Keine weiteren Kosten entstanden.")
            return

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

        approval_start = start_step(3, TOTAL_STEPS, "Skript wird freigegeben")
        source_folder = saved_file.parent
        approved_folder = Path("approval") / source_folder.name
        approve_script(saved_file)

        if not approved_folder.exists():
            print("[3/8] FEHLER: Skript wurde nicht freigegeben.", flush=True)
            print("Pipeline beendet. Keine weiteren Kosten entstanden.")
            return

        finish_step(3, TOTAL_STEPS, approval_start)
        generation.output_folder = str(approved_folder)
        generation.status = "script_approved"

        if not continue_approved_generation(generation):
            print("Pipeline beendet. Keine weiteren Kosten entstanden.")
            return

        completion_start = start_step(8, TOTAL_STEPS, "Video fertig")
        finish_step(8, TOTAL_STEPS, completion_start)
        total_duration = perf_counter() - pipeline_start
        print(f"Gesamtzeit: {total_duration:.1f} Sekunden", flush=True)
