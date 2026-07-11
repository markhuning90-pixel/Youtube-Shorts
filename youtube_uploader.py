import json
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = Path("token.json")


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
    credentials = None

    if TOKEN_FILE.exists():
        credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if credentials and credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            "client_secret.json",
            SCOPES,
        )
        credentials = flow.run_local_server(port=0)
        TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")

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

    return response["id"]


if __name__ == "__main__":
    print("Bitte upload_video(video_path, title, description, hashtags) verwenden.")
