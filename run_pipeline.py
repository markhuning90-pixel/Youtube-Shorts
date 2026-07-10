from approve import approve_script
from console import show_generation
from generators.content_generator import generate_content, validate_content
from generators.file_writer import save_script
from generators.status_manager import update_status
from generators.topic_picker import get_all_topics
from generators.voice_generator import generate_voice
from models.generation import Generation


def run():
    topics = get_all_topics()

    if not topics:
        print("Keine Themen gefunden.")
        return

    for index, topic in enumerate(topics):
        content = generate_content(topic)

        if validate_content(content):
            generation = Generation(
                topic=topic,
                title=content["title"],
                description=content["description"],
                hashtags=content["hashtags"],
                script=content["script"],
                status="generated",
            )

            saved_file = save_script(generation)
            metadata_file = saved_file.parent / "metadata.json"
            voice_file = generate_voice(generation)

            if voice_file is not None:
                update_status(metadata_file, "voice_created")
                generation.status = "voice_created"

                print("\nSprachdatei erstellt.")
                print("Gespeichert unter:")
                print(voice_file.resolve())

            show_generation(generation)

            print("\nScript erfolgreich gespeichert.")
            print("Gespeichert unter:")
            print(saved_file.resolve())

            approve_script(saved_file)

        if index < len(topics) - 1:
            while True:
                choice = input("Nächstes Thema bearbeiten? (j/n):").strip().lower()

                if choice == "j":
                    break

                if choice == "n":
                    return

                print("Bitte nur j oder n eingeben.")
