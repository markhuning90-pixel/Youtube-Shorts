from datetime import datetime
from pathlib import Path


def save_script(topic, script):
    output_folder = Path("output")
    output_folder.mkdir(exist_ok=True)

    folder_name = datetime.now().strftime("%Y%m%d_%H%M%S")
    generation_folder = output_folder / folder_name
    generation_folder.mkdir(exist_ok=True)

    output_file = generation_folder / "script.txt"
    output_file.write_text(
        f"Thema:\n{topic}\n\nScript:\n{script}",
        encoding="utf-8",
    )

    return output_file
