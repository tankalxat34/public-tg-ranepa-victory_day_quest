"""Главный скрипт бота. На данной версии является тестовым образцом

https://github.com/tankalxat34/ranepa-quest-victoryday

БОТ ЗАПУЩЕН
"""
import telebot
from telebot import types
import botlib
import random
import importlib
import json
import collections

# создаем клавиатуру для завершения квеста
kb_end_quest = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
kb_end_quest.add(types.KeyboardButton("Завершить связь"))

# записываем мой ID как главный
BOSS_ID = botlib.env.TELEGRAM_YOUR_ID

# создаем словарь КОМАНДА: ДЕЙСТВИЕ для интерфейса администратора
dict_admin_ui = {
    "обновить": {
        "function": lambda: importlib.reload(botlib),
        "description": f"перезагружает реплики бота. После любых изменений в ветке {botlib.CONST_GITHUB_CONTENT_BRANCH_NAME} необходимо выполнить эту команду, чтобы бот получил эти изменения"
    },
    "список": {
        "function": lambda: getPlayerList(),
        "description": "высылает список всех пользователей, которые хоть раз писали боту, и их текущий уровень"
    },
    "победитель": {
        "function": lambda: getPlayerWinnersList(),
        "description": "высылает список всех победителей квеста, а также их количество"
    },
    "помощь": {
        "function": lambda: getHelpAdmin(),
        "description": "высылает список всех команд администратора и их описание"
    }
}
# получаем токен из файла с константами
TOKEN = botlib.env.TELEGRAM_TOKEN

# создаем объект бота
bot = telebot.TeleBot(TOKEN)

print(__doc__)


def setZeroProgress(user_id=BOSS_ID):
    """Обнуляет мой прогресс в боте"""
    botlib.list_players[str(user_id)]["step"] = 0
    botlib.github.commit(filepath=botlib.CONST["userProgressFile"], filecontent=json.dumps(botlib.list_players), branch=botlib.CONST_GITHUB_CONTENT_BRANCH_NAME, commit_message=f'{botlib.list_players[str(user_id)]["username"]} ({user_id}) → {botlib.list_players[str(user_id)]["step"] - 1}')


def getHelpAdmin():
    """Высылает сообщение с помощью по командам администратора"""
    result = "🍕 Обратите внимание, некоторые команды могут вызвать зависание бота! Выполнять только при особой необходимости!\n\nДоступные функции:\n\n"
    for key in dict_admin_ui.keys():
        result += f"*{key}*" + " - " + dict_admin_ui[key]["description"] + "\n\n"
    return result


def getMaxQuestLevel():
    """Получает номер финального квестового задания, которое считается победным"""
    return len(botlib.CONST["messages"].keys()) - 1


def increaseProgressLevel(user_id):
    """Увеличивает прогресс пользователя на 1 и коммитит изменение"""
    # изменяем этап пользователя на 1
    botlib.list_players[str(user_id)]["step"] += 1
    # и коммитим изменения в специальный файл на github в ветке content
    botlib.github.commit(filepath=botlib.CONST["userProgressFile"], filecontent=json.dumps(botlib.list_players), branch=botlib.CONST_GITHUB_CONTENT_BRANCH_NAME, commit_message=f'{botlib.list_players[str(user_id)]["username"]} ({user_id}) → {botlib.list_players[str(user_id)]["step"] - 1}')


def getPlayerList(start_message="СПИСОК ИГРОКОВ:\nstep user_id username\n\n"):
    """Возвращает текстом список игроков, содержащий id и имя пользователей, которые написали боту на момент вызова функции. Идет сортировка согласно этапу пользователя на данный момент"""
    answer = "" + start_message
    local_dict = dict()

    for user_id in botlib.list_players.keys():
        try:
            local_dict[botlib.list_players[str(user_id)]['step'] - 1].append({"user_id": user_id, "username": botlib.list_players[str(user_id)]['username']})
        except Exception:
            local_dict[botlib.list_players[str(user_id)]['step'] - 1] = list()
            local_dict[botlib.list_players[str(user_id)]['step'] - 1].append({"user_id": user_id, "username": botlib.list_players[str(user_id)]['username']})

    sorted_local_dict = collections.OrderedDict(sorted(local_dict.items(), reverse=True))

    for step in sorted_local_dict.keys():
        for section in sorted_local_dict[step]:
            answer += f'{step} {section["user_id"]} @{section["username"]}\n'

    # for user_id in botlib.list_players.keys():
    #     answer += f"{user_id} @{botlib.list_players[str(user_id)]['username']} {botlib.list_players[str(user_id)]['step'] - 1}\n"
    return answer


