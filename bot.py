from time import ctime
from tkinter import PhotoImage
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
import requests
from config import TOKEN
from telegram import LoginUrl, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
)
import json
from functions import *


# Определяем константы этапов разговора
FULLNAME, STUDENTID, DEPARTMENT, JOURNAL, FILEUPLOAD, LOGIN = range(6)

USERDATA = {}


bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


def start(update, _):
    update.message.reply_text(
        'Привет! Меня зовут Моторбек :D'
        '\n\nНаша PR @aniyarasset создала меня, чтобы лучше понимать и следить за деятельностью мемберов. '
        '(А так же, чтобы собирать контент для инсты и спонсоров).'
        '\n\nРаз в неделю, тебе нужно будет коротко рассказывать выполненных задачах '
        'и прикладывать фото/видео.')
    update.message.reply_text(
        'А пока, давай познакомимся. '
        'Как тебя зовут? (Имя и фамилия латиницей)')
    return FULLNAME


def fullname(update, _):
    ans = update.message.text
    if ans.count(' ') != 1:
        update.message.reply_text(
            'Кажется, вы ввели некоректные данные:)\nВведи имя и фамилию латиницей через пробел')
        return incorrect_fullname()
    else:
        USERDATA['name'] = ans.split()[0]
        USERDATA['surname'] = ans.split()[1]
        update.message.reply_text('Введи свой Student ID')
        return STUDENTID


def incorrect_fullname():
    return FULLNAME


def studentid(update, _):
    ans = update.message.text
    if ans.isnumeric() == False or len(ans) != 9:
        update.message.reply_text(
            'Кажется, вы ввели некоректные данные:)\nStudent Id должен состоять из 9 цифр')
        return incorrect_id()
    USERDATA['id'] = ans
    reply_keyboard = [['GLV', 'Management',
                       'Chassis', 'Suspension', 'Tractive', 'CV']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(
        'Из какого ты департамента?', reply_markup=markup_key)

    return DEPARTMENT


def incorrect_id():
    return STUDENTID


def department(update, _):
    user = update.message.from_user
    USERDATA['department'] = update.message.text
    update.message.reply_text(
        'Кратко опиши выполненные задачи (минимум 2 предложения)'
        'или /skip если еще не готов... я спрошу еще раз перед дедлайном'
    )
    insert_member(USERDATA)

    return JOURNAL


def add_work(update, _):
    if 'id' in USERDATA and 'name' in USERDATA and 'department' in USERDATA:
        update.message.reply_text(
            'Вы зашли как '
            + USERDATA['name'] +
            '\nКратко опиши выполненные задачи (минимум 2 предложения)'
            'или /skip если еще не готов... я спрошу еще раз перед дедлайном')
        return JOURNAL
    update.message.reply_text('Введи Student ID')
    return LOGIN


def login(update, _):
    USERDATA['id'] = update.message.text
    member = get_member(int(USERDATA['id']))
    if member == None:
        update.message.reply_text(
            'Похоже, вы ввели неправильный Student ID\n'
            'Введите Student ID снова, или /start чтобы зарегистрироватьься в системе')
        return LOGIN
    USERDATA['name'] = member['Name']
    USERDATA['surname'] = member['Surname']
    USERDATA['department'] = member['Department']

    update.message.reply_text(
        'Вы зашли как '
        + USERDATA['name'] +
        '\nКратко опиши выполненные задачи (минимум 2 предложения)'
        'или /skip если еще не готов... я спрошу еще раз перед дедлайном')

    return JOURNAL


def journal(update, _):
    USERDATA['journal'] = update.message.text
    update.message.reply_text(
        'Великолепная работа!\nА теперь скинь фото/видео/документ для отчета')
    return FILEUPLOAD


def fileupload(update, context):
    if update.message.video:
        file_id = update.message.video.file_id
        print("got video")
    elif update.message.photo:
        file_id = update.message.photo[-1].file_id
    elif update.message.document:
        file_id = update.message.document.file_id
        print("got document")

    # writing to a custom file

    print(file_id)
    url = f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={file_id}"
    response = requests.get(url).json()
    path = response['result']['file_path']
    print(path)
    url = f"https://api.telegram.org/file/bot{TOKEN}/{path}"
    response = requests.get(url)
    fname = path.split('/')[1]
    open(fname, "wb").write(response.content)

    USERDATA['link'] = upload_file(fname)
    insert_record(USERDATA)
    # Отвечаем на сообщение с фото
    update.message.reply_text(
        'Спасибо! Журнальная запись сохранена и отправлена Хэду твоего департмента ;)'
        'Спишемся через неделю'
    )
    return ConversationHandler.END


def skip_journal(update, _):
    # определяем пользователя
    user = update.message.from_user
    # Отвечаем на сообщение с пропущенным местоположением
    update.message.reply_text(
        'Ну что-ж... Я все равно напишу тебе перед дедлайном')

    return ConversationHandler.END

# Обрабатываем команду /cancel если пользователь отменил разговор


def cancel(update, _):
    # определяем пользователя
    user = update.message.from_user
    # Отвечаем на отказ поговорить
    update.message.reply_text(
        'Мое дело предложить - Ваше отказаться'
        ' Будет скучно - пиши.',
        reply_markup=ReplyKeyboardRemove())
    # Заканчиваем разговор.
    return ConversationHandler.END


if __name__ == '__main__':
    # Создаем Updater и передаем ему токен вашего бота.
    updater = Updater(TOKEN)
    # получаем диспетчера для регистрации обработчиков
    dispatcher = updater.dispatcher

    # Определяем обработчик разговоров `ConversationHandler`
    # с состояниями GENDER, PHOTO, LOCATION и BIO
    conv_handler = ConversationHandler(  # здесь строится логика разговора
        # точка входа в разговор
        entry_points=[CommandHandler('start', start), CommandHandler(
            'add_work', add_work), CommandHandler('file', journal)],
        # этапы разговора, каждый со своим списком обработчиков сообщений
        states={
            FULLNAME: [MessageHandler(Filters.text & ~Filters.command, fullname)],
            STUDENTID: [MessageHandler(Filters.text & ~Filters.command, studentid)],
            DEPARTMENT: [MessageHandler(Filters.regex('^(GLV|Management|Chassis|Suspension|Tractive|CV)$'), department)],
            JOURNAL: [MessageHandler(Filters.text & ~Filters.command, journal), CommandHandler('skip', skip_journal)],
            FILEUPLOAD: [MessageHandler(Filters.photo | Filters.video | Filters.document, fileupload)],
            LOGIN: [MessageHandler(Filters.text & ~Filters.command, login)],
        },
        # точка выхода из разговора
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Добавляем обработчик разговоров `conv_handler`
    dispatcher.add_handler(conv_handler)

    # Запуск бота
    updater.start_polling()
    updater.idle()
