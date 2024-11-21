import sqlite3
import telebot
import datetime
import matplotlib.pyplot as plt
import numpy as np
import io

# Инициализация бота и базы данных
bot = telebot.TeleBot("7835145744:AAFKKZVxvkpWiqKREJ0HDrDcsi4OZb57ZKE")  # Замените 'your_token' на токен вашего бота
conn = sqlite3.connect('bot_database.db', check_same_thread=False)
cursor = conn.cursor()

# Функции для работы с базой данных
def db_table_val(user_id: int, username: str):
    cursor.execute('INSERT INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
    conn.commit()

def add_meeting(title: str, start_time: str, end_time: str, description: str, usernames: list):
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
    conn.commit()

def get_all_meetings():
    # Получаем все встречи из базы данных и их участников
    cursor.execute('SELECT m.id, m.title, m.start_time, m.end_time, m.description FROM meetings m')
    meetings = cursor.fetchall()

    all_meetings = []
    for meeting in meetings:
        meeting_id = meeting[0]
        title = meeting[1]
        start_time = meeting[2]
        end_time = meeting[3]
        description = meeting[4]

        # Получаем участников для этой встречи
        cursor.execute('SELECT u.username FROM participants p JOIN users u ON p.user_id = u.user_id WHERE p.meeting_id = ?', (meeting_id,))
        participants = cursor.fetchall()
        participants_list = [username[0] for username in participants]

        all_meetings.append((meeting_id, title, start_time, end_time, description, participants_list))

    return all_meetings

def get_meetings_for_user(user_id):
    # Получаем все встречи для конкретного пользователя
    cursor.execute('SELECT m.id, m.title, m.start_time, m.end_time, m.description FROM meetings m ' +
                   'JOIN participants p ON m.id = p.meeting_id WHERE p.user_id = ?', (user_id,))
    return cursor.fetchall()


@bot.message_handler(commands=['view_meetings'])
def view_meetings_command(message):
    # Получаем все встречи
    meetings = get_all_meetings()
    user_id = message.from_user.id

    if not meetings:
        bot.send_message(message.chat.id, 'В базе данных нет запланированных встреч.')
    else:
        response = 'Все запланированные встречи:\n'
        for meeting in meetings:
            meeting_id, title, start_time, end_time, description, participants = meeting
            participants_str = ', '.join(participants) if participants else 'Нет участников'
            response += f"ID: {meeting_id}, Название: {title}, Дата начала: {start_time}, Дата окончания: {end_time}, Описание: {description}, Участники: {participants_str}\n"
        
        # Выводим все встречи
        bot.send_message(message.chat.id, response)

        # Получаем встречи для данного пользователя
        user_meetings = get_meetings_for_user(user_id)

        if not user_meetings:
            bot.send_message(message.chat.id, 'У вас нет запланированных встреч.')
        else:
            user_response = '\nВаши запланированные встречи:\n'
            for meeting in user_meetings:
                meeting_id, title, start_time, end_time, description = meeting
                user_response += f"ID: {meeting_id}, Название: {title}, Дата начала: {start_time}, Дата окончания: {end_time}, Описание: {description}\n"
            bot.send_message(message.chat.id, user_response)
            
def users_are_free(usernames, start_time, end_time):
    unavailable_users = []
    for username in usernames:
        cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        if user:
            user_id = user[0]
            meetings = get_all_meetings_for_user(user_id)
            for meeting in meetings:
                meeting_start = datetime.datetime.strptime(meeting[2], "%Y-%m-%d %H:%M:%S")
                meeting_end = datetime.datetime.strptime(meeting[3], "%Y-%m-%d %H:%M:%S")
                if (start_time < meeting_end and end_time > meeting_start):
                    unavailable_users.append(username)
                    break
    return unavailable_users

def get_all_meetings_for_user(user_id):
    # Получаем все встречи для конкретного пользователя
    cursor.execute('SELECT m.id, m.title, m.start_time, m.end_time, m.description FROM meetings m ' +
                   'JOIN participants p ON m.id = p.meeting_id WHERE p.user_id = ?', (user_id,))
    return cursor.fetchall()

def find_next_free_slot(meetings, duration=60):
    one_hour = datetime.timedelta(hours=1)
    current_time = datetime.datetime.now().replace(second=0, microsecond=0)
    next_free_time = current_time + one_hour  # Предполагаем, что первая проверка через час

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

def generate_daily_stats_plot():
    # Получаем сегодняшние встречи
    today = datetime.date.today()
    cursor.execute("""
        SELECT start_time 
        FROM meetings 
        WHERE DATE(start_time) = ?
    """, (today,))
    meetings = cursor.fetchall()

    # Подсчитываем количество встреч по часам
    hours = np.zeros(24)  # 24 часа
    for meeting in meetings:
        start_hour = datetime.datetime.strptime(meeting[0], "%Y-%m-%d %H:%M:%S").hour
        hours[start_hour] += 1

    # Создание графика
    plt.figure(figsize=(10, 6))
    plt.bar(range(24), hours, color='blue', alpha=0.7)
    plt.title('Загруженность встречами за сегодняшний день')
    plt.xlabel('Часы')
    plt.ylabel('Количество встреч')
    plt.xticks(range(24))
    
    # Сохранение графика в память
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()  # Закрываем фигуру после сохранения
    return img

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Добро пожаловать! Введите /register, чтобы добавиться в базу данных. Введите /help , чтобы посмотреть доступные команды')

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = (
        "Доступные команды:\n"
        "\n"
        "/start - Начать взаимодействие с ботом.\n"
        "\n"
        "/register - Зарегистрироваться в базе данных.\n"
        "\n"
        "/set_schedule_meeting - Запланировать встречу на определенное время.\n"
        "   Используйте формат: название, дата (YYYY-MM-DD), время начала (HH:MM), "
        "время окончания (HH:MM), описание, участники (username через запятую).\n"
        "\n"
        "/set_free_meeting - Запланировать встречу на свободное время.\n"
        "\n"
        "/view_meetings - Посмотреть все запланированные встречи на текущей неделе.\n"
        "\n"
        "/delete_meeting - Удалить встречу.\n"
        "\n"
        "/stats - Показать статистику встреч и визуализацию загруженности.\n"
    )
    bot.send_message(message.chat.id, help_text)
    
@bot.message_handler(commands=['register'])
def register_user(message):
    us_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (us_id,))
    if cursor.fetchone() is not None:
        bot.send_message(message.chat.id, 'Вы уже зарегистрированы в базе данных.')
    else:
        db_table_val(user_id=us_id, username=username)
        bot.send_message(message.chat.id, 'Вы успешно добавлены в базу данных!')

