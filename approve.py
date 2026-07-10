from pathlib import Path
from shutil import move


def approve_script(script_file):
    source_file = Path(script_file)

    if not source_file.exists():
        print("Kein Script zum Freigeben gefunden.")
        return

    while True:
        choice = input("Skript freigeben? (j/n/s):").strip().lower()

        if choice == "j":
            target_folder = Path("completed")
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
    move(str(source_file), str(target_folder / "script.txt"))
    print(message)
