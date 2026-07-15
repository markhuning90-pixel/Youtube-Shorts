import json
import traceback
from datetime import datetime
from pathlib import Path
from shutil import move
from time import perf_counter

from console import show_generation
from generators.content_generator import extend_script, generate_content, validate_content
from generators.file_writer import save_script, update_saved_generation
from generators.scene_generator import generate_scenes
from generators.status_manager import update_status
from generators.stock_media_generator import generate_stock_media
from generators.subtitle_generator import generate_subtitles
from generators.topic_generator import ensure_topic_supply
from generators.topic_loader import remove_topic, save_used_topic
from generators.video_generator import generate_video, get_audio_duration
from generators.video_validator import validate_rendered_video
from generators.voice_generator import generate_voice
from models.generation import Generation
from utils.cost_tracker import print_cost_summary
from utils.progress import finish_step, run_with_progress, start_step


TOTAL_STEPS = 10


def load_settings():
    defaults = {
        "test_mode": False,
        "target_video_min_seconds": 43,
        "target_script_min_words": 115,
        "max_duration_retries": 2,
    }
    settings_file = Path("config/settings.json")

    if not settings_file.exists():
        return defaults

    try:
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("Die Datei config/settings.json enthält kein gültiges JSON.")
        return defaults

    return {key: settings.get(key, value) for key, value in defaults.items()}


def run_test_mode():
    print("Testmodus aktiviert. Nutze resume_pipeline.py zum Neu-Rendern vorhandener Videos.")


def count_words(text):
    return len(text.split())


def log_pipeline_error(topic, step, error, generation=None):
    log_folder = Path("logs")
    log_folder.mkdir(exist_ok=True)
    generation_folder = generation.output_folder if generation else "nicht erstellt"
    log_file = log_folder / "pipeline_errors.log"

    with log_file.open("a", encoding="utf-8") as file:
        file.write(
            f"[{datetime.now().isoformat(timespec='seconds')}]\n"
            f"Thema: {topic}\n"
            f"Schritt: {step}\n"
            f"Fehlertyp: {type(error).__name__}\n"
            f"Fehlermeldung: {error}\n"
            f"Generierungsordner: {generation_folder}\n"
            f"Stacktrace:\n{traceback.format_exc()}\n"
        )


def run_step(step_number, message, function, *args):
    try:
        return run_with_progress(step_number, TOTAL_STEPS, message, function, *args)
    except Exception as error:
        raise RuntimeError(f"{message} fehlgeschlagen: {error}") from error


def require_step(step_number, message, function, *args):
    result = run_step(step_number, message, function, *args)
    if result is None:
        raise RuntimeError(f"{message} konnte nicht abgeschlossen werden.")
    return result


def generate_valid_content(topic):
    content = generate_content(topic)
    return content if validate_content(content) else None


def ensure_script_minimum(generation, settings):
    minimum_words = int(settings["target_script_min_words"])
    current_words = count_words(generation.script)
    print(f"Skriptwortzahl: {current_words}")

    if current_words >= minimum_words:
        return generation.script

    print("Skript ist zu kurz und wird sinnvoll erweitert.")
    generation.script = extend_script(generation.topic, generation.script, minimum_words)
    if count_words(generation.script) < minimum_words:
        print("Das erweiterte Skript ist weiterhin zu kurz.")
        return None

    update_saved_generation(generation)
    print(f"Neue Skriptwortzahl: {count_words(generation.script)}")
    return generation.script


def create_voice_with_minimum_duration(generation, settings):
    minimum_duration = float(settings["target_video_min_seconds"])
    retries = int(settings["max_duration_retries"])

    for attempt in range(retries + 1):
        voice_file = generate_voice(generation)
        if voice_file is None:
            return None

        audio_duration = get_audio_duration(voice_file)
        if audio_duration is None:
            return None

        generation.audio_duration = audio_duration
        print(f"Tatsächliche Sprachlänge: {audio_duration:.1f} Sekunden")
        if audio_duration >= minimum_duration:
            return voice_file

        if attempt >= retries:
            print("Die Sprachdatei bleibt nach allen Versuchen zu kurz.")
            return None

        print("Sprachdatei ist zu kurz. Das Skript wird erweitert und die Stimme neu erstellt.")
        generation.script = extend_script(
            generation.topic,
            generation.script,
            count_words(generation.script) + 25,
        )
        update_saved_generation(generation)

    return None


def get_posted_folder(source_folder):
    posted_root = Path("posted")
    posted_root.mkdir(exist_ok=True)
    target_folder = posted_root / source_folder.name
    suffix = 2

    while target_folder.exists():
        target_folder = posted_root / f"{source_folder.name}_{suffix}"
        suffix += 1

    return target_folder


