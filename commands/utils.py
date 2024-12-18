import sqlite3
import datetime

def get_db_connection():
    """Открывает и возвращает новое соединение с базой данных."""
    return sqlite3.connect('bot_database2.db')

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
                    if (start_time < meeting_end and end_time > meeting_start): # Ищем занятых пользователей и запоминаем
                        unavailable_users.append(username)
                        break
    return unavailable_users

def find_nearest_free_time(meetings, duration, start_time):
    """Находит следующее свободное время для встречи с указанной продолжительностью."""
    next_free_time = start_time 
    while True:
        is_free = True
        meeting_end_time = next_free_time + datetime.timedelta(minutes=duration)  # Длительность встречи
        for meeting in meetings:
            start_time = datetime.datetime.strptime(meeting[2], "%Y-%m-%d %H:%M:%S")
            end_time = datetime.datetime.strptime(meeting[3], "%Y-%m-%d %H:%M:%S")

            if next_free_time < end_time and meeting_end_time > start_time: # Проверяем, не накладывается ли время встреч
                is_free = False
                break

        if is_free: # Значит нашли тот самый слот
            return next_free_time

        next_free_time += datetime.timedelta(minutes=15)  # Проверяем следующий интервал каждые 15 минут
    
def all_usernames_exist(usernames):
    """Проверяет, существуют ли все юзернеймы в базе данных."""
    conn = get_db_connection()
    cursor = conn.cursor()

    existing_usernames = set()
    cursor.execute('SELECT username FROM users') 
    for row in cursor.fetchall():
        existing_usernames.add(row[0])  # Собираем существующие юзернеймы

    conn.close()
    # Проверка, если все введенные юзернеймы существуют в базе данных
    return all(username in existing_usernames for username in usernames)

def send_meeting_notification(bot, user_id, title, start_time, end_time, description):
    """Отправка уведомления пользователю о назначенной встрече."""
    start_time = start_time.split()
    s_time = start_time[1]
    s_date = start_time[0]
    s_date = s_date[8:] + '-' + s_date[5:7] + '-' + s_date[0:4]
    start_time = s_date + ' ' + s_time[:-3]

    end_time = end_time.split()
    e_time = end_time[1]
    e_date = end_time[0]
    e_date = e_date[8:] + '-' + e_date[5:7] + '-' + e_date[0:4]
    end_time = e_date + ' ' + e_time[:-3]
    
    message = (
        f"🔥 Вам назначена новая встреча!\n"
        f"Название: {title}\n"
        f"Дата и время начала: {start_time}\n"
        f"Дата и время окончания: {end_time}\n"
        f"Описание: {description}\n"
        f"Эта встреча появится в вашем гугл-календаре в течение минуты"
    )
    bot.send_message(user_id, message)



def add_meeting(bot, title: str, start_time: str, end_time: str, description: str, usernames: list):
    """Добавление встречи в базу данных."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('INSERT INTO meetings (title, start_time, end_time, description) VALUES (?, ?, ?, ?)',
                   (title, start_time, end_time, description))
    meeting_id = cursor.lastrowid  # Получаем ID новой встречи

    # Записываем участников в таблицу participants
    for username in usernames:
        cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        if user:
            user_id = user[0]
            cursor.execute('INSERT INTO participants (meeting_id, user_id) VALUES (?, ?)', (meeting_id, user_id))
            send_meeting_notification(bot, user_id, title, start_time, end_time, description)

    conn.commit()
    conn.close() 


def get_last_meeting_for_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Получаем текущее время
    now = datetime.datetime.now()

    # Извлечение встречи с самым большим id у участников
    cursor.execute("""
        SELECT m.id, m.title, m.start_time, m.end_time, m.description
        FROM meetings m
        WHERE m.id = (
            SELECT MAX(m.id)
            FROM meetings m
            JOIN participants p ON m.id = p.meeting_id
            WHERE p.user_id = ? AND m.start_time > ?
        )
    """, (user_id, now))

    meeting = cursor.fetchone()  # Получаем только одну запись с самым большим id
    conn.close()

    return meeting

def get_user_email(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT email FROM users WHERE user_id = ?", (user_id,))
    email = cursor.fetchone()
    
    conn.close()
    return email

def get_participants(meeting):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM participants WHERE meeting_id = ?", (meeting[0],))
    participants = cursor.fetchall()
    conn.close()

    return [pid[0] for pid in participants]  # Извлекаем user_id из кортежей

