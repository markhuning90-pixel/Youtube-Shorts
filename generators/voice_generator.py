from pathlib import Path

from openai import OpenAI

from config import load_api_key


def generate_voice(generation):
    if not generation.output_folder:
        print("Kein Output-Ordner für die Generierung gefunden.")
        return None

    api_key = load_api_key()

    if not api_key:
        raise RuntimeError("Kein API-Key gefunden.")

    output_file = Path(generation.output_folder) / "voice.mp3"
    client = OpenAI(api_key=api_key)

    with client.audio.speech.with_streaming_response.create(
        model="tts-1",
        voice="alloy",
        input=generation.script,
    ) as response:
        response.stream_to_file(output_file)

    return output_file