def getCountOfWinners():
    """Возвращает количество победителей квеста"""
    counter = 0
    for user_id in botlib.list_players.keys():
        if botlib.list_players[str(user_id)]["step"] == getMaxQuestLevel():
            counter += 1
    return counter


def getPlayerWinnersList(start_message=f"СПИСОК ПОБЕДИТЕЛЕЙ:\n\nid username\n"):
    """Возвращает список победителей квеста в виде текста, содержащего id и имя пользователей"""
    answer = "" + start_message
    for user_id in botlib.list_players.keys():
        if botlib.list_players[str(user_id)]["step"] == getMaxQuestLevel():
            answer += f"{user_id} @{botlib.list_players[str(user_id)]['username']}\n"
    return answer


# хендлер для отлова команд администратора
@bot.message_handler(commands=["бот"])
def message_admin_interface(message):
    """Обрабатывает команды администратора"""
    user_id = message.from_user.id
    text = message.text.lower()
    username = message.from_user.username

    if str(user_id) in botlib.CONST_ADMINLIST:
        # получаем аргументы команды
        args = text.split()

        if len(args) == 1:
            # если команда набрана неверно - сообщим админу об этом
            bot.send_message(user_id, "🍕 Для выполнения команд администратора необходимо задать аргументы команды. Например: `/бот обновить`", parse_mode="markdown")
        else:
            try:
                # выполняем команду
                command = dict_admin_ui[args[1]]["function"]()

                # если результат выполнения команды является строкой - отправляем ее администратору
                if isinstance(command, str):
                    bot.send_message(user_id, command)

                # если администратор - не босс, уведомляем об успехе отправителя команды
                if user_id != BOSS_ID:
                    bot.send_message(user_id, f"🍕 Команда `{text}` успешно выполнена!", parse_mode="markdown")
                # и обязательно пишем боссу, что некто выполнил команду
                bot.send_message(BOSS_ID, f"🍕 Команда `{text}` выполнена администратором @{username}", parse_mode="markdown")
            except Exception:
                # если команда не найдена - сообщим админу об этом
                bot.send_message(user_id, f"🍕 Произошла ошибка в выполнении команды либо команда не найдена!\n\n"+getHelpAdmin(), parse_mode="markdown")
    else:
        bot.send_message(user_id, random.choice(botlib.CONST["random_messages"]))


# возможность писать любым пользователям от имени бота
@bot.message_handler(commands=["message"])
def message_touser_validator(message):
    """Функция отправляет сообщение по id"""
    user_id = message.from_user.id
    text = message.text.lower()
    username = message.from_user.username

    # обнуление прогресса доступно только для тех, кто является админом бота
    if str(user_id) in botlib.CONST_ADMINLIST:
        try:
            # получаем аргументы (почти как в sys.args)
            args = text.split()

            # уведомляем пользователя текстовым сообщением, сообщаем об успехе админу и главному админу
            bot.send_message(int(args[1]), " ".join(args[2:]))
            bot.send_message(user_id, f"🍕 Сообщение отправлено пользователю `{args[1]}`\n\nТекст сообщения:\n{' '.join(args[2:])}", parse_mode="markdown")
            bot.send_message(BOSS_ID, f"🍕 Команда `{text}` выполнена администратором @{username}\n\nТекст сообщения:\n{' '.join(args[2:])}", parse_mode="markdown")
        except Exception:
            # в случае ошибки сообщим об этом
            bot.send_message(user_id, f"🍕 Произошла ошибка в выполнении команды либо команда не найдена!\n\n" + getHelpAdmin(), parse_mode="markdown")