@bot.message_handler(commands=['set_schedule_meeting'])
def set_schedule_meeting(message):
    bot.send_message(message.chat.id, 'Введите данные для встречи в следующем формате:\n'
                                        'Название, дата (YYYY-MM-DD), время начала (HH:MM), время окончания (HH:MM), описание, участники (username через запятую).')
    bot.register_next_step_handler(message, save_meeting)

def save_meeting(message):
    try:
        data = message.text.split(',')
        title = data[0].strip()
        date = data[1].strip()
        start_time_str = data[2].strip()
        end_time_str = data[3].strip()
        description = data[4].strip()
        usernames = [name.strip() for name in data[5:]]  # Пользователи

        start_time = datetime.datetime.strptime(f"{date} {start_time_str}", "%Y-%m-%d %H:%M")
        end_time = datetime.datetime.strptime(f"{date} {end_time_str}", "%Y-%m-%d %H:%M")

        unavailable_users = users_are_free(usernames, start_time, end_time)

        if unavailable_users:
            response_msg = f'Не удалось запланировать встречу, так как следующие пользователи заняты: {", ".join(unavailable_users)}'
            bot.send_message(message.chat.id, response_msg)
        else:
            add_meeting(title=title, start_time=start_time.strftime("%Y-%m-%d %H:%M:%S"), 
                        end_time=end_time.strftime("%Y-%m-%d %H:%M:%S"), description=description, 
                        usernames=usernames)
            bot.send_message(message.chat.id, 'Встреча успешно запланирована!')
    except Exception as e:
        bot.send_message(message.chat.id, 'Ошибка в формате данных. Пожалуйста, повторите ввод.')

