import shutil
import subprocess
from pathlib import Path


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


def split_into_captions(script):
    words = script.split()
    captions = []
    current_caption = []

    for word in words:
        current_caption.append(word)

        if len(current_caption) >= 5 or (
            len(current_caption) >= 2 and word[-1] in ".,!?;:"
        ):
            captions.append(" ".join(current_caption))
            current_caption = []

    if current_caption:
        if captions and len(current_caption) < 2:
            previous_caption = captions[-1].split()

            if len(previous_caption) > 2:
                current_caption.insert(0, previous_caption.pop())
                captions[-1] = " ".join(previous_caption)
                captions.append(" ".join(current_caption))
            else:
                captions[-1] = f"{captions[-1]} {' '.join(current_caption)}"
        else:
            captions.append(" ".join(current_caption))

    return captions


def format_srt_time(seconds):
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    seconds, milliseconds = divmod(milliseconds, 1_000)
    return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


def format_ass_time(seconds):
    centiseconds = round(seconds * 100)
    hours, centiseconds = divmod(centiseconds, 360_000)
    minutes, centiseconds = divmod(centiseconds, 6_000)
    seconds, centiseconds = divmod(centiseconds, 100)
    return f"{hours}:{minutes:02}:{seconds:02}.{centiseconds:02}"


def escape_ass_text(text):
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def generate_subtitles(generation):
    if not generation.output_folder:
        print("Kein Output-Ordner für die Generierung gefunden.")
        return None

    if shutil.which("ffprobe") is None:
        print("ffprobe wurde nicht gefunden. Bitte installiere ffprobe.")
        return None

    output_folder = Path(generation.output_folder)
    voice_file = output_folder / "voice.mp3"

    if not voice_file.exists():
        print("Die Sprachdatei voice.mp3 wurde nicht gefunden.")
        return None

    audio_duration = get_audio_duration(voice_file)
    captions = split_into_captions(generation.script)

    if audio_duration is None or not captions:
        if not captions:
            print("Für die Untertitel wurde kein Script gefunden.")
        return None

    caption_duration = audio_duration / len(captions)
    subtitle_blocks = []

    for number, caption in enumerate(captions, start=1):
        start_time = (number - 1) * caption_duration
        end_time = number * caption_duration
        subtitle_blocks.append(
            f"{number}\n"
            f"{format_srt_time(start_time)} --> {format_srt_time(end_time)}\n"
            f"{caption}"
        )

    output_file = output_folder / "subtitles.srt"
    output_file.write_text("\n\n".join(subtitle_blocks) + "\n", encoding="utf-8")

    ass_header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Shorts,Arial,34,&H00FFFFFF,&H00000000,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,3,0,2,10,10,160,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    ass_events = []

    for number, caption in enumerate(captions, start=1):
        start_time = (number - 1) * caption_duration
        end_time = number * caption_duration
        ass_events.append(
            f"Dialogue: 0,{format_ass_time(start_time)},{format_ass_time(end_time)},"
            f"Shorts,,0,0,0,,{escape_ass_text(caption)}"
        )

    ass_file = output_folder / "subtitles.ass"
    ass_file.write_text(ass_header + "\n".join(ass_events) + "\n", encoding="utf-8")

    return ass_file
