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


def upload_video():
    youtube = get_youtube()

    video = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "Test Upload",
                "description": "Automatischer Test Upload",
                "categoryId": "22"
            },
            "status": {
                "privacyStatus": "private"
            }
        },
        media_body=MediaFileUpload(
            "test.mp4",
            mimetype="video/mp4"
        )
    )

    response = video.execute()

    print("Upload erfolgreich!")
    print("Video ID:", response["id"])


if __name__ == "__main__":
    upload_video()