@bot.message_handler(commands=['set_free_meeting'])
def set_free_meeting(message):
    bot.send_message(message.chat.id, 'Введите usernames участников, которых вы хотите пригласить (через запятую):')
    bot.register_next_step_handler(message, find_free_slot)

def find_free_slot(message):
    usernames = [username.strip() for username in message.text.split(',')]
    all_meetings = []

    for username in usernames:
        cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        if user:
            user_id = user[0]
            meetings = get_all_meetings_for_user(user_id)
            all_meetings.extend(meetings)

    next_free_slot = find_next_free_slot(all_meetings)

    if next_free_slot:
        response = f'Ближайшее свободное время для встречи: {next_free_slot.strftime("%Y-%m-%d %H:%M")}. ' \
                   'Хотите запланировать встречу на это время? (да/нет)'
        bot.send_message(message.chat.id, response)
        bot.register_next_step_handler(message, lambda m: schedule_meeting(m, next_free_slot, usernames))
    else:
        bot.send_message(message.chat.id, 'Нет доступного времени для встречи.')

def schedule_meeting(message, next_free_slot, usernames):
    if message.text.lower() == 'да':
        bot.send_message(message.chat.id, 'Введите название встречи:')
        bot.register_next_step_handler(message, lambda m: get_meeting_title(m, next_free_slot, usernames))
    else:
        bot.send_message(message.chat.id, 'Встреча не была запланирована.')

def get_meeting_title(message, next_free_slot, usernames):
    title = message.text
    bot.send_message(message.chat.id, 'Введите описание встречи:')
    bot.register_next_step_handler(message, lambda m: create_meeting(m, title, next_free_slot, usernames))
    
def create_meeting(message, title, next_free_slot, usernames):
    description = message.text
    end_time = next_free_slot + datetime.timedelta(hours=1)  # Длительность встречи 1 час

    # Добавление встречи и участников
    add_meeting(title=title, start_time=next_free_slot.strftime("%Y-%m-%d %H:%M:%S"),
                end_time=end_time.strftime("%Y-%m-%d %H:%M:%S"), description=description, usernames=usernames)
    bot.send_message(message.chat.id, 'Встреча успешно запланирована!')

@bot.message_handler(commands=['delete_meeting'])
def delete_meeting_command(message):
    bot.send_message(message.chat.id, 'Введите ID встречи, которую хотите удалить:')
    bot.register_next_step_handler(message, delete_meeting_handler)

def delete_meeting_handler(message):
    try:
        meeting_id = int(message.text)
        cursor.execute('DELETE FROM meetings WHERE id = ?', (meeting_id,))
        cursor.execute('DELETE FROM participants WHERE meeting_id = ?', (meeting_id,))  # Удаляем участников
        conn.commit()
        bot.send_message(message.chat.id, 'Встреча успешно удалена!')
    except ValueError:
        bot.send_message(message.chat.id, 'Введите корректный ID встречи.')
    except Exception as e:
        bot.send_message(message.chat.id, 'Ошибка при удалении встречи. Убедитесь, что такая встреча существует.')

@bot.message_handler(commands=['stats'])
def stats_command(message):
    plot_image = generate_daily_stats_plot()

    # Отправка графика пользователю
    bot.send_photo(message.chat.id, plot_image.getvalue(), caption='Загруженность встречами за сегодняшний день по часам.')

# Запуск бота
bot.polling(none_stop=True)