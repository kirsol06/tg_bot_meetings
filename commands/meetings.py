from .utils import  add_meeting, get_meetings_for_user, find_next_free_slot, all_usernames_exist, users_are_free, get_db_connection, delete_meeting_handler
import datetime

def set_schedule_meeting(bot, message):
    """Обработка команды для назначения встречи."""
    bot.send_message(message.chat.id, 'Введите дату и время начала встречи  в формате "YYYY-MM-DD HH:MM" (например, 2024-12-01 20:30).')
    bot.register_next_step_handler(message, lambda msg: process_start_time(bot, msg))

def process_start_time(bot, message):
    """Обработка времени начала встречи."""
    try:
        start_time_str = message.text.strip()
        start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")
        
        # Запрашиваем время конца встречи
        bot.send_message(message.chat.id, 'Введите время окончания встречи в формате НН:ММ (например, 21:30).')
        bot.register_next_step_handler(message, lambda msg: process_end_time(bot, msg, start_time))
        
    except ValueError:
        bot.send_message(message.chat.id, 'Ошибка. Пожалуйста, введите дату и время в правильном формате (YYYY-MM-DD HH:MM).')
        bot.register_next_step_handler(message, lambda msg: process_start_time(bot, msg))

def process_end_time(bot, message, start_time):
    """Обработка времени окончания встречи."""
    try:
        end_time_str = message.text.strip()
        end_time = datetime.datetime.strptime(end_time_str, "%H:%M")
        
        # Создаем полное время окончания, использовав дату начала
        end_time = end_time.replace(year=start_time.year, month=start_time.month, day=start_time.day)
        
        if end_time <= start_time:
            bot.send_message(message.chat.id, 'Ошибка. Время окончания встречи должно быть позже времени начала. Попробуйте снова.')
            bot.register_next_step_handler(message, lambda msg: process_end_time(bot, msg, start_time))
            return

        # Запрашиваем юзернеймы участников
        bot.send_message(message.chat.id, 'Введите юзернеймы участников (через запятую). Если вы тоже участник, то свой юзернейм тоже надо ввести')
        bot.register_next_step_handler(message, lambda msg: process_usernames(bot, msg, start_time, end_time))

    except ValueError:
        bot.send_message(message.chat.id, 'Ошибка. Пожалуйста, введите время окончания в правильном формате (HH:MM).')
        bot.register_next_step_handler(message, lambda msg: process_end_time(bot, msg, start_time))

def process_usernames(bot, message, start_time, end_time):
    """Обработка юзернеймов участников встречи."""
    usernames = [name.strip() for name in message.text.split(',')]
    
    # Проверка наличия юзернеймов в базе данных
    if not all_usernames_exist(usernames):
        bot.send_message(message.chat.id, 'Некоторые из указанных юзернеймов не найдены в базе данных. Пожалуйста, повторите ввод.')
        bot.register_next_step_handler(message, lambda msg: process_usernames(bot, msg, start_time, end_time))
        return

    # Проверка доступности участников
    unavailable_users = users_are_free(usernames, start_time, end_time)

    if unavailable_users:
        response_msg = f'Не удалось запланировать встречу, так как следующие пользователи заняты: {", ".join(unavailable_users)}'
        bot.send_message(message.chat.id, response_msg)
        return

    # Запрашиваем название встречи
    bot.send_message(message.chat.id, 'Введите название встречи.')
    bot.register_next_step_handler(message, lambda msg: process_meeting_title(bot, msg, start_time, end_time, usernames))

def process_meeting_title(bot, message, start_time, end_time, usernames):
    """Обработка названия встречи."""
    title = message.text.strip()

    # Запрашиваем описание встречи
    bot.send_message(message.chat.id, 'Введите описание встречи.')
    bot.register_next_step_handler(message, lambda msg: save_meeting(bot, msg, title, start_time, end_time, usernames))

def save_meeting(bot, message, title, start_time, end_time, usernames):
    """Сохранение данных о встрече в базу данных."""
    description = message.text.strip()

    try:
        add_meeting(bot, title=title,
                    start_time=start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    end_time=end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    description=description,
                    usernames=usernames)

        bot.send_message(message.chat.id, 'Встреча успешно запланирована!')
    except Exception as e:
        bot.send_message(message.chat.id, 'Ошибка при сохранении встречи. Пожалуйста, попробуйте снова.')
        print(f"Ошибка при сохранении встречи: {e}")  # Для отладки

