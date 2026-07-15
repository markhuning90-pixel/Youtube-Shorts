import json
import shutil
import subprocess
from pathlib import Path


def validate_video_assets(generation):
    if not generation.output_folder:
        print("Kein Output-Ordner für die Generierung gefunden.")
        return False

    output_folder = Path(generation.output_folder)
    required_files = ["voice.mp3", "subtitles.ass", "scenes.json"]
    missing_files = [
        file_name
        for file_name in required_files
        if not (output_folder / file_name).exists()
    ]

    if missing_files:
        print(f"Fehlende Dateien: {', '.join(missing_files)}")
        return False

    try:
        scenes = json.loads((output_folder / "scenes.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("Die Datei scenes.json enthält kein gültiges JSON.")
        return False

    if not isinstance(scenes, list) or not scenes:
        print("Die Datei scenes.json enthält keine Szenen.")
        return False

    for scene in scenes:
        try:
            scene_number = int(scene["scene_number"])
            duration = float(scene["duration"])
        except (KeyError, TypeError, ValueError):
            print("Die Szenenplanung enthält unvollständige Daten.")
            return False

        if scene.get("media_type") != "stock_video" or duration <= 0:
            print("Die Szenenplanung enthält keine gültige Stockvideo-Szene.")
            return False

        stock_file = output_folder / "stock" / f"scene_{scene_number:02d}.mp4"
        if not stock_file.exists():
            print(f"Stockvideo für Szene {scene_number} fehlt: {stock_file}")
            return False

    return True


def validate_rendered_video(video_file, minimum_duration):
    video_path = Path(video_file)

    if not video_path.exists() or video_path.stat().st_size == 0:
        print("Das fertige Video fehlt oder ist leer.")
        return False

    if shutil.which("ffprobe") is None:
        print("ffprobe wurde nicht gefunden. Das fertige Video kann nicht geprüft werden.")
        return False

    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(video_path),
        ],
        capture_output=True,
        text=True,
    )

    try:
        duration = float(result.stdout.strip())
    except ValueError:
        print("Die Dauer des fertigen Videos konnte nicht geprüft werden.")
        return False

    if result.returncode != 0 or duration + 0.1 < minimum_duration:
        print("Das fertige Video ist kürzer als die erforderliche Mindestdauer.")
        return False

    print(f"Fertige Videolänge: {duration:.1f} Sekunden")
    return True