# основной хендлер для обнуления прогресса
@bot.message_handler(commands=["zero"])
def message_hint_validator(message):
    """Функция обнуляет прогресс пользователя по его ID"""
    user_id = message.from_user.id
    text = message.text.lower()
    username = message.from_user.username

    # обнуление прогресса доступно только для тех, кто является админом бота
    if str(user_id) in botlib.CONST_ADMINLIST:
        try:
            # получаем аргументы (почти как в sys.args)
            args = text.split()
            # если команда выглядит так: /zero me
            if args[1] == "me":
                # обнуляем прогресс квеста у написавшего админа
                setZeroProgress(user_id)
                # Пишем системное сообщение о том, что ваш прогресс обнулен
                bot.send_message(user_id, "🍕 Ваш прогресс обнулен!")
            else:
                # иначе считаем, что аргументом является id какого-то пользователя
                setZeroProgress(int(args[1]))
                # уведомляем об обнулении главного админа, пользователя и админа, запросившего обнуление
                bot.send_message(user_id,f"🍕 Прогресс пользователя `{args[1]}` обнулен!", parse_mode="markdown")
                bot.send_message(int(args[1]),f"Администраторы обнулули ваш прогресс в прохождении квеста\n\nУзнать, почему так произошло: @{username}", parse_mode="markdown")
                bot.send_message(BOSS_ID, f"🍕 Команда `{text}` выполнена администратором @{username}", parse_mode="markdown")
        except Exception:
            # в случае какой либо ошибки - пишем об этом админу
            bot.send_message(user_id,f"🍕 Произошла ошибка в выполнении команды либо команда не найдена!\n\n" + getHelpAdmin(), parse_mode="markdown")


# основной хендлер для отправки подсказок
@bot.message_handler(commands=["hint"])
def message_hint_validator(message):
    """Функция высылает подсказку по конкретному этапу"""
    user_id = message.from_user.id
    text = message.text.lower()
    username = message.from_user.username

    # если пользователь не является победителем
    if json.loads(botlib.github.get_file(botlib.CONST["userProgressFile"], botlib.CONST_GITHUB_CONTENT_BRANCH_NAME))[str(user_id)]["iswinner"] == 0:
        try:
            # отправляем текст подсказки из файла на GitHub с помощью библиотеки
            bot.send_message(user_id, botlib.github.get_file(botlib.CONST_DIR_NAMES["hints"] + f"/hint{botlib.list_players[str(user_id)]['step'] - 1}.md", botlib.CONST_GITHUB_CONTENT_BRANCH_NAME), parse_mode="markdown")
        except Exception:
            # в случае если подсказки нет на GitHub - пишем непонимание
            bot.send_message(user_id, "_" + random.choice(botlib.CONST["random_hintGetError"]) + "_", parse_mode="markdown")



