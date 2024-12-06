from .utils import get_db_connection

def register_user(bot, message):
    conn = get_db_connection('bot_database')
    cursor = conn.cursor()
    
    us_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (us_id,))
    if cursor.fetchone() is not None:
        bot.send_message(message.chat.id, 'Вы уже зарегистрированы в базе данных.')
    else:
        cursor.execute('INSERT INTO users (user_id, username) VALUES (?, ?)', (us_id, username))
        conn.commit()
        bot.send_message(message.chat.id, 'Вы успешно добавлены в базу данных!')

def view_users(bot, message):
    """Отображение всех пользователей в базе данных."""
    conn = get_db_connection('bot_database')
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