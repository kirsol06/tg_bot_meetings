import os
import telebot
from dotenv import load_dotenv
from commands.register import register_user, view_users  # Импорт функции регистрации
from commands.meetings import (
    set_schedule_meeting,
    view_meetings,
    delete_meeting,
    set_free_meeting
)  # Импорт функций для встреч
from commands.help import help_command_handler  # Импорт функции справки
from commands.stats import generate_monthly_stats_plot
from commands.reminders import schedule_reminder_check 

load_dotenv()
TOKEN = os.getenv("TOKEN")

bot = telebot.TeleBot(TOKEN) # Спрятали токен

schedule_reminder_check(bot)

@bot.message_handler(commands=['start'])
def start_command(message):
    bot.send_message(message.chat.id, 'Добро пожаловать! Введите /register, чтобы добавиться в базу данных. Введите /help, чтобы посмотреть список команд')

@bot.message_handler(commands=['help'])
def help_command(message):
    help_command_handler(message)

@bot.message_handler(commands=['register'])
def register_command(message):
    register_user(bot, message)

@bot.message_handler(commands=['set_schedule_meeting'])
def schedule_meeting_command(message):
    set_schedule_meeting(bot, message)

@bot.message_handler(commands=['view_meetings'])
def view_meetings_command(message):
    view_meetings(bot, message)

@bot.message_handler(commands=['view_users'])
def view_users_command(message):
    view_users(bot, message)

@bot.message_handler(commands=['delete_meeting'])
def delete_meeting_command_handler(message):
    delete_meeting(bot, message)

@bot.message_handler(commands=['set_free_meeting'])
def set_free_meeting_command_handler(message):
    set_free_meeting(bot, message)

@bot.message_handler(commands=['stats'])
def show_stats(message):
    generate_monthly_stats_plot(bot, message)

if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)