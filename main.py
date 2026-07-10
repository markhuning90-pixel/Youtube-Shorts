from generators.topic_picker import get_next_topic

topic = get_next_topic()

if topic is None:
    print("Keine Themen gefunden.")
else:
    print("Nächstes Thema:")
    print(topic)
