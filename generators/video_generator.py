import shutil
import subprocess
from pathlib import Path

from generators.video_validator import validate_video_assets


def get_audio_duration(voice_file):
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(voice_file),
    ]
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        print("Die Länge der Sprachdatei konnte nicht ermittelt werden.")
        return None

    try:
        return float(result.stdout.strip())
    except ValueError:
        print("Die Länge der Sprachdatei konnte nicht ermittelt werden.")
        return None


def generate_video(generation):
    if not validate_video_assets(generation):
        return None

    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        print("ffmpeg oder ffprobe wurde nicht gefunden. Bitte installiere beides.")
        return None

    output_folder = Path(generation.output_folder)
    images_folder = output_folder / "images"
    image_files = sorted(images_folder.glob("*.png"))
    voice_file = output_folder / "voice.mp3"
    subtitles_file = output_folder / "subtitles.ass"
    video_file = output_folder / "final_video.mp4"
    concat_file = output_folder / "images.txt"
    audio_duration = get_audio_duration(voice_file)

    if audio_duration is None:
        return None

    image_duration = audio_duration / len(image_files)
    subtitles_path = subtitles_file.resolve().as_posix().replace(":", "\\:")
    video_filter = (
        "scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,setsar=1,fps=30,"
        f"ass='{subtitles_path}'"
    )

    try:
        concat_lines = []

        for image_file in image_files:
            concat_lines.append(f"file '{image_file.resolve().as_posix()}'\n")
            concat_lines.append(f"duration {image_duration}\n")

        concat_lines.append(f"file '{image_files[-1].resolve().as_posix()}'\n")
        concat_file.write_text("".join(concat_lines), encoding="utf-8")

        command = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-i",
            str(voice_file),
            "-map",
            "0:v:0",
            "-map",
            "1:a:0",
            "-vf",
            video_filter,
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-t",
            str(audio_duration),
            "-shortest",
            str(video_file),
        ]
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            print("Das Video konnte nicht erstellt werden.")
            print(result.stderr)
            return None
    finally:
        if concat_file.exists():
            concat_file.unlink()

    return video_file
