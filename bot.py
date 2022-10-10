from time import ctime
from tkinter import PhotoImage
from webbrowser import get
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
import os
from functions import *


# Определяем константы этапов разговора
FULLNAME, STUDENTID, DEPARTMENT, JOURNAL, FILEUPLOAD, LOGIN, APPROVE = range(7)

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
    member = get_member(update.message.chat.id)
    if (member):
        update.message.reply_text(
        'Вы зашли как ' + member['Name'] + ' ' + member['Surname'] + ' ' + 
        '/report чтобы добавить запись')
        return ConversationHandler.END
    update.message.reply_text(
        'А пока, давай познакомимся. '
        'Как тебя зовут? (Имя и фамилия латиницей)')
    return FULLNAME


def fullname(update, _):
    USERDATA['chatId'] = update.message.chat.id
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
    USERDATA['chatId'] = update.message.chat.id
    ans = update.message.text
    if ans.isnumeric() == False or len(ans) != 9:
        update.message.reply_text(
            'Кажется, вы ввели некоректные данные:)\nStudent Id должен состоять из 9 цифр')
        return incorrect_id()
    USERDATA['id'] = ans
    member = get_member(USERDATA['chatId'])
    if member != None:
        update.message.reply_text('Мембер ' + member['Name'] + ' ' + member['Surname'] + ' уже существует. Чтобы добавить журнальную запись, напиши /report')
        return ConversationHandler.END
    
    reply_keyboard = [['GLV', 'Management',
                       'Chassis', 'Suspension', 'Tractive', 'CV']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(
        'Из какого ты департамента?', reply_markup=markup_key)

    return DEPARTMENT


def incorrect_id():
    return STUDENTID


def department(update, _):
    USERDATA['chatId'] = update.message.chat.id
    USERDATA['department'] = update.message.text
    update.message.reply_text(
        'Кратко опиши выполненные задачи (минимум 2 предложения)'
        'или /skip если еще не готов... я спрошу еще раз перед дедлайном',
        reply_markup=ReplyKeyboardRemove())
    insert_member(USERDATA)

    return JOURNAL


def add_work(update, _):
    USERDATA['chatId'] = update.message.chat.id
    member = get_member(USERDATA['chatId'])
    if member:
        USERDATA['id'] = member['StudentId']
        update.message.reply_text(
            '\nКратко опиши выполненные задачи (минимум 2 предложения)'
            'или /skip если еще не готов... я спрошу еще раз перед дедлайном')
        return JOURNAL
    update.message.reply_text('Не могу найти тебя в списке мемберов... /start чтобы зарегистрироваться')
    return ConversationHandler.END


def journal(update, _):
    USERDATA['journal'] = update.message.text
    update.message.reply_text(
        'Великолепная работа!\nА теперь скинь фото/видео/документ для отчета')
    return FILEUPLOAD


def fileupload(update, context):
    if update.message.video:
        file_id = update.message.video.file_id
    elif update.message.photo:
        file_id = update.message.photo[-1].file_id
    elif update.message.document:
        file_id = update.message.document.file_id


    # downloading file to local folder
    url = f"https://api.telegram.org/bot{TOKEN}/getFile?file_id={file_id}"
    response = requests.get(url).json()
    path = response['result']['file_path']
    url = f"https://api.telegram.org/file/bot{TOKEN}/{path}"
    response = requests.get(url)
    fname = path.split('/')[1]
    with open(fname, "wb") as f:
        f.write(response.content)

    # uploading file to google drive
    USERDATA['link'] = upload_file(fname)
    
    reply_keyboard = [['Да', 'Нет']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    
    update.message.reply_text(
        'Журнальная запись: ' + USERDATA['journal'] + '\nПодтвердить?', reply_markup=markup_key
    )
    chat_id = update.message.chat_id
    with open(fname, 'rb') as document:
        context.bot.send_document(chat_id, document)
    os.remove(fname)
    return APPROVE


def approve_journal(update, _):
    if (update.message.text == 'Да'):
        insert_record(USERDATA)
        update.message.reply_text(
            'Спасибо! Журнальная запись сохранена и отправлена Хэду твоего департмента ;)'
            'Спишемся через неделю', reply_markup=ReplyKeyboardRemove() 
        )
    else:
        update.message.reply_text(
            'Напиши /report чтобы заполнить журнал заново', reply_markup=ReplyKeyboardRemove()
        )
    return ConversationHandler.END


def skip_journal(update, _):
    # определяем пользователя
    user = update.message.from_user
    # Отвечаем на сообщение с пропущенным местоположением
    update.message.reply_text(
        'Ну что-ж... Я все равно напишу тебе перед дедлайном')

    return ConversationHandler.END


def cancel(update, _):
    # Отвечаем на отказ поговорить
    update.message.reply_text(
        'Мое дело предложить - Ваше отказаться'
        ' Будет скучно - пиши.',
        reply_markup=ReplyKeyboardRemove())
    # Заканчиваем разговор.
    return ConversationHandler.END

def get_reports(update, _):
    USERDATA['chatId'] = update.message.chat.id
    member = get_member(USERDATA['chatId'])
    if member['status'] == 'member':
        update.message.reply_text('Вы не обладаете достаточным статусом')
        return ConversationHandler.END
    
    reply_keyboard = [['Сегодня', 'Неделя', 'Все']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    
    update.message.reply_text(
        'Выберите период: ', reply_markup=markup_key
    )

    reports = get_reports_by_department(member['Department'])
    for rep in reports:
        update.message.reply_text('Имя: ' + rep['Name'] + 
                                    '\nФамилия: ' + rep['Surname'] +
                                    '\nЗапись: ' + rep['Journal'])
        fileid = 
    

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
            'report', add_work), CommandHandler('file', journal)],
        # этапы разговора, каждый со своим списком обработчиков сообщений
        states={
            FULLNAME: [MessageHandler(Filters.text & ~Filters.command, fullname)],
            STUDENTID: [MessageHandler(Filters.text & ~Filters.command, studentid)],
            DEPARTMENT: [MessageHandler(Filters.regex('^(GLV|Management|Chassis|Suspension|Tractive|CV)$'), department)],
            JOURNAL: [MessageHandler(Filters.text & ~Filters.command, journal), CommandHandler('skip', skip_journal)],
            FILEUPLOAD: [MessageHandler(Filters.photo | Filters.video | Filters.document, fileupload)],
            APPROVE: [MessageHandler(Filters.regex('^(Да|Нет)$'), approve_journal)],
        },
        # точка выхода из разговора
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Добавляем обработчик разговоров `conv_handler`
    dispatcher.add_handler(conv_handler)

    # Запуск бота
    updater.start_polling()
    updater.idle()
