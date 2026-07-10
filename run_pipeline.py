from approve import approve_script
from generators.file_writer import save_script
from generators.topic_picker import get_next_topic
from generators.script_generator import generate_script


def run():
    topic = get_next_topic()

    if topic is None:
        print("Keine Themen gefunden.")
        return

    script = generate_script(topic)
    save_script(topic, script)
    approve_script()

    print("Thema:")
    print(topic)

    print("\nScript:")
    print(script)

    print("\nScript erfolgreich gespeichert.")
