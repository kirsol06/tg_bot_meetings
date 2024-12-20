from .utils import *
from .help import create_keyboard, create_cancel_keyboard, create_yes_no_keyboard
import datetime

def set_schedule_meeting(bot, message):
    """Обработка команды для назначения встречи на определенное время."""
    bot.send_message(message.chat.id, 'Введите дату и время начала встречи в формате "DD-MM-YYYY HH:MM" (например, 01-12-2024 20:30).', reply_markup=create_cancel_keyboard())
    bot.register_next_step_handler(message, lambda msg: process_scheduled_start_time(bot, msg)) # следующий шаг - функция process_scheduled_start_time

def process_scheduled_start_time(bot, message):
    """Обработка времени начала встречи."""
    if message.text.strip() == '/cancel': # Оставляем на каждом шаге возможность отменить создание встречи
        keyboard = create_keyboard() 
        bot.send_message(message.chat.id, 'Отмена', reply_markup=keyboard)
        return
    try:
        start_time_str = message.text.strip()
        start_time = datetime.datetime.strptime(start_time_str, "%d-%m-%Y %H:%M")
        
        # Запрашиваем длительность встречи
        bot.send_message(message.chat.id, 'Введите длительность встречи в минутах.', reply_markup=create_cancel_keyboard())
        bot.register_next_step_handler(message, lambda msg: process_scheduled_duration(bot, msg, start_time))
        
    except ValueError:
        bot.send_message(message.chat.id, 'Ошибка. Пожалуйста, введите дату и время в правильном формате.', reply_markup=create_cancel_keyboard())
        bot.register_next_step_handler(message, lambda msg: process_scheduled_start_time(bot, msg))

def process_scheduled_duration(bot, message, start_time):
    """Обработка длительности встречи"""
    if message.text.strip() == '/cancel':
        keyboard = create_keyboard() 
        bot.send_message(message.chat.id, 'Отмена', reply_markup=keyboard)
        return
    try:
        duration = int(message.text.strip())
        end_time = start_time + datetime.timedelta(minutes=duration)
        
        # Создаем полное время окончания, использовав дату начала
        end_time = end_time.replace(year=start_time.year, month=start_time.month, day=start_time.day)
        
        if end_time <= start_time:
            bot.send_message(message.chat.id, 'Ошибка. Время окончания встречи должно быть позже времени начала. Попробуйте снова.', reply_markup=create_cancel_keyboard())
            bot.register_next_step_handler(message, lambda msg: process_scheduled_duration(bot, msg, start_time))
            return

        # Запрашиваем юзернеймы участников
        bot.send_message(message.chat.id, 'Введите юзернеймы участников (через запятую). Если вы тоже участник, то свой юзернейм тоже надо ввести \n ', reply_markup=create_cancel_keyboard())
        bot.register_next_step_handler(message, lambda msg: process_usernames(bot, msg, start_time, end_time))

    except ValueError:
        bot.send_message(message.chat.id, 'Ошибка. Пожалуйста, введите время в правильном формате.', reply_markup=create_cancel_keyboard())
        bot.register_next_step_handler(message, lambda msg: process_scheduled_duration(bot, msg, start_time))

def process_usernames(bot, message, start_time, end_time):
    """Обработка юзернеймов участников встречи."""
    if message.text.strip() == '/cancel':
        keyboard = create_keyboard() 
        bot.send_message(message.chat.id, 'Отмена', reply_markup=keyboard)
        return
    usernames = [name.strip() for name in message.text.split(',')]
    
    # Проверка наличия юзернеймов в базе данных
    if not all_usernames_exist(usernames):
        bot.send_message(message.chat.id, 'Некоторые из указанных юзернеймов не найдены в базе данных. Пожалуйста, повторите ввод.', reply_markup=create_cancel_keyboard())
        bot.register_next_step_handler(message, lambda msg: process_usernames(bot, msg, start_time, end_time))
        return

    # Проверка доступности участников
    unavailable_users = users_are_free(usernames, start_time, end_time)
    if unavailable_users:
        response_msg = f'Не удалось запланировать встречу, так как следующие пользователи заняты: {", ".join(unavailable_users)}'
        keyboard = create_keyboard()
        bot.send_message(message.chat.id, response_msg, reply_markup=keyboard)
        return

    # Запрашиваем название встречи
    bot.send_message(message.chat.id, 'Введите название встречи.', reply_markup=create_cancel_keyboard())
    bot.register_next_step_handler(message, lambda msg: process_scheduled_meeting_title(bot, msg, start_time, end_time, usernames))

def process_scheduled_meeting_title(bot, message, start_time, end_time, usernames):
    """Обработка названия встречи."""
    if message.text.strip() == '/cancel':
        keyboard = create_keyboard() 
        bot.send_message(message.chat.id, 'Отмена', reply_markup=keyboard)
        return
    title = message.text.strip()

    # Запрашиваем описание встречи
    bot.send_message(message.chat.id, 'Введите описание встречи.', reply_markup=create_cancel_keyboard())
    bot.register_next_step_handler(message, lambda msg: save_scheduled_meeting(bot, msg, title, start_time, end_time, usernames))

