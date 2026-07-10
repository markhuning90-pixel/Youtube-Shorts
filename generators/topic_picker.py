from generators.topic_loader import load_topics


def get_next_topic():
    topics = load_topics()

    if not topics:
        return None

    return topics[0]


def get_all_topics():
    return load_topics()