# основной хендлер. Он отлавливает квестовые сообщения
@bot.message_handler(content_types="text")
def message_validator(message):
    """Главная функция по получению и обработке сообщений пользователя"""
    user_id = message.from_user.id
    text = message.text.lower()
    username = message.from_user.username

    # записываем id пользователя в общий словарь пользователей
    try:
        # сохраним шаг пользователя
        user_info = {"username": username, "step": int(botlib.list_players[str(user_id)]["step"]), "iswinner": 0}
    except KeyError:
        # если же этот пользователь еще ниразу нам не писал - создадим для него отдельную секцию
        user_info = {"username": username, "step": 0, "iswinner": 0}

    # и запишем в новый словарь
    botlib.list_players[str(user_id)] = user_info

    try:
        # обработка ответов на квестовые задания
        if text in botlib.CONST["messages"]["step" + str(botlib.list_players[str(user_id)]["step"])]["trigger"].split(","):

            try:
                # сначала пытаемся отправить явный ответ из ключа answer
                bot.send_message(user_id, botlib.CONST["messages"]["step" + str(botlib.list_players[str(user_id)]["step"])]["answer"], parse_mode="markdown")
            except Exception:
                # если ключа answer нет - отправляем текст из файла с ответом
                # по умолчанию файлы с репликами находятся в папке "Реплики/" и называются "answer{number}.md"
                try:
                    bot.send_message(user_id, botlib.answer_texts[botlib.list_players[str(user_id)]["step"]], parse_mode="markdown")
                except Exception:
                    # если же и такого ключа нет - пишем, что бот нечего ответить
                    bot.send_message(user_id, "Мне нечего тебе ответить...")

            # попытка отправить фото
            try:
                bot.send_photo(user_id, botlib.github.get_file_new_method(botlib.CONST_DIR_NAMES["images"] + "/" + botlib.CONST["messages"]["step" + str(botlib.list_players[str(user_id)]["step"])]["image"], botlib.CONST_GITHUB_CONTENT_BRANCH_NAME))
            except Exception:
                pass
            # попытка отправить аудио
            try:
                bot.send_audio(user_id, botlib.github.get_file_new_method(botlib.CONST_DIR_NAMES["audios"] + "/" + botlib.CONST["messages"]["step" + str(botlib.list_players[str(user_id)]["step"])]["audio"], botlib.CONST_GITHUB_CONTENT_BRANCH_NAME))
            except Exception:
                pass
            # попытка отправить документ
            try:
                bot.send_document(user_id, botlib.github.get_file_new_method(botlib.CONST_DIR_NAMES["files"] + "/" + botlib.CONST["messages"]["step" + str(botlib.list_players[str(user_id)]["step"])]["doc"], botlib.CONST_GITHUB_CONTENT_BRANCH_NAME))
            except Exception:
                pass

            if botlib.list_players[str(user_id)]["step"] == 9:
                bot.send_message(user_id, 'Для ответного завершения связи нажмите на кнопку "Завершить связь"', parse_mode="markdown", reply_markup=kb_end_quest)

            # увеличиваем прогресс пользователя
            increaseProgressLevel(user_id)

        else:
            bot.send_message(user_id, "_" + random.choice(botlib.CONST["random_messages"]) + "_", parse_mode="markdown")
    except Exception:
        # Одновременно проверяется два условия:
        #   если текст сообщения от пользователя есть в триггере для финального сообщения
        #   если уровень игрока равен максимальному и статус победителя, сохраненный на гитхабе, равен 0
        if text in botlib.CONST["messages"]["finalMessage"]["trigger"] and json.loads(botlib.github.get_file(botlib.CONST["userProgressFile"], botlib.CONST_GITHUB_CONTENT_BRANCH_NAME))[str(user_id)]["iswinner"] == 0:
            bot.send_message(user_id, botlib.github.get_file(botlib.CONST_DIR_NAMES["replicates"] + "/answer_final.md", botlib.CONST_GITHUB_CONTENT_BRANCH_NAME), parse_mode="markdown", reply_markup=types.ReplyKeyboardRemove())

            # если уровень игрока равен максимальному и статус победителя, сохраненный на гитхабе, равен 0
            # (не является победителем) - выслать ник игрока в канал и записать его как победителя
            if botlib.list_players[str(user_id)]["step"] == getMaxQuestLevel() and json.loads(botlib.github.get_file(botlib.CONST["userProgressFile"], botlib.CONST_GITHUB_CONTENT_BRANCH_NAME))[str(user_id)]["iswinner"] == 0:
                
                # делаем пользователя победителем
                botlib.list_players[str(user_id)]["iswinner"] = 1
                
                # пишем в канал его ник
                bot.send_message(botlib.env.TELEGRAM_CHANNEL_ID, f"НОВЫЙ ПОБЕДИТЕЛЬ\n\nНикнейм: @{username}\nID: {user_id}")
                
                # и боссу в личку
                bot.send_message(BOSS_ID, f"НОВЫЙ ПОБЕДИТЕЛЬ\n\nНикнейм: @{username}\nID: {user_id}")
                
                # а также коммитим изменения в его секции
                botlib.github.commit(filepath=botlib.CONST["userProgressFile"],
                                     filecontent=json.dumps(botlib.list_players),
                                     branch=botlib.CONST_GITHUB_CONTENT_BRANCH_NAME,
                                     commit_message=f'{botlib.list_players[str(user_id)]["username"]} ({user_id}) → победитель')

        # иначе если пользователь не является победителем квеста
        elif json.loads(botlib.github.get_file(botlib.CONST["userProgressFile"], botlib.CONST_GITHUB_CONTENT_BRANCH_NAME))[str(user_id)]["iswinner"] == 0:
            # высказываем непонимание
            bot.send_message(user_id, "_" + random.choice(botlib.CONST["random_messages"]) + "_", parse_mode="markdown")


bot.infinity_polling()