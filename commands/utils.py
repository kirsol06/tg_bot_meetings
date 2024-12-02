import sqlite3
import datetime

def get_db_connection():
    """Открывает и возвращает новое соединение с базой данных."""
    return sqlite3.connect('bot_database.db')

def get_meetings_for_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Получаем текущее время
    now = datetime.datetime.now()

    # Извлечение meeting_id из participants, а затем выборка будущих встреч
    cursor.execute("""
        SELECT m.id, m.title, m.start_time, m.end_time, m.description 
        FROM meetings m
        JOIN participants p ON m.id = p.meeting_id
        WHERE p.user_id = ? AND m.start_time > ?
    """, (user_id, now))

    meetings = cursor.fetchall()
    conn.close()
    return meetings


def users_are_free(usernames, start_time, end_time):
    """Проверяет, свободны ли пользователи в заданном временном интервале."""
    unavailable_users = []
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for username in usernames:
            cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            if user:
                user_id = user[0]
                meetings = get_meetings_for_user(user_id)
                for meeting in meetings:
                
                    meeting_start = datetime.datetime.strptime(meeting[2], "%Y-%m-%d %H:%M:%S")
                    meeting_end = datetime.datetime.strptime(meeting[3], "%Y-%m-%d %H:%M:%S")
                    if (start_time < meeting_end and end_time > meeting_start):
                        unavailable_users.append(username)
                        break
    return unavailable_users

def find_next_free_slot(meetings, duration, start_time):
    """Находит следующее свободное время для встречи с указанной продолжительностью."""
    next_free_time = start_time  # Предполагаем, что первая проверка через час

    while True:
        is_free = True
        meeting_end_time = next_free_time + datetime.timedelta(minutes=duration)  # Длительность встречи
        for meeting in meetings:
            start_time = datetime.datetime.strptime(meeting[2], "%Y-%m-%d %H:%M:%S")
            end_time = datetime.datetime.strptime(meeting[3], "%Y-%m-%d %H:%M:%S")

            if next_free_time < end_time and meeting_end_time > start_time:
                is_free = False
                break

        if is_free:
            return next_free_time

        next_free_time += datetime.timedelta(minutes=15)  # Проверяем следующий интервал каждые 15 минут
    
def all_usernames_exist(usernames):
    """Проверяет, существуют ли все юзернеймы в базе данных."""
    conn = get_db_connection()
    cursor = conn.cursor()

    existing_usernames = set()
    cursor.execute('SELECT username FROM users')  # Например, предположим, что в таблице users есть колонка username
    for row in cursor.fetchall():
        existing_usernames.add(row[0])  # Собираем существующие юзернеймы в множество

    conn.close()
    # Проверка, если все переданные юзернеймы существуют в базе данных
    return all(username in existing_usernames for username in usernames)

def send_meeting_notification(bot, user_id, title, start_time, end_time, description):
    """Отправка уведомления пользователю о назначенной встрече."""
    message = (
        f"🔥 Вам назначена новая встреча!\n"
        f"Название: {title}\n"
        f"Дата и время начала: {start_time[:-3]}\n"
        f"Дата и время окончания: {end_time[:-3]}\n"
        f"Описание: {description}\n"
    )
    bot.send_message(user_id, message)


def add_meeting(bot, title: str, start_time: str, end_time: str, description: str, usernames: list):
    """Добавление встречи в базу данных."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('INSERT INTO meetings (title, start_time, end_time, description) VALUES (?, ?, ?, ?)',
                   (title, start_time, end_time, description))
    meeting_id = cursor.lastrowid  # Получаем ID новосозданной встречи

    # Записываем участников в таблицу participants
    for username in usernames:
        cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        if user:
            user_id = user[0]
            cursor.execute('INSERT INTO participants (meeting_id, user_id) VALUES (?, ?)', (meeting_id, user_id))
            send_meeting_notification(bot, user_id, title, start_time, end_time, description)

    conn.commit()
    conn.close()  # Закрываем соединение после операции


def delete_meeting_handler(bot, message):
    """Удаление встречи из базы данных."""
    if message.text.strip() == '/cancel':
        return
    try:
        meeting_id = int(message.text)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Проверка на существование встречи
        cursor.execute('SELECT * FROM meetings WHERE id = ?', (meeting_id,))
        meeting = cursor.fetchone()

        if not meeting:
            bot.send_message(message.chat.id, 'Встреча с таким ID не найдена.')
            return

        cursor.execute('DELETE FROM meetings WHERE id = ?', (meeting_id,))
        cursor.execute('DELETE FROM participants WHERE meeting_id = ?', (meeting_id,))  # Удаляем участников
        conn.commit()

        bot.send_message(message.chat.id, 'Встреча успешно удалена!')
        conn.close()

    except ValueError:
        bot.send_message(message.chat.id, 'Введите корректный ID встречи.')
    except Exception as e:
        bot.send_message(message.chat.id, 'Ошибка при удалении встречи. Убедитесь, что такая встреча существует.')
        print(f"Ошибка при удалении встречи: {e}")  # Для отладки
        