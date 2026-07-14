import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from config import load_pexels_api_key


PEXELS_VIDEO_SEARCH_URL = "https://api.pexels.com/v1/videos/search"


def load_stock_settings():
    defaults = {
        "stock_provider": "pexels",
        "stock_media_type": "video",
        "stock_orientation": "portrait",
        "stock_results_per_query": 10,
        "stock_download_timeout": 60,
        "reuse_existing_stock": True,
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


def load_scenes(scenes_file):
    try:
        scenes = json.loads(scenes_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("Die Datei scenes.json enthält kein gültiges JSON.")
        return None

    if not isinstance(scenes, list):
        print("Die Datei scenes.json enthält keine Szenenliste.")
        return None

    try:
        return [
            {
                "scene_number": int(scene["scene_number"]),
                "stock_keyword": str(scene["stock_keyword"]).strip(),
            }
            for scene in scenes
            if scene["media_type"] == "stock"
        ]
    except (KeyError, TypeError, ValueError):
        print("Die Datei scenes.json enthält ungültige Stock-Szenen.")
        return None


def search_pexels_videos(keyword, api_key, settings):
    params = urlencode(
        {
            "query": keyword,
            "orientation": settings["stock_orientation"],
            "per_page": settings["stock_results_per_query"],
        }
    )
    request = Request(
        f"{PEXELS_VIDEO_SEARCH_URL}?{params}",
        headers={
            "Authorization": api_key,
            "User-Agent": "FaktenBlitz-VideoGenerator/1.0",
            "Accept": "application/json",
        },
    )

    try:
        with urlopen(request, timeout=settings["stock_download_timeout"]) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        try:
            response_text = error.read().decode("utf-8", errors="replace")
        except OSError:
            response_text = "Kein Antworttext verfügbar."

        print(f"Pexels-Suche für '{keyword}' fehlgeschlagen: HTTP {error.code}")

        if error.code == 401:
            print("Pexels-API-Key ist ungültig oder fehlt.")
        elif error.code == 403:
            print(
                "Pexels hat den Zugriff abgelehnt. Prüfe, ob der API-Key aktiv ist "
                "und der richtige Endpunkt verwendet wird."
            )

        if response_text:
            print(f"Pexels-Antwort: {response_text}")

        return None
    except (URLError, OSError, json.JSONDecodeError) as error:
        print(f"Pexels-Suche für '{keyword}' fehlgeschlagen: {error}")
        return None


def choose_video(search_result):
    candidates = []

    for video in search_result.get("videos", []):
        for video_file in video.get("video_files", []):
            if video_file.get("file_type") != "video/mp4" or not video_file.get("link"):
                continue

            width = int(video_file.get("width") or 0)
            height = int(video_file.get("height") or 0)
            duration = float(video.get("duration") or 0)
            score = (
                height >= width,
                width >= 720,
                -abs(duration - 8),
                width * height,
            )
            candidates.append((score, video, video_file))

    if not candidates:
        return None

    _, video, video_file = max(candidates, key=lambda candidate: candidate[0])
    return video, video_file


def simplified_keyword(keyword):
    words = keyword.split()
    return words[0] if len(words) > 1 else keyword


def download_video(media_url, destination, timeout):
    request = Request(
        media_url,
        headers={
            "User-Agent": "FaktenBlitz-VideoGenerator/1.0",
            "Accept": "video/mp4,*/*",
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            with destination.open("wb") as output_file:
                while chunk := response.read(1024 * 1024):
                    output_file.write(chunk)
    except (HTTPError, URLError, OSError) as error:
        if destination.exists():
            destination.unlink()
        print(f"Stock-Video konnte nicht heruntergeladen werden: {error}")
        return False

    return True


def generate_stock_media(generation):
    if not generation.output_folder:
        print("Kein Output-Ordner für die Generierung gefunden.")
        return None

    output_folder = Path(generation.output_folder)
    scenes_file = output_folder / "scenes.json"

    if not scenes_file.exists():
        print("Die Datei scenes.json wurde nicht gefunden.")
        return None

    settings = load_stock_settings()
    stock_scenes = load_scenes(scenes_file)

    if stock_scenes is None:
        return None

    stock_folder = output_folder / "stock"
    stock_folder.mkdir(exist_ok=True)

    if not stock_scenes:
        return stock_folder

    api_key = load_pexels_api_key()

    if not api_key:
        print("Kein Pexels-API-Key gefunden.")
        return None

    credits_file = stock_folder / "credits.json"
    credits_by_scene = {}

    if credits_file.exists():
        try:
            for credit in json.loads(credits_file.read_text(encoding="utf-8")):
                credits_by_scene[credit["scene_number"]] = credit
        except (json.JSONDecodeError, KeyError, TypeError):
            print("Bestehende Stock-Credits konnten nicht gelesen werden.")

    for scene in stock_scenes:
        scene_number = scene["scene_number"]
        keyword = scene["stock_keyword"]
        destination = stock_folder / f"scene_{scene_number:02d}.mp4"

        if destination.exists() and settings["reuse_existing_stock"] is True:
            continue

        if not keyword:
            print(f"Für Stock-Szene {scene_number} fehlt ein Suchbegriff.")
            return None

        search_result = search_pexels_videos(keyword, api_key, settings)
        selected_video = choose_video(search_result) if search_result else None

        if selected_video is None:
            fallback_keyword = simplified_keyword(keyword)
            if fallback_keyword != keyword:
                search_result = search_pexels_videos(fallback_keyword, api_key, settings)
                selected_video = choose_video(search_result) if search_result else None

        if selected_video is None:
            print(f"Kein passendes Pexels-Video für Szene {scene_number} gefunden.")
            return None

        video, video_file = selected_video

        if not download_video(
            video_file["link"],
            destination,
            settings["stock_download_timeout"],
        ):
            return None

        credits_by_scene[scene_number] = {
            "scene_number": scene_number,
            "provider": settings["stock_provider"],
            "creator": video.get("user", {}).get("name", "Unbekannt"),
            "source_url": video.get("url", ""),
            "media_url": video_file["link"],
            "search_keyword": keyword,
        }

    credits_file.write_text(
        json.dumps(
            [credits_by_scene[key] for key in sorted(credits_by_scene)],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return stock_folder
