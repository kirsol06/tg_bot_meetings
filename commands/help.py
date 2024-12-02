def help_command_handler(message):
    from bot import bot
    help_text = (
        "Доступные команды:\n"
        "/start - Начать взаимодействие с ботом.\n"
        "/register - Зарегистрироваться в базе данных.\n"
        "/set_schedule_meeting - Запланировать встречу на определенное время.\n"
        "/set_free_meeting - Запланировать встречу на свободное время.\n"
        "/view_meetings - Посмотреть все запланированные встречи на текущей неделе.\n"
        "/view_users- Посмотреть всех зарегистрированных пользователей.\n"
        "/delete_meeting - Удалить встречу по id.\n"
        "/stats - Показать статистику встреч и визуализацию загруженности.\n"
    )
    bot.send_message(message.chat.id, help_text)
