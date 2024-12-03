from datetime import time
import os
import telebot
from dotenv import load_dotenv
from commands.register import register_user, view_users
from commands.meetings import (
    set_schedule_meeting,
    view_meetings,
    delete_meeting,
    set_free_meeting
)  
from commands.help import help_command_handler
from commands.stats import generate_monthly_stats_plot
from commands.reminders import schedule_reminder_check 
from commands.help import create_keyboard
from google_auth import *



load_dotenv()
TOKEN = os.getenv("TOKEN")

bot = telebot.TeleBot(TOKEN) # Спрятали токен

schedule_reminder_check(bot)

@bot.message_handler(commands=['cancel'])
def start_handler(message):
    keyboard = create_keyboard() 
    bot.send_message(message.chat.id, 'Отмена', reply_markup=keyboard)

@bot.message_handler(commands=['start'])
def start_handler(message):
    keyboard = create_keyboard() 
    bot.send_message(message.chat.id, 'Добро пожаловать! Введите /register, чтобы добавиться в базу данных. Введите /help, чтобы посмотреть список команд', reply_markup=keyboard)

@bot.message_handler(commands=['help'])
def help_command(message):
    keyboard = create_keyboard() 
    help_command_handler(message)
    bot.send_message(message.chat.id, "Выберите команду:", reply_markup=keyboard)


@bot.message_handler(commands=['register'])
def register_command(message):
    keyboard = create_keyboard() 
    register_user(bot, message)
    bot.send_message(message.chat.id, "Выберите команду:", reply_markup=keyboard)


@bot.message_handler(commands=['set_schedule_meeting'])
def schedule_meeting_command(message):
    set_schedule_meeting(bot, message)

@bot.message_handler(commands=['view_meetings'])
def view_meetings_command(message):
    keyboard = create_keyboard() 
    view_meetings(bot, message)
    bot.send_message(message.chat.id, "Выберите команду:", reply_markup=keyboard)


@bot.message_handler(commands=['view_users'])
def view_users_command(message):
    keyboard = create_keyboard() 
    view_users(bot, message)
    bot.send_message(message.chat.id, "Выберите команду:", reply_markup=keyboard)


@bot.message_handler(commands=['delete_meeting'])
def delete_meeting_command_handler(message):
    delete_meeting(bot, message)

@bot.message_handler(commands=['set_free_meeting'])
def set_free_meeting_command_handler(message):
    set_free_meeting(bot, message)

@bot.message_handler(commands=['stats'])
def show_stats(message):
    keyboard = create_keyboard() 
    generate_monthly_stats_plot(bot, message)
    bot.send_message(message.chat.id, "Выберите команду:", reply_markup=keyboard)

@bot.message_handler(commands=['authenticate'])
def authenticate_user(message):
    user_id = message.from_user.id
    creds = authenticate_google(user_id)  # Пытаемся аутентифицировать пользователя

    if creds is None:
        # Если creds отсутствует, выводим URL для аутентификации
        bot.send_message(message.chat.id, 
                         f"Перейдите по следующей ссылке для аутентификации: {generate_auth_url(user_id)}.\n "
                         "После авторизации введите 'code: ' и код, который вам будет предоставлен. Надо перетерпеть это один разок")
    else:
        bot.send_message(message.chat.id, 
                         "Вы успешно аутентифицированы! Теперь вы можете использовать команду /sync_events.")

@bot.message_handler(func=lambda message: message.text.startswith('code:'.lower()))
def handle_code(message):
    user_id = message.from_user.id
    code = message.text.split(':')[1].strip()  # Извлекаем код из сообщения
    creds = authenticate_user_with_code(user_id, code)  # Получаем и сохраняем токен доступа
    if creds:
        bot.send_message(message.chat.id, "Вы успешно аутентифицированы! Теперь вы можете использовать команду /sync_events.")
    else:
        bot.send_message(message.chat.id, "Произошла ошибка при аутентификации.")

@bot.message_handler(commands=['sync_events'])
def sync_events_handler(message):
    user_id = message.from_user.id  # Получаем идентификатор пользователя
    if token_exists(bot, message, user_id): # Прерываем выполнение функции, если токен отсутствует
        sync_events(user_id)  # Выполняем синхронизацию
        bot.send_message(message.chat.id, "Синхронизация с Google Calendar завершена.")


if __name__ == '__main__':
    print("Бот запущен...")
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(f"Ошибка: {e}, повторная попытка подключения через 5 секунд...")
            time.sleep(5)


