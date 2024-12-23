event_data = {
    "summary": "",
    "location": "",
    "description": "",
    "start": {"dateTime": "", "timeZone": ""},
    "end": {"dateTime": "", "timeZone": ""},
    "recurrence": [],
    "attendees": [],
    "reminders": {"useDefault": False, "overrides": []},
}


def update_event_field(field_path, value):
    """Обновляет указанное поле в event_data."""
    keys = field_path.split(".")
    data = event_data
    for key in keys[:-1]:
        data = data[key]
    data[keys[-1]] = value


def reset_event_data():
    """Сбрасывает event_data до пустого состояния."""
    event_data = {
        "summary": "",
        "location": "",
        "description": "",
        "start": {"dateTime": "", "timeZone": ""},
        "end": {"dateTime": "", "timeZone": ""},
        "recurrence": [],
        "attendees": [],
        "reminders": {"useDefault": False, "overrides": []},
    }


def get_event_data():
    """Возвращает текущее состояние event_data."""
    return event_data
