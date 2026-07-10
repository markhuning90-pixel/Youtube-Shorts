from pathlib import Path


def save_script(topic, script):
    output_folder = Path("output")
    output_folder.mkdir(exist_ok=True)

    output_file = output_folder / "script.txt"
    output_file.write_text(
        f"Thema:\n{topic}\n\nScript:\n{script}",
        encoding="utf-8",
    )
