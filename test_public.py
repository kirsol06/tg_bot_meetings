import pytest
from unittest.mock import *
import datetime
import io
from commands.utils import *
from commands.meetings import *
from commands.register import *
from commands.stats import *
from commands.reminders import *


def test_all_usernames_exist():
    with patch('commands.utils.get_db_connection') as mock_conn:
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [('user1',), ('user2',)]
        mock_conn.return_value.cursor.return_value = mock_cursor
        
        assert all_usernames_exist(['user1', 'user2'])
        assert not all_usernames_exist(['user1', 'user3'])

def test_set_free_meeting():
    bot = MagicMock()
    message = MagicMock()
    message.chat.id = 12345

    with patch('commands.meetings.create_cancel_keyboard', return_value=MagicMock()) as mock_create_cancel_keyboard:
        set_free_meeting(bot, message)

        bot.send_message.assert_called_with(
            message.chat.id,
            'Введите usernames участников, которых вы хотите пригласить (через запятую). Если вы тоже участник встречи, то свой юзернейм тоже надо ввести',
            reply_markup=mock_create_cancel_keyboard.return_value  # Используем замокированный объект
        )


def test_send_meeting_notification():
    bot = MagicMock()
    user_id = 12345
    title = "Встреча"
    start_time = "2023-10-01 12:00:00"
    end_time = "2023-10-01 13:00:00"
    description = "Описание встречи"

    send_meeting_notification(bot, user_id, title, start_time, end_time, description)

    bot.send_message.assert_called_once_with(
        user_id, 
        f"🔥 Вам назначена новая встреча!\n"
        f"Название: {title}\n"
        f"Дата и время начала: {start_time[:-3]}\n"
        f"Дата и время окончания: {end_time[:-3]}\n"
        f"Описание: {description}\n"
    )


def test_delete_meeting_handler():
    bot = MagicMock()
    message = MagicMock()
    message.text = '1'
    message.chat.id = 67890
    
    with patch('commands.meetings.get_db_connection') as mock_conn:
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1, "Meeting Title")  # Встреча найдена

        # Вызываем функцию
        delete_meeting_handler(bot, message)

        # Проверяем удаление записи
        mock_cursor.execute.assert_any_call('DELETE FROM meetings WHERE id = ?', (1,))
        mock_cursor.execute.assert_any_call('DELETE FROM participants WHERE meeting_id = ?', (1,))
        bot.send_message.assert_called_once_with(message.chat.id, 'Встреча успешно удалена!')

def test_generate_monthly_stats_plot():
    bot = MagicMock()
    message = MagicMock()
    message.chat.id = 67890

    # Патчим необходимые функции
    with patch('commands.stats.get_db_connection') as mock_conn, \
         patch('commands.stats.calculate_average_meeting_duration') as mock_calculate_duration, \
         patch('matplotlib.pyplot.savefig') as mock_savefig:

        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor

        # Установим дату и время
        first_day_of_month = datetime.datetime.now().replace(day=1)
        last_day_of_month = (first_day_of_month + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)

        # Настраиваем возврат для расчета средней продолжительности встреч
        mock_calculate_duration.return_value = (30, 5, 150)  # (average_duration, count, total_time)

        # Настраиваем возврат количества встреч по дням
        meetings_per_day_data = [
            (first_day_of_month.strftime('%Y-%m-%d'), 2),
            ((first_day_of_month + datetime.timedelta(days=1)).strftime('%Y-%m-%d'), 3),
        ]
        mock_cursor.fetchall.return_value = meetings_per_day_data

        # Вызываем тестируемую функцию
        generate_monthly_stats_plot(bot, message)

        # Проверяем, что график был создан с правильными данными
        days = [0] * last_day_of_month.day  # 31 день
        days[0] = 2  # 1 число месяца
        days[1] = 3  # 2 число месяца
        bot.send_photo.assert_called_once_with(
            message.chat.id,
            ANY,  # Указываем, что вы ожидаете объект изображения из памяти
            caption="Количество встреч за текущий месяц по дням.\nВаше общее количество встреч: 5.\nВаше среднее время встречи: 30 минут.\nВаше общее время встреч: 150 минут."
        )

        # Проверяем, что сохраняется график
        mock_savefig.assert_called_once()

        # Проверяем, что соединение с базой данных закрывается
        mock_conn.return_value.close.assert_called_once()

