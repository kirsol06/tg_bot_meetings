import datetime
from threading import Timer
from .utils import get_db_connection

sent_reminders = {}

def send_reminders(bot):
    """Отправка напоминаний участникам встреч за 30 минут до их начала."""
    conn = get_db_connection('bot_database')
    cursor = conn.cursor()

    now = datetime.datetime.now()
    reminder_time = now + datetime.timedelta(minutes=30)

    cursor.execute("""
        SELECT m.id, m.title, m.start_time, m.end_time, m.description, p.user_id
        FROM meetings m
        JOIN participants p ON m.id = p.meeting_id
        WHERE m.start_time BETWEEN ? AND ?
    """, (now, reminder_time))

    meetings = cursor.fetchall()
    conn.close()

    for meeting_id, title, start_time, end_time, description, user_id in meetings:
        if meeting_id not in sent_reminders:
            message = (
                f"🔔 Напоминание о встрече!\n"
                f"Название: {title}\n"
                f"Начало: {start_time}\n"
                f"Описание: {description}\n"
            )
            bot.send_message(user_id, message)
            sent_reminders[meeting_id] = True  # Отмечаем, что напоминание отправлено

def schedule_reminder_check(bot):
    """Запланируйте проверку напоминаний каждые 60 секунд."""
    send_reminders(bot)
    Timer(60, schedule_reminder_check, [bot]).start()


