from pathlib import Path


def generate_subtitles(generation):
    if not generation.output_folder:
        print("Kein Output-Ordner für die Generierung gefunden.")
        return None

    output_file = Path(generation.output_folder) / "subtitles.srt"
    output_file.write_text(
        f"1\n00:00:00,000 --> 00:00:10,000\n{generation.script}\n",
        encoding="utf-8",
    )

    return output_file
