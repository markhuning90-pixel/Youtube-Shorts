from generators.topic_loader import load_topics

topics = load_topics()

print(f"{len(topics)} Themen gefunden:\n")

for number, topic in enumerate(topics, start=1):
    print(f"{number}. {topic}")
