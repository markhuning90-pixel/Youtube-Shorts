from pathlib import Path
from shutil import move


def review_videos():
    videos = sorted(Path("completed").glob("*/final_video.mp4"))

    if not videos:
        print("Keine fertigen Videos zur Prüfung gefunden.")
        return

    for video_file in videos:
        while True:
            choice = input(f"Video freigeben? {video_file.parent.name} (j/n/s): ").strip().lower()

            if choice == "s":
                break

            if choice not in ("j", "n"):
                print("Bitte nur j, n oder s eingeben.")
                continue

            target_root = Path("posted" if choice == "j" else "rejected")
            target_root.mkdir(exist_ok=True)
            move(str(video_file.parent), str(target_root / video_file.parent.name))
            print("Video freigegeben." if choice == "j" else "Video abgelehnt.")
            break


if __name__ == "__main__":
    review_videos()
