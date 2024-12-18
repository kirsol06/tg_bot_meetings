import sqlite3
from .utils import get_db_connection
from google_auth import *
from .help import create_keyboard

def register_user(bot, message):
    """Регистрация пользователя"""
    conn = get_db_connection()
    cursor = conn.cursor()
    us_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name # Получили тг юзернейм и id
    
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (us_id,)) # Проверяем, нет ли этого пользователя в базе
    if cursor.fetchone() is not None:
        bot.send_message(message.chat.id, 'Вы уже зарегистрированы в базе данных.')
    else: # Если нет, то записываем
        cursor.execute('INSERT INTO users (user_id, username) VALUES (?, ?)', (us_id, username))
        conn.commit()
        bot.send_message(message.chat.id, 'Вы успешно добавлены в базу данных!')
        bot.send_message(message.chat.id, "Пройдите аутентификацию в гугл, для синхронизации с гугл календарем \nВведите вашу гугл почту:")
        bot.register_next_step_handler(message, lambda msg: authenticate_user(bot, msg))

def authenticate_user(bot, message):
    conn = get_db_connection()
    cursor = conn.cursor()
    user_id = message.from_user.id
    gmail = message.text.strip()
    creds = authenticate_google(user_id)  # Пытаемся аутентифицировать пользователя
    if creds is None:
        # Если creds отсутствует, выводим URL для аутентификации
        gmail = message.text.strip()
        if gmail[-10:] == '@gmail.com':
            user_id = message.from_user.id
            print(gmail)
            cursor.execute('UPDATE users SET email = ? WHERE user_id = ?', (gmail, user_id))
            conn.commit()
            bot.send_message(message.chat.id, f"Перейдите по следующей ссылке для аутентификации: {generate_auth_url(user_id)}.\n"
                                "После авторизации введите код, который вам будет предоставлен")
            bot.register_next_step_handler(message, lambda msg: handle_code(bot, msg))
        else: 
            bot.send_message(message.chat.id, "Неверный ввод: введите свою гугл почту")
            bot.register_next_step_handler(message, lambda msg: authenticate_user(msg))
    else:
        bot.send_message(message.chat.id, "Вы успешно аутентифицированы! Синхронизация встреч запущена", reply_markup=create_keyboard())
        #sync_events(user_id)  # Ваша функция синхронизации
        #threading.Timer(60, start_sync_events, [bot, user_id]).start() 

def handle_code(bot, message):
    user_id = message.from_user.id
    code = message.text.strip()# Извлекаем код из сообщения
    if code[:3] == '4/1':
        creds = authenticate_user_with_code(user_id, code)  # Получаем и сохраняем токен доступа
        if creds:
            bot.send_message(message.chat.id, "Вы успешно аутентифицированы! Введите /help, чтобы увидеть список команд.", reply_markup=create_keyboard())
        else:
            bot.send_message(message.chat.id, "Произошла ошибка при аутентификации.")
    else:
        bot.send_message(message.chat.id, "Что-то не то с кодом, попробуйте еще раз. Введите правильный код")
        bot.register_next_step_handler(message, lambda msg: handle_code(bot, msg))

def view_users(bot, message):
    """Отображение всех пользователей в базе данных."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Запрос всех пользователей
    cursor.execute('SELECT username FROM users')
    users = cursor.fetchall()
    conn.close()

    if not users:
        bot.send_message(message.chat.id, 'Список пользователей пуст.')
    else:
        user_list = '\n'.join([user[0] for user in users])  # Получаем список юзернеймов
        response_message = f'Список пользователей:\n{user_list}'
        bot.send_message(message.chat.id, response_message)

def get_all_user_ids():
    """Получает все идентификаторы пользователей из базы данных."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Запрос для получения всех user_id из таблицы users
        cursor.execute("SELECT id FROM users")
        user_ids = [row[0] for row in cursor.fetchall()]  # Извлекаем user_id из результата
        
        return user_ids
    except sqlite3.Error as e:
        print(f"Ошибка при работе с базой данных: {e}")
        return []
    finally:
        if conn:
            conn.close()