import os
import pickle
import sqlite3
import requests
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google_auth_oauthlib.flow import Flow
from commands.utils import get_meetings_for_user

# мы не говорим о том, что происходит в этом файле
# Определение необходимых областей доступа
SCOPES = ['https://www.googleapis.com/auth/calendar']
CLIENT_SECRETS_FILE = "credentials.json"

def authenticate_google(user_id):
    creds = None
    token_file = f'token_{user_id}.pickle'

    # Проверка наличия сохраненного токена
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            creds = pickle.load(token)

    # Проверка на действительность токена
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())  # Обновляем токен, если он истек
        else:
            # Генерируем URL для аутентификации
            flow = Flow.from_client_secrets_file('credentials.json', SCOPES)
            flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
            authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')

            print(f"Перейдите по следующей ссылке для аутентификации: {authorization_url}")
            return None  

    return creds  # Если токен действителен, возвращаем creds


def generate_auth_url(user_id):
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'  # Используем редирект для получения кода
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')

    return authorization_url

def authenticate_user_with_code(user_id, code):
    flow = Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'  # Нужен редирект URN
    flow.fetch_token(code=code)  # Получаем токен доступа с помощью кода
    creds = flow.credentials

    # Сохраняем токен
    token_file = f'token_{user_id}.pickle'
    with open(token_file, 'wb') as token:
        pickle.dump(creds, token)

    return creds  # Возвращаем учетные данные



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
            'timeZone': 'Europe/Moscow',  # Наш часовой пояс
        },
        'end': {
            'dateTime': end_time,
            'timeZone': 'Europe/Moscow',
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
    creds = authenticate_google(user_id)  # Аутентификация
    meetings = get_meetings_for_user(user_id)  # Получаем встречи из базы данных
    
    # Состояние для хранения событий из Google Calendar
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

def token_exists(bot, message, user_id):
    token_file = f'token_{user_id}.pickle'

    # Проверяем, существует ли токен
    if not os.path.exists(token_file):
        bot.send_message(message.chat.id, 
                         "Пожалуйста, пройдите аутентификацию, прежде чем использовать эту команду. \n"
                         "Введите /authenticate для начала процесса.")
        return False
    return True