def save_scheduled_meeting(bot, message, title, start_time, end_time, usernames):
    """Сохранение данных о встрече в базу данных."""
    if message.text.strip() == '/cancel':
        keyboard = create_keyboard() 
        bot.send_message(message.chat.id, 'Отмена', reply_markup=keyboard)
        return
    description = message.text.strip()

    try:
        add_meeting(bot, title=title,
                    start_time=start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    end_time=end_time.strftime("%Y-%m-%d %H:%M:%S"),
                    description=description,
                    usernames=usernames)
        bot.send_message(message.chat.id, 'Встреча успешно запланирована!', reply_markup = create_keyboard())

    except Exception as e:
        bot.send_message(message.chat.id, 'Ошибка при сохранении встречи. Пожалуйста, попробуйте снова.', reply_markup=create_cancel_keyboard())
        print(f"Ошибка при сохранении встречи: {e}")  # Для отладки
 
def view_meetings(bot, message):
    """Отображение запланированных встреч для пользователя."""
    user_id = message.from_user.id
    user_meetings = get_meetings_for_user(user_id)
    
    # Если у пользователя нет встреч 
    if not user_meetings:
        bot.send_message(message.chat.id, 'У вас нет запланированных встреч.', reply_markup = create_keyboard())
    # Если есть
    else:
        user_response = 'Ваши предстоящие  запланированные встречи:\n \n'
        for meeting_id, title, start_time, end_time, description in user_meetings:
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
            
            user_response += f"ID: {meeting_id}; \n Название: {title}, \n Дата начала: {start_time}, \n Дата окончания: {end_time}, \n Описание: {description} \n \n"
        bot.send_message(message.chat.id, user_response, reply_markup = create_keyboard())


def set_free_meeting(bot, message):
    """Обработка команды для нахождения свободного времени для встречи."""
    bot.send_message(message.chat.id, 'Введите usernames участников, которых вы хотите пригласить (через запятую). Если вы тоже участник встречи, то свой юзернейм тоже надо ввести', reply_markup=create_cancel_keyboard())
    bot.register_next_step_handler(message, lambda msg: check_users(bot, msg))

def check_users(bot, message):
    """Поиск ближайшего свободного слота для встречи."""
    if message.text.strip() == '/cancel':
        keyboard = create_keyboard() 
        bot.send_message(message.chat.id, 'Отмена', reply_markup=keyboard)
        return
    # Проверка на существование юзеров в базе
    usernames = [username.strip() for username in message.text.split(',')]
    if not all_usernames_exist(usernames):
        bot.send_message(message.chat.id, 'Некоторые из указанных юзернеймов не найдены в базе данных. Пожалуйста, повторите ввод.', reply_markup=create_cancel_keyboard())
        bot.register_next_step_handler(message, lambda msg: check_users(bot, msg))
        return
    bot.send_message(message.chat.id, 'Введите желаемую дату (DD-MM-YYY) и самое раннее время начала (HH:MM) через пробел (например: 01-12-2024 12:00)', reply_markup=create_cancel_keyboard())
    bot.register_next_step_handler(message, lambda msg: add_free_users(bot, msg, usernames))

 
