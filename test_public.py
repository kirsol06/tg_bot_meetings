import pytest
import sqlite3
from unittest.mock import Mock
from commands.utils import add_meeting, get_db_connection
import os

# Тестируем функции из meetings:
def test_add_meeting():
    bot_mock = Mock()
    title = 'Встреча'
    start_time = '2023-10-01 10:00:00'
    end_time = '2023-10-01 11:00:00'
    description = 'Описание'
    usernames = ['alice', 'bob']

    # Вызываем добавление встречи с использованием db_connection
    add_meeting(bot_mock, 'test_database.db', title, start_time, end_time, description, usernames)

    # Проверяем, что встреча добавилась
    conn = get_db_connection('test_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM meetings WHERE title = ?', (title,))
    meeting = cursor.fetchone()

    assert meeting is not None
    assert meeting[1] == title
    assert meeting[2] == start_time
    assert meeting[3] == end_time
    assert meeting[4] == description

    # Проверяем участников
    cursor.execute('SELECT * FROM participants WHERE meeting_id = ?', (meeting[0],))
    participants = cursor.fetchall()
    assert len(participants) == 2  # Должно быть 2 участника

    user_ids = [p[2] for p in participants]
    assert all(user_id in [1, 2] for user_id in user_ids)

