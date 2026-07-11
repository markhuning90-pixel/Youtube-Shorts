import json
from pathlib import Path

from youtube_uploader import upload_video


def upload_ready_videos():
    videos = sorted(Path("posted").glob("*/final_video.mp4"))

    if not videos:
        print("Keine uploadbereiten Videos gefunden.")
        return

    for video_file in videos:
        metadata_file = video_file.parent / "metadata.json"

        if not metadata_file.exists():
            print(f"Metadaten fehlen: {video_file.parent}")
            continue

        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        choice = input(f"{video_file.name} auf YouTube hochladen? (j/n): ").strip().lower()

        if choice != "j":
            print("Upload übersprungen.")
            continue

        try:
            upload_video(str(video_file), metadata.get("title", ""), metadata.get("description", ""), metadata.get("hashtags", ""))
            print("Video auf YouTube hochgeladen.")
        except Exception as error:
            print(f"YouTube-Upload fehlgeschlagen: {error}")


if __name__ == "__main__":
    upload_ready_videos()
