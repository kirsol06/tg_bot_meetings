import os
import pickle
import sqlite3
import requests
from datetime import datetime, timezone, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

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


def create_event(creds, meeting):
    """Создание события в Google Calendar."""
    url = 'https://www.googleapis.com/calendar/v3/calendars/primary/events'
    
    # Структура события
    event = {
        'summary': meeting[1],  # Название
        'start': {
            'dateTime': datetime.strptime(meeting[3], "%Y-%m-%d %H:%M:%S").isoformat() ,  # Время начала
            'timeZone': 'Europe/Moscow',  # Установите свой часовой пояс
        },
        'end': {
            'dateTime': datetime.strptime(meeting[4], "%Y-%m-%d %H:%M:%S").isoformat() ,  # Время окончания
            'timeZone': 'Europe/Moscow',  # Установите свой часовой пояс
        },
        'description': meeting[2],  # Описание
    }

    headers = {
        'Authorization': f'Bearer {creds.token}',  # Используем токен для авторизации
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, json=event)  # Отправляем POST запрос

    if response.status_code == 200:
        print(f"Событие '{meeting[1]}' успешно добавлено в Google Calendar.")
    else:
        print(f'Ошибка при добавлении события: {response.json()}')