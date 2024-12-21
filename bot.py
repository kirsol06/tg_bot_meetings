import time
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

# Импортируем все, что можно

load_dotenv()
TOKEN = os.getenv("TOKEN")

bot = telebot.TeleBot(TOKEN) # Спрятали токен

schedule_reminder_check(bot) # Запустили отправление напоминалок

# Хендлеры

@bot.message_handler(commands=['cancel'])
def start_handler(message):
    keyboard = create_keyboard() 
    bot.send_message(message.chat.id, 'Отмена', reply_markup=keyboard)
    user_id = message.from_user.id 

@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.send_message(message.chat.id, 'Добро пожаловать! Введите /register, чтобы добавиться в базу данных.')

@bot.message_handler(commands=['help'])
def help_command(message):
    keyboard = create_keyboard() 
    help_command_handler(message)
    bot.send_message(message.chat.id, "Выберите команду:", reply_markup=keyboard)

@bot.message_handler(commands=['register'])
def register_command(message):
    register_user(bot, message)
    
@bot.message_handler(commands=['set_schedule_meeting'])
def schedule_meeting_command(message):
    set_schedule_meeting(bot, message)
    user_id = message.from_user.id 
    start_sync_events(bot, user_id)

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
    user_id = message.from_user.id 
    start_sync_events(bot, user_id)

@bot.message_handler(commands=['set_free_meeting'])
def set_free_meeting_command_handler(message):
    set_free_meeting(bot, message)
    user_id = message.from_user.id 
    start_sync_events(bot, user_id)

@bot.message_handler(commands=['stats'])
def show_stats(message):
    keyboard = create_keyboard() 
    generate_monthly_stats_plot(bot, message)
    bot.send_message(message.chat.id, "Выберите команду:", reply_markup=keyboard)


if __name__ == '__main__':
    print("Бот запущен...")
    while True:
        try:
            bot.polling(none_stop=True, timeout=60)
        except Exception as e:
            print(f"Ошибка: {e}, повторная попытка подключения через 5 секунд...")
            time.sleep(5)