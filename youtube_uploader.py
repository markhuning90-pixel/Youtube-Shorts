from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


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

    video = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": f"{description}\n\n{hashtags}".strip(),
                "categoryId": "22",
            },
            "status": {
                "privacyStatus": "private",
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
