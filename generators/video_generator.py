import json
import random
import shutil
import subprocess
from pathlib import Path


def get_audio_duration(voice_file):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(voice_file),
        ],
        capture_output=True,
        text=True,
    )

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


def load_scenes(scenes_file):
    if not scenes_file.exists():
        print("Die Datei scenes.json wurde nicht gefunden.")
        return None

    try:
        scenes = json.loads(scenes_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("Die Datei scenes.json enthält kein gültiges JSON.")
        return None

    if not isinstance(scenes, list) or not scenes:
        print("Die Datei scenes.json enthält keine Szenenliste.")
        return None

    try:
        parsed_scenes = [
            {
                "scene_number": int(scene["scene_number"]),
                "media_type": str(scene["media_type"]),
                "duration": float(scene["duration"]),
            }
            for scene in scenes
        ]
    except (KeyError, TypeError, ValueError):
        print("Die Datei scenes.json enthält unvollständige Szenendaten.")
        return None

    if any(
        scene["media_type"] not in {"ai_image", "stock"}
        or scene["duration"] <= 0
        for scene in parsed_scenes
    ):
        print("Die Datei scenes.json enthält ungültige Szenendaten.")
        return None

    return sorted(parsed_scenes, key=lambda scene: scene["scene_number"])


def get_motion_filter(frames_per_scene, zoom_increment):
    movements = ["zoom_in", "zoom_out", "pan_left", "pan_right", "pan_up", "pan_down"]
    motion = random.choice(movements)
    center_x = "iw/2-(iw/zoom/2)"
    center_y = "ih/2-(ih/zoom/2)"
    frame_range = max(1, frames_per_scene - 1)
    progress = f"(1-cos(PI*on/{frame_range}))/2"

    if motion == "zoom_in":
        zoom = f"min(zoom+{zoom_increment},1.1)"
        x_position, y_position = center_x, center_y
    elif motion == "zoom_out":
        zoom = f"if(eq(on,0),1.1,max(zoom-{zoom_increment},1))"
        x_position, y_position = center_x, center_y
    elif motion == "pan_left":
        zoom = "1.05"
        x_position, y_position = f"(iw-iw/zoom)*(1-{progress})", center_y
    elif motion == "pan_right":
        zoom = "1.05"
        x_position, y_position = f"(iw-iw/zoom)*{progress}", center_y
    elif motion == "pan_up":
        zoom = "1.05"
        x_position, y_position = center_x, f"(ih-ih/zoom)*(1-{progress})"
    else:
        zoom = "1.05"
        x_position, y_position = center_x, f"(ih-ih/zoom)*{progress}"

    return (
        "scale=2160:3840:force_original_aspect_ratio=increase,"
        "crop=2160:3840,"
        f"zoompan=z='{zoom}':x='{x_position}':y='{y_position}':"
        f"d={frames_per_scene}:s=1080x1920:fps=30,setsar=1"
    )


def build_scene_inputs(scenes, output_folder):
    command = []
    media_files = []

    for scene in scenes:
        scene_number = scene["scene_number"]

        if scene["media_type"] == "ai_image":
            media_file = output_folder / "images" / f"scene_{scene_number:02d}.png"
            input_options = ["-loop", "1", "-t", str(scene["duration"])]
        else:
            media_file = output_folder / "stock" / f"scene_{scene_number:02d}.mp4"
            input_options = ["-stream_loop", "-1"]

        if not media_file.exists():
            print(f"Mediendatei für Szene {scene_number} fehlt: {media_file}")
            return None, None

        command.extend(input_options + ["-i", str(media_file)])
        media_files.append(media_file)

    return command, media_files


def generate_video(generation):
    if not generation.output_folder:
        print("Kein Output-Ordner für die Generierung gefunden.")
        return None

    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        print("ffmpeg oder ffprobe wurde nicht gefunden. Bitte installiere beides.")
        return None

    output_folder = Path(generation.output_folder)
    voice_file = output_folder / "voice.mp3"
    subtitles_file = output_folder / "subtitles.ass"
    scenes = load_scenes(output_folder / "scenes.json")
    video_file = output_folder / "final_video.mp4"
    music_file = Path("assets/music/background.mp3")

    if not voice_file.exists() or not subtitles_file.exists():
        print("Voice-Datei oder ASS-Untertitel wurden nicht gefunden.")
        return None

    if scenes is None:
        return None

    audio_duration = get_audio_duration(voice_file)

    if audio_duration is None:
        return None

    scene_input_command, _ = build_scene_inputs(scenes, output_folder)

    if scene_input_command is None:
        return None

    command = ["ffmpeg", "-y"] + scene_input_command
    voice_input_index = len(scenes)
    command.extend(["-i", str(voice_file)])
    music_input_index = None

    if music_file.exists():
        music_input_index = voice_input_index + 1
        command.extend(["-stream_loop", "-1", "-i", str(music_file)])
    else:
        print("Keine Hintergrundmusik gefunden. Video wird ohne Musik erstellt.")

    filter_parts = []

    for input_index, scene in enumerate(scenes):
        duration = scene["duration"]

        if scene["media_type"] == "ai_image":
            frame_count = max(1, round(duration * 30))
            filter = get_motion_filter(frame_count, 0.1 / frame_count)
        else:
            filter = (
                f"trim=duration={duration},setpts=PTS-STARTPTS,"
                "scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,fps=30,setsar=1"
            )

        filter_parts.append(f"[{input_index}:v]{filter}[scene_{input_index}]")

    scene_streams = "".join(f"[scene_{index}]" for index in range(len(scenes)))
    subtitles_path = subtitles_file.resolve().as_posix().replace(":", "\\:")
    filter_parts.append(
        f"{scene_streams}concat=n={len(scenes)}:v=1:a=0,"
        f"tpad=stop_mode=clone:stop_duration={audio_duration},"
        f"trim=duration={audio_duration},setpts=PTS-STARTPTS,"
        f"ass='{subtitles_path}'[video_out]"
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
            "-c:v", "h264_nvenc", "-preset", "p4", "-rc", "vbr",
            "-cq", "23", "-b:v", "0",
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
