import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from config import load_pexels_api_key, load_pixabay_api_key


PEXELS_VIDEO_SEARCH_URL = "https://api.pexels.com/v1/videos/search"
PIXABAY_VIDEO_SEARCH_URL = "https://pixabay.com/api/videos/"


def load_stock_settings():
    defaults = {
        "stock_orientation": "portrait",
        "stock_results_per_query": 10,
        "stock_download_timeout": 60,
        "reuse_existing_stock": True,
        "stock_providers": ["pexels", "pixabay"],
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

    return scenes


def search_pexels_videos(keyword, api_key, settings):
    if not api_key:
        return None

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
            print("Pexels hat den Zugriff abgelehnt. Prüfe den aktiven API-Key und Endpunkt.")
        if response_text:
            print(f"Pexels-Antwort: {response_text}")
    except (URLError, OSError, json.JSONDecodeError) as error:
        print(f"Pexels-Suche für '{keyword}' fehlgeschlagen: {error}")

    return None


def choose_pexels_video(search_result):
    candidates = []

    for video in search_result.get("videos", []):
        for video_file in video.get("video_files", []):
            if video_file.get("file_type") != "video/mp4" or not video_file.get("link"):
                continue

            width = int(video_file.get("width") or 0)
            height = int(video_file.get("height") or 0)
            duration = float(video.get("duration") or 0)
            score = (height >= width, width >= 720, -abs(duration - 6), width * height)
            candidates.append((score, video, video_file))

    if not candidates:
        return None

    _, video, video_file = max(candidates, key=lambda candidate: candidate[0])
    return {
        "provider": "pexels",
        "creator": video.get("user", {}).get("name", "Unbekannt"),
        "source_url": video.get("url", ""),
        "media_url": video_file["link"],
    }


def search_pixabay_videos(keyword, api_key, settings):
    if not api_key:
        return None

    params = urlencode(
        {
            "key": api_key,
            "q": keyword,
            "min_width": 720,
            "per_page": settings["stock_results_per_query"],
            "safesearch": "true",
        }
    )

    try:
        with urlopen(
            f"{PIXABAY_VIDEO_SEARCH_URL}?{params}",
            timeout=settings["stock_download_timeout"],
        ) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, OSError, json.JSONDecodeError) as error:
        print(f"Pixabay-Suche für '{keyword}' fehlgeschlagen: {error}")
        return None


def choose_pixabay_video(search_result):
    candidates = []

    for video in search_result.get("hits", []):
        for size in ("large", "medium", "small"):
            video_file = video.get("videos", {}).get(size, {})
            media_url = video_file.get("url")

            if not media_url:
                continue

            width = int(video_file.get("width") or 0)
            height = int(video_file.get("height") or 0)
            duration = float(video.get("duration") or 0)
            score = (height >= width, width >= 720, -abs(duration - 6), width * height)
            candidates.append((score, video, video_file))

    if not candidates:
        return None

    _, video, video_file = max(candidates, key=lambda candidate: candidate[0])
    return {
        "provider": "pixabay",
        "creator": video.get("user", "Unbekannt"),
        "source_url": video.get("pageURL", ""),
        "media_url": video_file["url"],
    }


def simplified_keyword(keyword):
    words = keyword.split()
    return words[0] if len(words) > 1 else keyword


def find_stock_video(keywords, settings, used_media_urls):
    pexels_key = load_pexels_api_key()
    pixabay_key = load_pixabay_api_key()

    expanded_keywords = []
    for keyword in keywords:
        if keyword and keyword not in expanded_keywords:
            expanded_keywords.append(keyword)
        simplified = simplified_keyword(keyword)
        if simplified and simplified not in expanded_keywords:
            expanded_keywords.append(simplified)

    search_functions = {
        "pexels": (pexels_key, search_pexels_videos, choose_pexels_video),
        "pixabay": (pixabay_key, search_pixabay_videos, choose_pixabay_video),
    }
    providers = settings["stock_providers"]

    for provider in providers:
        if provider not in search_functions:
            continue
        api_key, search_function, choose_function = search_functions[provider]

        for search_keyword in expanded_keywords:
            search_result = search_function(search_keyword, api_key, settings)
            selected_video = choose_function(search_result) if search_result else None
            if selected_video and selected_video["media_url"] not in used_media_urls:
                return selected_video

    return None


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


def save_scenes(scenes_file, scenes):
    scenes_file.write_text(
        json.dumps(scenes, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


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
    scenes = load_scenes(scenes_file)

    if scenes is None:
        return None

    stock_folder = output_folder / "stock"
    stock_folder.mkdir(exist_ok=True)
    credits_file = stock_folder / "credits.json"
    credits_by_scene = {}

    if credits_file.exists():
        try:
            for credit in json.loads(credits_file.read_text(encoding="utf-8")):
                credits_by_scene[credit["scene_number"]] = credit
        except (json.JSONDecodeError, KeyError, TypeError):
            print("Bestehende Stock-Credits konnten nicht gelesen werden.")

    used_media_urls = {
        credit.get("media_url")
        for credit in credits_by_scene.values()
        if credit.get("media_url")
    }

    for scene in scenes:
        if scene.get("media_type") != "stock_video":
            print("Die Szenenplanung enthält kein zulässiges Stockvideo.")
            return None

        try:
            scene_number = int(scene["scene_number"])
            keywords = [
                str(scene["stock_search_query_de"]).strip(),
                str(scene["stock_search_query_en"]).strip(),
            ]
        except (KeyError, TypeError, ValueError):
            print("Eine Stock-Szene enthält ungültige Daten.")
            return None

        destination = stock_folder / f"scene_{scene_number:02d}.mp4"

        if destination.exists() and settings["reuse_existing_stock"] is True:
            continue

        if not all(keywords):
            print(f"Für Stock-Szene {scene_number} fehlt ein Suchbegriff.")
            return None

        selected_video = find_stock_video(keywords, settings, used_media_urls)

        if selected_video and download_video(
            selected_video["media_url"],
            destination,
            settings["stock_download_timeout"],
        ):
            credits_by_scene[scene_number] = {
                "scene_number": scene_number,
                "provider": selected_video["provider"],
                "creator": selected_video["creator"],
                "source_url": selected_video["source_url"],
                "media_url": selected_video["media_url"],
                "search_keywords": keywords,
            }
            scene["selected_provider"] = selected_video["provider"]
            scene["selected_video_path"] = str(Path("stock") / destination.name)
            used_media_urls.add(selected_video["media_url"])
            continue

        print(f"Kein passendes Stock-Video für Szene {scene_number} gefunden.")
        return None

    save_scenes(scenes_file, scenes)
    credits_file.write_text(
        json.dumps(
            [credits_by_scene[key] for key in sorted(credits_by_scene)],
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return stock_folder