def view_meetings(bot, message):
    """Отображение запланированных встреч для пользователя."""
    user_id = message.from_user.id
    user_meetings = get_meetings_for_user(user_id)

    if not user_meetings:
        bot.send_message(message.chat.id, 'У вас нет запланированных встреч.')
    else:
        user_response = '\nВаши предстоящие  запланированные встречи:\n \n'
        for meeting_id, title, start_time, end_time, description in user_meetings:
            user_response += f"ID: {meeting_id}; \n Название: {title}, \n Дата начала: {start_time[:-3]}, \n Дата окончания: {end_time[:-3]}, \n Описание: {description} \n \n"
        bot.send_message(message.chat.id, user_response)


def set_free_meeting(bot, message):
    """Обработка команды для нахождения свободного времени для встречи."""
    bot.send_message(message.chat.id, 'Введите usernames участников, которых вы хотите пригласить (через запятую). Если вы тоже участник встречи, то свой юзернейм тоже надо ввести')
    bot.register_next_step_handler(message, lambda msg: add_free_users(bot, msg))

def add_free_users(bot, message):
    """Поиск ближайшего свободного слота для встречи."""
    usernames = [username.strip() for username in message.text.split(',')]
    if not all_usernames_exist(usernames):
        bot.send_message(message.chat.id, 'Некоторые из указанных юзернеймов не найдены в базе данных. Пожалуйста, повторите ввод.')
        bot.register_next_step_handler(message, lambda msg: add_free_users(bot, msg))
        return
    all_meetings = []
    conn = get_db_connection()
    cursor = conn.cursor()

    for username in usernames:
        cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        if user:
            user_id = user[0]
            meetings = get_meetings_for_user(user_id)
            all_meetings.extend(meetings)
    
    conn.close() 
    
    bot.send_message(message.chat.id, 'Введите желаемую дату (YYYY-MM-DD), самое раннее время начала (HH-MM) и длительность встречи в минутах через запятую (например: 2024-12-03, 12:00, 50)')
    bot.register_next_step_handler(message, lambda msg: find_free_slot(bot, all_meetings, usernames, msg))

def find_free_slot(bot, all_meetings, usernames, message):
    try:
        data = message.text.split(',')
        date = data[0].strip()
        time = data[1].strip()
        duration = int(data[2].strip())
        datetime_str = f"{date} {time}"

        start_time = datetime.datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
        
        next_free_slot = find_next_free_slot(all_meetings, duration, start_time)

        if next_free_slot:
            response = f'Ближайшее свободное время для встречи: {next_free_slot.strftime("%Y-%m-%d %H:%M")}. ' \
                    'Хотите запланировать встречу на это время? (да/нет)'
            bot.send_message(message.chat.id, response)
            bot.register_next_step_handler(message, lambda msg: schedule_meeting(bot, msg, next_free_slot, usernames, duration))
    except ValueError:
        bot.send_message(message.chat.id, 'Ошибка. Пожалуйста, введите дату и время в правильном формате (YYYY-MM-DD HH:MM).')
        bot.register_next_step_handler(message, lambda msg: find_free_slot(bot, all_meetings, usernames, msg))

def schedule_meeting(bot, message, next_free_slot, usernames, duration):
    """Обработка согласия на назначение встречи."""
    if message.text.lower() == 'да':
        bot.send_message(message.chat.id, 'Введите название встречи:')
        bot.register_next_step_handler(message, lambda m: get_meeting_title(bot, m, next_free_slot, usernames, duration))
    else:
        bot.send_message(message.chat.id, 'Встреча не была запланирована.')

def get_meeting_title(bot, message, next_free_slot, usernames, duration):
    """Получение названия встречи."""
    title = message.text
    bot.send_message(message.chat.id, 'Введите описание встречи:')
    bot.register_next_step_handler(message, lambda m: create_meeting(bot, m, title, next_free_slot, usernames, duration))


def create_meeting(bot, message, title, next_free_slot, usernames, duration):
    """Создание новой встречи в базе данных."""
    description = message.text
    end_time = next_free_slot + datetime.timedelta(minutes=duration)  # Длительность встречи 1 час

    # Добавление встречи и участников
    add_meeting(bot, title=title, start_time=next_free_slot.strftime("%Y-%m-%d %H:%M:%S"),
                end_time=end_time.strftime("%Y-%m-%d %H:%M:%S"), description=description, usernames=usernames)
    bot.send_message(message.chat.id, 'Встреча успешно запланирована!')


def delete_meeting(bot, message):
    """Удаление встречи по ID."""
    bot.send_message(message.chat.id, 'Введите ID встречи, которую хотите удалить (чтобы узнать id встреч, используйте команду /view_meetings):')
    bot.register_next_step_handler(message, lambda msg: delete_meeting_handler(bot, msg))

