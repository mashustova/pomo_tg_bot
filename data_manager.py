import json
import os

# Путь к файлу для хранения данных
USER_DATA_FILE = "./user_data.json"


# Функция для загрузки данных из файла
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}


# Функция для сохранения данных в файл
def save_user_data(data):
    with open(USER_DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


# Функция для получения часового пояса пользователя по его ID
def get_timezone(user_id):
    user_data = load_user_data()
    return user_data.get(str(user_id), {}).get("timezone", None)


# Функция для установки часового пояса для пользователя
def set_timezone(user_id, timezone):
    user_data = load_user_data()
    if str(user_id) not in user_data:
        user_data[str(user_id)] = {}
    user_data[str(user_id)]["timezone"] = timezone
    save_user_data(user_data)