def test_register_user_already_registered():
    bot = MagicMock()
    message = MagicMock()
    message.from_user.id = 12345
    message.from_user.username = "test_user"
    message.chat.id = 67890

    with patch('commands.register.get_db_connection') as mock_conn:
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor

        # Настраиваем возврат, чтобы имитировать уже зарегистрированного пользователя
        mock_cursor.fetchone.return_value = (1, "test_user")  # Пользователь уже зарегистрирован
        
        register_user(bot, message)

        # Проверяем, что insert не вызывается и сообщение о регистрации уже было отправлено
        mock_cursor.execute.assert_called_once_with('SELECT * FROM users WHERE user_id = ?', (12345,))
        bot.send_message.assert_called_once_with(message.chat.id, 'Вы уже зарегистрированы в базе данных.')


def test_register_user_new_user():
    bot = MagicMock()
    message = MagicMock()
    message.from_user.id = 12345
    message.from_user.username = "new_user"
    message.chat.id = 67890

    with patch('commands.register.get_db_connection') as mock_conn:
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        
        # Настраиваем возврат, чтобы имитировать нового пользователя
        mock_cursor.fetchone.return_value = None  # Пользователь не зарегистрирован

        register_user(bot, message)

        # Проверяем, что insert вызывается и новое сообщение о регистрации было отправлено
        mock_cursor.execute.assert_any_call('SELECT * FROM users WHERE user_id = ?', (12345,))
        mock_cursor.execute.assert_any_call('INSERT INTO users (user_id, username) VALUES (?, ?)', (12345, "new_user"))
        bot.send_message.assert_called_once_with(message.chat.id, 'Вы успешно добавлены в базу данных!')



from unittest.mock import MagicMock, patch

def test_process_start_time_invalid_format1():
    bot = MagicMock()
    message = MagicMock()
    message.chat.id = 67890
    message.text = "invalid_format"

    # Патчинг create_cancel_keyboard, чтобы вернуть замокированный объект
    with patch('commands.meetings.create_cancel_keyboard', return_value=MagicMock()) as mock_create_cancel_keyboard:
        # Вызываем функцию обработки времени начала
        process_scheduled_start_time(bot, message)
        
        # Проверяем, что сообщение об ошибке отправлено
        bot.send_message.assert_called_once_with(
            message.chat.id,
            'Ошибка. Пожалуйста, введите дату и время в правильном формате.',
            reply_markup=mock_create_cancel_keyboard.return_value  # используем мок объект
        )


def test_process_start_time_invalid_format2():
    bot = MagicMock()
    message = MagicMock()
    message.chat.id = 67890
    message.text = "2024-12-01 25:17"

    # Патчинг create_cancel_keyboard, чтобы вернуть замокированный объект
    with patch('commands.meetings.create_cancel_keyboard', return_value=MagicMock()) as mock_create_cancel_keyboard:
        # Вызываем функцию обработки времени начала
        process_scheduled_start_time(bot, message)
        
        # Проверяем, что сообщение об ошибке отправлено
        bot.send_message.assert_called_once_with(
            message.chat.id,
            'Ошибка. Пожалуйста, введите дату и время в правильном формате.',
            reply_markup=mock_create_cancel_keyboard.return_value  # используем мок объект
        )



