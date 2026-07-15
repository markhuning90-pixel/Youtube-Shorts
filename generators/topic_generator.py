import json
from difflib import SequenceMatcher
from pathlib import Path

from openai import OpenAI

from config import load_api_key
from generators.topic_loader import load_topics
from utils.cost_tracker import record_gpt_cost


TOPIC_AREAS = (
    "Was-wäre-wenn-Szenarien",
    "Weltraum",
    "Erde und Natur",
    "menschlicher Körper",
    "Wissenschaft",
    "Technik",
    "Geschichte",
    "ungewöhnliche Alltagsfakten",
    "Geheimnisse und ungelöste Fragen",
)


def load_topic_settings():
    defaults = {
        "auto_generate_topics": True,
        "auto_topic_minimum": 3,
        "auto_topic_count": 5,
        "openai_model": "gpt-5-mini",
    }
    settings_file = Path("config/settings.json")

    if not settings_file.exists():
        return defaults

    try:
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("Die Datei config/settings.json enthält kein gültiges JSON.")
        return defaults

    return {key: settings.get(key, value) for key, value in defaults.items()}


def known_topics():
    topics = set(load_topics())
    used_topics_file = Path("used_topics.txt")

    if used_topics_file.exists():
        topics.update(
            line.strip()
            for line in used_topics_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )

    for metadata_file in Path(".").glob("*/**/metadata.json"):
        try:
            topic = json.loads(metadata_file.read_text(encoding="utf-8")).get("topic", "")
        except json.JSONDecodeError:
            continue
        if topic.strip():
            topics.add(topic.strip())

    return topics


def is_similar_topic(candidate, existing_topics):
    candidate_normalized = candidate.casefold()
    return any(
        SequenceMatcher(None, candidate_normalized, existing.casefold()).ratio() >= 0.82
        for existing in existing_topics
    )


def parse_topics(response_text, existing_topics, limit):
    new_topics = []

    for line in response_text.splitlines():
        topic = line.lstrip("-•0123456789. ").strip()
        if (
            len(topic) < 12
            or topic in new_topics
            or is_similar_topic(topic, existing_topics | set(new_topics))
        ):
            continue
        new_topics.append(topic)
        if len(new_topics) >= limit:
            break

    return new_topics


def ensure_topic_supply():
    settings = load_topic_settings()
    topics = load_topics()

    if not settings["auto_generate_topics"] or len(topics) >= settings["auto_topic_minimum"]:
        return topics

    api_key = load_api_key()
    if not api_key:
        print("Zu wenige Themen vorhanden, aber kein API-Key für neue Themen gefunden.")
        return topics

    requested_count = max(1, int(settings["auto_topic_count"]))
    prompt = f"""Erstelle {requested_count} neue, sachlich plausible Themen für deutsche
YouTube Shorts. Bereiche: {", ".join(TOPIC_AREAS)}.

Regeln:
- Formuliere neugierig, aber verspreche keine garantierte Viralität.
- Keine Clickbait-Lügen, keine Emojis und keine Erklärungen.
- Gib nur eine Liste mit je einem Thema pro Zeile aus.
"""

    try:
        response = OpenAI(api_key=api_key).responses.create(
            model=settings["openai_model"],
            input=prompt,
        )
    except Exception as error:
        print(f"Neue Themen konnten nicht erstellt werden: {error}")
        return topics

    record_gpt_cost()
    additions = parse_topics(response.output_text, known_topics(), requested_count)

    if not additions:
        print("Es wurden keine neuen, passenden Themen gefunden.")
        return topics

    topics_file = Path("topics.txt")
    with topics_file.open("a", encoding="utf-8") as file:
        if topics_file.stat().st_size:
            file.write("\n")
        file.write("\n".join(additions) + "\n")

    print(f"{len(additions)} neue Themen wurden ergänzt.")
    return load_topics()
