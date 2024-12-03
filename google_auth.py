import os
import pickle
import sqlite3
import requests
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from commands.utils import get_meetings_for_user

# Определение необходимых областей доступа
SCOPES = ['https://www.googleapis.com/auth/calendar']

def authenticate_google():
    creds = None
    # Проверка наличия сохраненного токена
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # Проверка на действительность токена
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Если токена нет или он недействителен, инициализируем процесс аутентификации
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)  # Откроется локальный сервер для аутентификации

            # Сохраняем токен для следующего использования
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

    return creds



def get_events(creds):
    """Получение событий из Google Calendar."""
    url = 'https://www.googleapis.com/calendar/v3/calendars/primary/events'
    
    headers = {
        'Authorization': f'Bearer {creds.token}',
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()  # Вернуть полученные события
    else:
        print(f'Ошибка при получении событий: {response.json()}')

def create_event(creds, meeting):
    """Создание события в Google Calendar."""
    url = 'https://www.googleapis.com/calendar/v3/calendars/primary/events'
    start_time = datetime.fromisoformat(meeting[2]).isoformat() + 'Z'
    end_time = datetime.fromisoformat(meeting[3]).isoformat() + 'Z'
    event = {
        'summary': meeting[1],  # Название
        'start': {
            'dateTime': start_time,  # Время начала
            'timeZone': 'Europe/Moscow',  # Установите свой часовой пояс
        },
        'end': {
            'dateTime': end_time,  # Время окончания
            'timeZone': 'Europe/Moscow',  # Установите свой часовой пояс
        },
        'description': meeting[4],  # Описание
    }

    headers = {
        'Authorization': f'Bearer {creds.token}',
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, json=event)

    if response.status_code == 200:
        print(f"Событие '{meeting[1]}' успешно добавлено в Google Calendar.")
    else:
        print(f'Ошибка при добавлении события: {response.json()}')

def delete_event(creds, event_id):
    """Удаление события из Google Calendar."""
    url = f'https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}'
    
    headers = {
        'Authorization': f'Bearer {creds.token}',
    }

    response = requests.delete(url, headers=headers)

    if response.status_code == 204:
        print(f"Событие с ID {event_id} успешно удалено.")
    else:
        print(f"Ошибка при удалении события с ID {event_id}: {response.json()}")

def sync_events(user_id):
    """Синхронизация встреч между SQLite и Google Calendar."""
    creds = authenticate_google()  # Аутентификация
    meetings = get_meetings_for_user(user_id)  # Получаем встречи из базы данных
    calendar_events = get_events(creds)  # Получаем события из Google Calendar

    # Создаем список ID событий из Google Calendar
    calendar_event_ids = {event['id'] for event in calendar_events.get('items', [])}

    # Добавляем новые события из базы данных в Google Calendar
    for meeting in meetings:
        event_exists = any(meeting[1] in event['summary'] for event in calendar_events.get('items', []))
        if not event_exists:
            create_event(creds, meeting)

    # Удаляем события из Google Calendar, отсутствующие в базе данных
    for event in calendar_events.get('items', []):
        event_exists = any(meeting[1] in event['summary'] for meeting in meetings)
        if not event_exists:
            delete_event(creds, event['id'])