def add_free_users(bot, message, usernames):
    if message.text.strip() == '/cancel':
        keyboard = create_keyboard() 
        bot.send_message(message.chat.id, 'Отмена', reply_markup=keyboard)
        return
    try:
        start_time_str = message.text.strip()
        start_time = datetime.datetime.strptime(start_time_str, "%d-%m-%Y %H:%M")
        all_meetings = []
        conn = get_db_connection()
        cursor = conn.cursor()
        # Достаем все будущие встречи для желаемых участников
        for username in usernames:
            cursor.execute('SELECT user_id FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            if user:
                user_id = user[0]
                meetings = get_meetings_for_user(user_id)
                all_meetings.extend(meetings)
        conn.close()
        # Запрашиваем длительность встречи
        bot.send_message(message.chat.id, 'Введите длительность встречи в минутах.', reply_markup=create_cancel_keyboard())
        bot.register_next_step_handler(message, lambda msg: get_duration_free(bot, msg, usernames, start_time, all_meetings))
        
    except ValueError:
        bot.send_message(message.chat.id, 'Ошибка. Пожалуйста, введите время в правильном формате.', reply_markup=create_cancel_keyboard())
        bot.register_next_step_handler(message, lambda msg: add_free_users(bot, msg, usernames))
    


def get_duration_free (bot, message, usernames, start_time, all_meetings):
    if message.text.strip() == '/cancel':
        keyboard = create_keyboard() 
        bot.send_message(message.chat.id, 'Отмена', reply_markup=keyboard)
        return
    try:
        duration = int(message.text.strip())
        """ для поиска свободного слота в соответствии с указанным временем и участниками"""
        next_free_slot = find_nearest_free_time(all_meetings, duration, start_time) 
        if next_free_slot:
            response = f'Ближайшее свободное время для встречи: {next_free_slot.strftime("%d-%m-%Y %H:%M")}. ' \
                    'Хотите запланировать встречу на это время? (да/нет)'
            bot.send_message(message.chat.id, response, reply_markup = create_yes_no_keyboard())
            bot.register_next_step_handler(message, lambda msg: confirm_free_meeting(bot, msg, next_free_slot, usernames, duration))
    except ValueError:
        bot.send_message(message.chat.id, 'Ошибка. Пожалуйста, введите время в правильном формате.', reply_markup=create_cancel_keyboard())
        bot.register_next_step_handler(message, lambda msg: get_duration_free(bot, msg, usernames, start_time, all_meetings))


def confirm_free_meeting(bot, message, next_free_slot, usernames, duration):
    """Обработка согласия на назначение встречи."""
    if message.text.lower() == 'да':
        bot.send_message(message.chat.id, 'Введите название встречи:', reply_markup=create_cancel_keyboard())
        bot.register_next_step_handler(message, lambda m: get_free_meeting_title(bot, m, next_free_slot, usernames, duration))
    else:
        keyboard = create_keyboard()
        bot.send_message(message.chat.id, 'Встреча не была запланирована.', reply_markup=keyboard)

def get_free_meeting_title(bot, message, next_free_slot, usernames, duration):
    """Получение названия встречи."""
    if message.text.strip() == '/cancel':
        keyboard = create_keyboard() 
        bot.send_message(message.chat.id, 'Отмена', reply_markup=keyboard)
        return
    title = message.text
    bot.send_message(message.chat.id, 'Введите описание встречи:', reply_markup=create_cancel_keyboard())
    bot.register_next_step_handler(message, lambda m: create_free_meeting(bot, m, title, next_free_slot, usernames, duration))


def create_free_meeting(bot, message, title, next_free_slot, usernames, duration):
    """Создание новой встречи в базе данных."""
    if message.text.strip() == '/cancel':
        keyboard = create_keyboard() 
        bot.send_message(message.chat.id, 'Отмена', reply_markup=keyboard)
        return
    description = message.text
    end_time = next_free_slot + datetime.timedelta(minutes=duration) 

    # Добавление встречи и участников
    add_meeting(bot, title=title,
                start_time=next_free_slot.strftime("%Y-%m-%d %H:%M:%S"),
                end_time=end_time.strftime("%Y-%m-%d %H:%M:%S"), 
                description=description, 
                usernames=usernames)
    bot.send_message(message.chat.id, 'Встреча успешно запланирована!', reply_markup = create_keyboard())


def delete_meeting(bot, message):
    """Удаление встречи по ID."""
    bot.send_message(message.chat.id, 'Введите ID встречи, которую хотите удалить (чтобы узнать id встреч, используйте команду /view_meetings):', reply_markup=create_cancel_keyboard())
    bot.register_next_step_handler(message, lambda msg: delete_meeting_handler(bot, msg))


def delete_meeting_handler(bot, message):
    """Удаление встречи из базы данных."""
    if message.text.strip() == '/cancel':
        keyboard = create_keyboard() 
        bot.send_message(message.chat.id, 'Отмена', reply_markup=keyboard)
        return
    if message.text.strip() == '/view_meetings':
        view_meetings(bot, message)
        return
    try:
        meeting_id = int(message.text)
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM meetings WHERE id = ?', (meeting_id,))
        meeting = cursor.fetchone()

        if not meeting:
            bot.send_message(message.chat.id, 'Встреча с таким ID не найдена, повторите ввод.', reply_markup = create_cancel_keyboard())
            bot.register_next_step_handler(message, lambda msg: delete_meeting_handler(bot, msg))
            return
        
        cursor.execute('DELETE FROM meetings WHERE id = ?', (meeting_id,))
        cursor.execute('DELETE FROM participants WHERE meeting_id = ?', (meeting_id,))  # Удаляем участников
        conn.commit()
               
        bot.send_message(message.chat.id, 'Встреча успешно удалена! Она исчезнет из вашего гугл-календаря в течение минуты', reply_markup = create_keyboard())
        conn.close()
        
        return

    except ValueError:
        bot.send_message(message.chat.id, 'Введите корректный ID встречи.', reply_markup = create_cancel_keyboard())
        bot.register_next_step_handler(message, lambda msg: delete_meeting_handler(bot, msg))

    except Exception as e:
        bot.send_message(message.chat.id, 'Ошибка при удалении встречи. Убедитесь, что такая встреча существует.', reply_markup = delete_meeting_handler(bot, message))
        print(f"Ошибка при удалении встречи: {e}")  # Для отладки
        
