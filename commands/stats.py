import sqlite3
import io
import datetime
import matplotlib
import matplotlib.pyplot as plt

matplotlib.use('Agg')  # Используем бекенд без GUI


def get_db_connection():
    """Открывает и возвращает новое соединение с базой данных."""
    return sqlite3.connect('bot_database.db')

def generate_monthly_stats_plot(bot, message):
    """Генерирует график с количеством встреч за текущий месяц."""
    conn = get_db_connection()
    cursor = conn.cursor()

    first_day_of_month = datetime.datetime.now().replace(day=1)
    last_day_of_month = (first_day_of_month + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)

    # Запрос на получение количества встреч по дням
    cursor.execute("""
        SELECT DATE(start_time), COUNT(*) FROM meetings
        WHERE start_time BETWEEN ? AND ?
        GROUP BY DATE(start_time)
    """, (first_day_of_month.strftime('%Y-%m-%d'), last_day_of_month.strftime('%Y-%m-%d')))

    meetings = cursor.fetchall()

    # Подсчитываем количество встреч по дням
    days = [0] * (last_day_of_month.day)  # Список для 31 дня
    for meeting_date, count in meetings:
        day = datetime.datetime.strptime(meeting_date, "%Y-%m-%d").day
        days[day - 1] = count  # Заполняем количество встреч за каждый день

    # Создание графика
    plt.figure(figsize=(10, 6))
    plt.bar(range(1, last_day_of_month.day + 1), days, color='blue', alpha=0.7)
    plt.title('Количество встреч за текущий месяц')
    plt.xlabel('Дни месяца')
    plt.ylabel('Количество встреч')
    plt.xticks(range(1, last_day_of_month.day + 1))

    # Сохранение графика в память
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()  # Закрываем фигуру после сохранения

    close_connection(conn)
    bot.send_photo(message.chat.id, img.getvalue(), caption='Количество встреч за текущий месяц по дням.')

def close_connection(conn):
    """Закрывает соединение с базой данных."""
    conn.close()
