# tests/conftest.py

import pytest
import sqlite3
import os

@pytest.fixture
def db():
    # Создание тестовой базы данных
    test_db = 'test_bot_database.db'
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()

    # Здесь можно создать схемы таблиц, например:
    cursor.execute('''
        CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT)
    ''')
    cursor.execute('''
        CREATE TABLE meetings (id INTEGER PRIMARY KEY, title TEXT, description TEXT, start_time DATETIME, end_time DATETIME)
    ''')
    cursor.execute('''
        CREATE TABLE participants (id INTEGER PRIMARY KEY, meeting_id INTEGER, user_id INTEGER, status TEXT)
    ''')

    conn.commit()

    yield conn  # Возвращаем соединение

    # Удаляем тестовую базу данных после теста
    conn.close()
    os.remove(test_db)
