from approve import approve_script
from generators.content_generator import generate_content, validate_content
from generators.file_writer import save_script
from generators.status_manager import update_status
from generators.topic_picker import get_all_topics
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

            print("Thema:")
            print(generation.topic)

            print("\nTitel:")
            print(generation.title)

            print("\nBeschreibung:")
            print(generation.description)

            print("\nHashtags:")
            print(generation.hashtags)

            print("\nScript:")
            print(generation.script)

            saved_file = save_script(
                topic=generation.topic,
                script=generation.script,
                title=generation.title,
                description=generation.description,
                hashtags=generation.hashtags,
            )
            metadata_file = saved_file.parent / "metadata.json"
            update_status(metadata_file, "generated")

            print("\nStatus:")
            print(generation.status)

            print("\nScript erfolgreich gespeichert.")
            print("Gespeichert unter:")
            print(saved_file.resolve())

            approve_script()

        if index < len(topics) - 1:
            while True:
                choice = input("Nächstes Thema bearbeiten? (j/n):").strip().lower()

                if choice == "j":
                    break

                if choice == "n":
                    return

                print("Bitte nur j oder n eingeben.")
