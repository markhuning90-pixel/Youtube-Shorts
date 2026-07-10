from approve import approve_script
from generators.content_generator import generate_content, validate_content
from generators.file_writer import save_script
from generators.status_manager import update_status
from generators.topic_picker import get_all_topics


def run():
    topics = get_all_topics()

    if not topics:
        print("Keine Themen gefunden.")
        return

    for index, topic in enumerate(topics):
        content = generate_content(topic)

        if validate_content(content):
            title = content["title"]
            description = content["description"]
            hashtags = content["hashtags"]
            script = content["script"]

            print("Thema:")
            print(topic)

            print("\nTitel:")
            print(title)

            print("\nBeschreibung:")
            print(description)

            print("\nHashtags:")
            print(hashtags)

            print("\nScript:")
            print(script)

            saved_file = save_script(
                topic=topic,
                script=script,
                title=title,
                description=description,
                hashtags=hashtags,
            )
            metadata_file = saved_file.parent / "metadata.json"
            update_status(metadata_file, "generated")

            print("\nStatus:")
            print("generated")

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
