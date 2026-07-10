from pathlib import Path


def count_files(folder):
    path = Path(folder)

    if not path.exists():
        return 0

    return len([item for item in path.iterdir()])


print("Projektstatus")
print("-" * 20)
print(f"Fertige Videos: {count_files('completed')}")
print(f"Abgelehnte Videos: {count_files('rejected')}")
print(f"Dateien im Output: {count_files('output')}")