def move_generation_to_posted(generation):
    source_folder = Path(generation.output_folder)
    target_folder = get_posted_folder(source_folder)
    move(str(source_folder), str(target_folder))
    generation.output_folder = str(target_folder)
    update_status(target_folder / "metadata.json", "posted")
    return target_folder


def process_topic(topic, settings):
    generation = None
    current_step = "Skripterstellung"

    try:
        content = require_step(2, "Skript wird erstellt", generate_valid_content, topic)
        generation = Generation(
            topic=topic,
            title=content["title"],
            description=content["description"],
            hashtags=content["hashtags"],
            script=content["script"],
            status="script_created",
        )
        saved_file = save_script(generation)
        print(f"Script gespeichert unter: {saved_file.resolve()}")
        update_status(Path(generation.output_folder) / "metadata.json", "script_accepted")
        generation.status = "script_accepted"
        print("Skript automatisch akzeptiert.")
        show_generation(generation)

        current_step = "Skriptlänge"
        require_step(3, "Skriptlänge wird geprüft", ensure_script_minimum, generation, settings)

        current_step = "Spracherzeugung und Mindestdauer"
        require_step(4, "Stimme wird erzeugt", create_voice_with_minimum_duration, generation, settings)
        metadata_file = Path(generation.output_folder) / "metadata.json"
        update_status(metadata_file, "voice_created")
        generation.status = "voice_created"

        current_step = "Szenenplan"
        scene_file = require_step(5, "Szenenplan wird erstellt", generate_scenes, generation)
        update_status(metadata_file, "scenes_created")
        print(f"Szenenanzahl: {len(json.loads(scene_file.read_text(encoding='utf-8')))}")

        current_step = "Stockvideos"
        require_step(6, "Stockvideos werden gesucht", generate_stock_media, generation)
        update_status(metadata_file, "stock_media_created")
        print("Stockvideo-Anbieter: Pexels, Pixabay")

        current_step = "Untertitel"
        require_step(7, "Untertitel werden erstellt", generate_subtitles, generation)
        update_status(metadata_file, "subtitles_created")

        current_step = "Videorendering"
        video_file = require_step(8, "Video wird gerendert", generate_video, generation)
        update_status(metadata_file, "video_created")
        generation.status = "video_created"

        current_step = "Videoprüfung"
        final_video = Path(generation.output_folder) / "final_video.mp4"
        require_step(
            9,
            "Video wird geprüft",
            validate_rendered_video,
            final_video,
            float(settings["target_video_min_seconds"]),
        )

        current_step = "Verschieben nach posted"
        posted_folder = require_step(10, "Video wird nach posted verschoben", move_generation_to_posted, generation)

        if not remove_topic(generation.topic):
            raise RuntimeError("Das verwendete Thema konnte nicht aus topics.txt entfernt werden.")
        save_used_topic(generation.topic)

        print("Thema aus topics.txt entfernt.")
        print("Thema in used_topics.txt gespeichert.")
        print("Video erfolgreich erstellt.")
        print(f"Speicherort: {posted_folder.resolve()}")
        return True
    except Exception as error:
        log_pipeline_error(topic, current_step, error, generation)
        print(f"Thema fehlgeschlagen – nächstes Thema wird verarbeitet. ({error})")
        return False


def run():
    settings = load_settings()
    if settings["test_mode"] is True:
        run_test_mode()
        return

    pipeline_start = perf_counter()
    topics = require_step(1, "Themen werden vorbereitet", ensure_topic_supply)

    if not topics:
        print("Keine Themen vorhanden. Die Pipeline wird beendet.")
        return

    successful_videos = 0
    failed_topics = 0

    for topic in topics:
        print(f"\nAktuelles Thema: {topic}")
        if process_topic(topic, settings):
            successful_videos += 1
        else:
            failed_topics += 1

    completion_start = start_step(TOTAL_STEPS, TOTAL_STEPS, "Pipeline abgeschlossen")
    finish_step(TOTAL_STEPS, TOTAL_STEPS, completion_start)
    print(f"Verarbeitete Themen: {len(topics)}")
    print(f"Erfolgreiche Videos: {successful_videos}")
    print(f"Fehlgeschlagene Themen: {failed_topics}")
    print(f"Gesamtzeit: {perf_counter() - pipeline_start:.1f} Sekunden")
    print_cost_summary()
    print("Fertige Videos: posted")
    print("Zum Hochladen: python upload_ready.py")
