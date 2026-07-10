import random
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


def has_nvenc():
    result = subprocess.run(
        ["ffmpeg", "-hide_banner", "-encoders"],
        capture_output=True,
        text=True,
    )
    return "h264_nvenc" in f"{result.stdout}\n{result.stderr}"


def get_motion_filter(motion, frames_per_image, zoom_increment):
    center_x = "iw/2-(iw/zoom/2)"
    center_y = "ih/2-(ih/zoom/2)"
    frame_range = max(1, frames_per_image - 1)
    progress = f"(1-cos(PI*on/{frame_range}))/2"

    if motion == "zoom_in":
        zoom = f"min(zoom+{zoom_increment},1.1)"
        x_position = center_x
        y_position = center_y
    elif motion == "zoom_out":
        zoom = f"if(eq(on,0),1.1,max(zoom-{zoom_increment},1))"
        x_position = center_x
        y_position = center_y
    elif motion == "pan_left":
        zoom = "1.05"
        x_position = f"(iw-iw/zoom)*(1-{progress})"
        y_position = center_y
    elif motion == "pan_right":
        zoom = "1.05"
        x_position = f"(iw-iw/zoom)*{progress}"
        y_position = center_y
    elif motion == "pan_up":
        zoom = "1.05"
        x_position = center_x
        y_position = f"(ih-ih/zoom)*(1-{progress})"
    else:
        zoom = "1.05"
        x_position = center_x
        y_position = f"(ih-ih/zoom)*{progress}"

    return (
        "scale=2160:3840:force_original_aspect_ratio=increase,"
        "crop=2160:3840,"
        f"zoompan=z='{zoom}':x='{x_position}':y='{y_position}':"
        f"d={frames_per_image}:s=1080x1920:fps=30"
    )


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
    music_file = Path("assets/music/background.mp3")
    audio_duration = get_audio_duration(voice_file)

    if audio_duration is None:
        return None

    image_duration = audio_duration / len(image_files)
    frames_per_image = max(1, round(image_duration * 30))
    zoom_increment = 0.1 / frames_per_image
    subtitles_path = subtitles_file.resolve().as_posix().replace(":", "\\:")
    movements = [
        "zoom_in",
        "zoom_out",
        "pan_left",
        "pan_right",
        "pan_up",
        "pan_down",
    ]

    command = ["ffmpeg", "-y"]

    for image_file in image_files:
        command.extend(["-i", str(image_file)])

    command.extend(["-i", str(voice_file)])

    voice_input_index = len(image_files)
    music_input_index = None

    if music_file.exists():
        music_input_index = voice_input_index + 1
        command.extend(["-stream_loop", "-1", "-i", str(music_file)])
    else:
        print("Keine Hintergrundmusik gefunden. Video wird ohne Musik erstellt.")

    filter_parts = []

    for index in range(len(image_files)):
        motion = random.choice(movements)
        motion_filter = get_motion_filter(motion, frames_per_image, zoom_increment)
        filter_parts.append(f"[{index}:v]{motion_filter}[video_{index}]")

    video_inputs = "".join(f"[video_{index}]" for index in range(len(image_files)))
    filter_parts.append(
        f"{video_inputs}concat=n={len(image_files)}:v=1:a=0,"
        f"setsar=1,ass='{subtitles_path}'[video_out]"
    )

    if music_input_index is not None:
        filter_parts.append(
            f"[{music_input_index}:a]volume=0.08[background_music];"
            f"[{voice_input_index}:a][background_music]"
            "amix=inputs=2:duration=first:dropout_transition=0[audio_out]"
        )

    command.extend(
        [
            "-filter_complex",
            ";".join(filter_parts),
            "-map",
            "[video_out]",
            "-map",
            "[audio_out]" if music_input_index is not None else f"{voice_input_index}:a:0",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-t",
            str(audio_duration),
            "-shortest",
        ]
    )
    cpu_options = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23"]

    if has_nvenc():
        print("NVIDIA GPU-Encoding wird verwendet.")
        gpu_options = [
            "-c:v",
            "h264_nvenc",
            "-preset",
            "p4",
            "-rc",
            "vbr",
            "-cq",
            "23",
            "-b:v",
            "0",
        ]
        result = subprocess.run(
            command + gpu_options + [str(video_file)],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print("GPU-Encoding fehlgeschlagen. Neuer Versuch mit CPU-Encoding.")
            print(result.stderr)
            result = subprocess.run(
                command + cpu_options + [str(video_file)],
                capture_output=True,
                text=True,
            )
    else:
        print("NVIDIA-Encoding nicht verfügbar. CPU-Encoding wird verwendet.")
        result = subprocess.run(
            command + cpu_options + [str(video_file)],
            capture_output=True,
            text=True,
        )

    if result.returncode != 0:
        print("Das Video konnte nicht erstellt werden.")
        print(result.stderr)
        return None

    return video_file
