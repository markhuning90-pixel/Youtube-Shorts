import json
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_youtube_privacy():
    settings_file = Path("config/settings.json")

    if not settings_file.exists():
        return "private"

    try:
        settings = json.loads(settings_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "private"

    return settings.get("youtube_privacy", "private")


def get_youtube():
    flow = InstalledAppFlow.from_client_secrets_file(
        "client_secret.json",
        SCOPES
    )

    credentials = flow.run_local_server(port=0)

    return build(
        "youtube",
        "v3",
        credentials=credentials
    )


def upload_video(video_path, title, description, hashtags):
    youtube = get_youtube()
    privacy_status = get_youtube_privacy()

    video = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": f"{description}\n\n{hashtags}".strip(),
                "categoryId": "22",
            },
            "status": {
                "privacyStatus": privacy_status,
            },
        },
        media_body=MediaFileUpload(
            video_path,
            mimetype="video/mp4",
        ),
    )

    response = video.execute()

    print("Upload erfolgreich!")
    print("Video ID:", response["id"])


if __name__ == "__main__":
    print("Bitte upload_video(video_path, title, description, hashtags) verwenden.")
