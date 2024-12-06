import sqlite3
import io
import datetime
import matplotlib
import matplotlib.pyplot as plt
from .utils import get_db_connection

matplotlib.use('Agg')  # Используем бекенд без GUI

def calculate_average_meeting_duration(first_day, last_day):
    """Вычисляет среднюю длительность встреч за заданный период."""
    conn = get_db_connection('bot_database.db')
    cursor = conn.cursor()

    # Запрос на получение начала и конца встреч за указанный период
    cursor.execute("""
        SELECT start_time, end_time FROM meetings
        WHERE start_time BETWEEN ? AND ?
    """, (first_day.strftime('%Y-%m-%d'), last_day.strftime('%Y-%m-%d')))

    meetings = cursor.fetchall()
    
    total_duration = datetime.timedelta()
    meeting_count = len(meetings)

    for start, end in meetings:
        start_dt = datetime.datetime.strptime(start, "%Y-%m-%d %H:%M:%S")
        end_dt = datetime.datetime.strptime(end, "%Y-%m-%d %H:%M:%S")
        total_duration += (end_dt - start_dt)
    
    close_connection(conn)
    average_duration_minutes = (total_duration.total_seconds() / 60) / meeting_count if meeting_count > 0 else 0
    total_duration = (total_duration.total_seconds() / 60) 

    return round(average_duration_minutes, 1), meeting_count, int(total_duration)

def generate_monthly_stats_plot(bot, message):
    """Генерирует график с количеством встреч за текущий месяц."""
    conn = get_db_connection('bot_database.db')
    cursor = conn.cursor()

    # Определяем первый и последний день текущего месяца
    first_day_of_month = datetime.datetime.now().replace(day=1)
    last_day_of_month = (first_day_of_month + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)

    # Получаем среднюю длительность встреч
    average_meeting_duration, meeting_count, total_meeting_time = calculate_average_meeting_duration(first_day_of_month, last_day_of_month)

    # Запрос на получение количества встреч по дням
    cursor.execute("""
        SELECT DATE(start_time), COUNT(*) FROM meetings
        WHERE start_time BETWEEN ? AND ?
        GROUP BY DATE(start_time)
    """, (first_day_of_month.strftime('%Y-%m-%d'), last_day_of_month.strftime('%Y-%m-%d')))
    
    meetings_per_day = cursor.fetchall()
    
    # Подсчет количества встреч по дням
    days = [0] * (last_day_of_month.day)  # Список для 31 дня
    for meeting_date, count in meetings_per_day:
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
    
    
    bot.send_photo(message.chat.id, img.getvalue(), caption=f"Количество встреч за текущий месяц по дням.\nВаше общее количество встреч: {meeting_count}.\nВаше среднее время встречи: {average_meeting_duration} минут.\nВаше общее время встреч: {total_meeting_time} минут.")

def close_connection(conn):
    """Закрывает соединение с базой данных."""
    conn.close()
