from generators.topic_picker import get_next_topic
from generators.script_generator import generate_script

topic = get_next_topic()

if topic is None:
    print("Keine Themen gefunden.")
else:
    script = generate_script(topic)

    print("Thema:")
    print(topic)

    print("\nScript:")
    print(script)
