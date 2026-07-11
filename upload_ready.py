import json
from pathlib import Path
from shutil import move

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

        uploaded_folder = Path("uploaded") / video_file.parent.name

        if uploaded_folder.exists():
            print(
                "Zielordner existiert bereits. Das Video wird nicht überschrieben oder hochgeladen."
            )
            continue

        try:
            video_id = upload_video(
                str(video_file),
                metadata.get("title", ""),
                metadata.get("description", ""),
                metadata.get("hashtags", ""),
            )
        except Exception as error:
            print(f"YouTube-Upload fehlgeschlagen: {error}")
            continue

        metadata["status"] = "uploaded"
        metadata["youtube_video_id"] = video_id
        metadata_file.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        uploaded_folder.parent.mkdir(exist_ok=True)
        move(str(video_file.parent), str(uploaded_folder))
        print("Video erfolgreich hochgeladen und nach uploaded verschoben.")


if __name__ == "__main__":
    upload_ready_videos()