def test_save_meeting_success():
    bot = MagicMock()
    message = MagicMock()
    message.chat.id = 67890
    message.text = "Test meeting description"
    
    title = "Test Meeting"
    start_time = datetime.datetime(2024, 12, 1, 20, 30)
    end_time = datetime.datetime(2024, 12, 1, 21, 30)
    usernames = ['user1', 'user2']

    # Патчинг create_keyboard
    with patch('commands.meetings.create_keyboard', return_value=MagicMock()) as mock_create_keyboard, \
         patch('commands.meetings.add_meeting') as mock_add_meeting:
        
        mock_add_meeting.return_value = None  # предполагаем, что add_meeting ничего не возвращает в случае успеха
        
        save_scheduled_meeting(bot, message, title, start_time, end_time, usernames)

        # Проверяем, что функция для добавления встречи была вызвана с правильными аргументами
        mock_add_meeting.assert_called_once_with(
            bot,
            'bot_database.db',
            title=title,
            start_time=start_time.strftime("%Y-%m-%d %H:%M:%S"),
            end_time=end_time.strftime("%Y-%m-%d %H:%M:%S"),
            description=message.text.strip(),
            usernames=usernames
        )

        # Проверяем, что сообщение об успешном сохранении отправлено
        bot.send_message.assert_called_once_with(
            message.chat.id,
            'Встреча успешно запланирована!',
            reply_markup=mock_create_keyboard.return_value  # использование замокированного объекта
        )


def test_view_meetings_no_meetings():
    bot = MagicMock()
    message = MagicMock()
    message.chat.id = 67890  # ID чата
    message.from_user.id = 12345  # ID пользователя

    # Патчинг get_meetings_for_user, чтобы вернуть пустой список
    with patch('commands.meetings.get_meetings_for_user', return_value=[]), \
         patch('commands.meetings.create_keyboard', return_value=MagicMock()) as mock_create_keyboard:

        view_meetings(bot, message)

        # Проверяем, что отправлено сообщение о том, что нет встреч
        bot.send_message.assert_called_once_with(
            message.chat.id,
            'У вас нет запланированных встреч.',
            reply_markup=mock_create_keyboard.return_value  # Используем замокированный объект
        )


def test_view_meetings_with_meetings():
    bot = MagicMock()
    message = MagicMock()
    message.chat.id = 67890
    message.from_user.id = 12345

    user_meetings = [
        (1, 'Встреча 1', '2024-12-01 20:30:00', '2024-12-01 21:30:00', 'Описание встречи 1'),
        (2, 'Встреча 2', '2024-12-02 18:00:00', '2024-12-02 19:00:00', 'Описание встречи 2'),
    ]

    with patch('commands.meetings.get_meetings_for_user', return_value=user_meetings), \
         patch('commands.meetings.create_keyboard', return_value=MagicMock()) as mock_create_keyboard:

        view_meetings(bot, message)

        expected_response = (
            "Ваши предстоящие  запланированные встречи:\n \n"
            "ID: 1; \n Название: Встреча 1, \n Дата начала: 2024-12-01 20:30, \n "
            "Дата окончания: 2024-12-01 21:30, \n Описание: Описание встречи 1 \n \n"
            "ID: 2; \n Название: Встреча 2, \n Дата начала: 2024-12-02 18:00, \n "
            "Дата окончания: 2024-12-02 19:00, \n Описание: Описание встречи 2 \n \n"
        )

        bot.send_message.assert_called_once_with(
            message.chat.id,
            expected_response,
            reply_markup=mock_create_keyboard.return_value  # Используем замокированный объект
        )



def test_send_reminders_no_reminders():
    bot = MagicMock()

    # Патчинг get_db_connection, чтобы вернуть замокированный объект соединения
    with patch('commands.reminders.get_db_connection') as mock_get_db_connection:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()

        # Настройка возвратов для мок-объекта
        mock_get_db_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        now = datetime.datetime.now()
        reminder_time = now + datetime.timedelta(minutes=30)

        # Устанавливаем возврат для курсора - у нас нет встреч по времени
        mock_cursor.fetchall.return_value = []

        # Вызываем функцию отправки напоминаний
        send_reminders(bot)

        # Проверяем, что сообщение не было отправлено
        bot.send_message.assert_not_called()
