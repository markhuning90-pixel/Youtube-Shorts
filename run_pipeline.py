from approve import approve_script
from generators.content_generator import generate_content, validate_content
from generators.file_writer import save_script
from generators.topic_picker import get_next_topic


def run():
    topic = get_next_topic()

    if topic is None:
        print("Keine Themen gefunden.")
        return

    content = generate_content(topic)

    if not validate_content(content):
        return

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

    save_script(topic, script)
    print("\nScript erfolgreich gespeichert.")

    approve_script()
