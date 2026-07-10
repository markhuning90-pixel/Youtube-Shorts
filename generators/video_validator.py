from pathlib import Path


def validate_video_assets(generation):
    if not generation.output_folder:
        print("Kein Output-Ordner für die Generierung gefunden.")
        return False

    output_folder = Path(generation.output_folder)
    required_files = ["voice.mp3", "subtitles.srt", "scenes.txt"]
    missing_files = [
        file_name
        for file_name in required_files
        if not (output_folder / file_name).exists()
    ]

    images_folder = output_folder / "images"

    if not images_folder.exists():
        print("Der Bilder-Ordner images wurde nicht gefunden.")
        return False

    if not any(images_folder.glob("*.png")):
        print("Im Bilder-Ordner wurde keine PNG-Datei gefunden.")
        return False

    if missing_files:
        print(f"Fehlende Dateien: {', '.join(missing_files)}")
        return False

    return True
