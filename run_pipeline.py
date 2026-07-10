from approve import approve_script
from console import show_generation
from generators.character_generator import generate_character
from generators.content_generator import generate_content, validate_content
from generators.file_writer import save_script
from generators.image_generator import generate_images
from generators.image_prompt_generator import generate_image_prompts
from generators.scene_generator import generate_scenes
from generators.status_manager import update_status
from generators.subtitle_generator import generate_subtitles
from generators.topic_picker import get_all_topics
from generators.video_generator import generate_video
from generators.voice_generator import generate_voice
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

            saved_file = save_script(generation)
            metadata_file = saved_file.parent / "metadata.json"
            voice_file = generate_voice(generation)

            if voice_file is not None:
                update_status(metadata_file, "voice_created")
                generation.status = "voice_created"

                subtitle_file = generate_subtitles(generation)

                if subtitle_file is not None:
                    update_status(metadata_file, "subtitles_created")
                    generation.status = "subtitles_created"

                    scene_file = generate_scenes(generation)

                    if scene_file is not None:
                        update_status(metadata_file, "scenes_created")
                        generation.status = "scenes_created"

                        images_folder = None
                        image_prompt_file = None
                        character_file = generate_character(generation)

                        if character_file is not None:
                            update_status(metadata_file, "character_created")
                            generation.status = "character_created"

                            image_prompt_file = generate_image_prompts(generation)

                        if image_prompt_file is not None:
                            update_status(metadata_file, "image_prompts_created")
                            generation.status = "image_prompts_created"

                            images_folder = generate_images(generation)

                            if images_folder is not None:
                                update_status(metadata_file, "images_created")
                                generation.status = "images_created"

                                video_file = generate_video(generation)

                                if video_file is not None:
                                    update_status(metadata_file, "video_created")
                                    generation.status = "video_created"

                print("\nSprachdatei erstellt.")
                print("Gespeichert unter:")
                print(voice_file.resolve())

                if subtitle_file is not None:
                    print("\nUntertitel erstellt.")
                    print("Gespeichert unter:")
                    print(subtitle_file.resolve())

                    if scene_file is not None:
                        print("\nSzenenplan erstellt.")
                        print("Gespeichert unter:")
                        print(scene_file.resolve())

                        if character_file is not None:
                            print("\nHauptcharakter erstellt.")
                            print("Gespeichert unter:")
                            print(character_file.resolve())

                            if image_prompt_file is not None:
                                print("\nBildprompts erstellt.")
                                print("Gespeichert unter:")
                                print(image_prompt_file.resolve())

                                if images_folder is not None:
                                    print("\nBilder erstellt.")
                                    print("Gespeichert unter:")
                                    print(images_folder.resolve())

                                    if video_file is not None:
                                        print("\nVideo erstellt.")
                                        print("Gespeichert unter:")
                                        print(video_file.resolve())

            show_generation(generation)

            print("\nScript erfolgreich gespeichert.")
            print("Gespeichert unter:")
            print(saved_file.resolve())

            approve_script(saved_file)

        if index < len(topics) - 1:
            while True:
                choice = input("Nächstes Thema bearbeiten? (j/n):").strip().lower()

                if choice == "j":
                    break

                if choice == "n":
                    return

                print("Bitte nur j oder n eingeben.")
