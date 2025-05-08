import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/calendar"]
TOKEN_PATH = "data/tokens.json"
CREDENTIALS_PATH = "credentials.json"


class GoogleCalendar:
    def __init__(self):
        self.service = None

    def authenticate_user(self):
        creds = None
        # Проверяем, существует ли файл токенов
        if os.path.exists(TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        # Если токен недействителен, запускаем повторную авторизацию
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_PATH, SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Сохраняем новые токены
            with open(TOKEN_PATH, "w") as token:
                token.write(creds.to_json())

        self.service = build("calendar", "v3", credentials=creds)

    def add_event(self, event_data):
        event = (
            self.service.events()
            .insert(
                calendarId="primary",
                body={
                    "summary": event_data.get("summary"),
                    "start": {
                        "dateTime": event_data.get("start"),
                        "timeZone": event_data.get("timeZone"),
                    },
                    "end": {
                        "dateTime": event_data.get("end"),
                        "timeZone": event_data.get("timeZone"),
                    },
                },
            )
            .execute()
        )
        return event
