import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ["https://www.googleapis.com/auth/tasks"]
TOKEN_PATH = "data/tokens.json"
CREDENTIALS_PATH = "credentials.json"


class GoogleTasks:
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

        self.service = build("tasks", "v1", credentials=creds)

    def add_task(self, task_data):
        task = (
            self.service.tasks()
            .insert(
                tasklist="@default",
                body={"title": task_data.get("title"), "due": task_data.get("due")},
            )
            .execute()
        )
        return task
