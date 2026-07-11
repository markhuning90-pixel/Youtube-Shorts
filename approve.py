from pathlib import Path
from shutil import move

from generators.status_manager import update_status


def approve_script(script_file):
    source_file = Path(script_file)
    generation_folder = source_file.parent

    if not source_file.exists():
        print("Kein Script zum Freigeben gefunden.")
        return

    while True:
        choice = input("Skript freigeben? (j/n/s):").strip().lower()

        if choice == "j":
            target_folder = Path("approval")
            message = "Skript freigegeben."
            break

        if choice == "n":
            target_folder = Path("rejected")
            message = "Skript abgelehnt."
            break

        if choice == "s":
            print("Freigabe übersprungen.")
            return

        print("Bitte nur j, n oder s eingeben.")

    target_folder.mkdir(exist_ok=True)
    target_path = target_folder / generation_folder.name
    move(str(generation_folder), str(target_path))

    if choice == "j":
        update_status(target_path / "metadata.json", "script_approved")

    print(message)
