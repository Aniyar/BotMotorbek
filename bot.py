from tkinter import PhotoImage
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
import logging
from config import TOKEN
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
)

# Включим ведение журнала
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(department)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Определяем константы этапов разговора
FULLNAME, STUDENTID, DEPARTMENT, JOURNAL, FILEUPLOAD  = range(5)





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
        'Как тебя зовут? (Фамилия и имя латиницей)')
    return FULLNAME

def fullname(update, _):
    update.message.reply_text('Введи свой Student ID')
    user = update.message.from_user
    logger.info("ФИО: %s", update.message.text)
    return STUDENTID

def studentid(update, _):
    user = update.message.from_user
    logger.info("Student ID: %s", update.message.text)
    reply_keyboard = [['GLV', 'Management', 'Chassis', 'Suspension' , 'Tractive', 'CV']]
    markup_key = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text('Из какого ты департамента?', reply_markup=markup_key)
    
    return DEPARTMENT

def department(update, _):
    user = update.message.from_user
    logger.info("Department: %s", update.message.text)
    update.message.reply_text(
        'Кратко опиши выполненные задачи (минимум 2 предложения)'
        'или /skip если еще не готов... я спрошу еще раз перед дедлайном'
    )
    
    return JOURNAL

    
def journal(update, _):
    user = update.message.from_user
    logger.info("Journal: %s", update.message.text)
    update.message.reply_text('Великолепная работа!\nА теперь скинь фото/видео/презентацию для отчета')
    return FILEUPLOAD

def fileupload(update, _):
    # определяем пользователя
    user = update.message.from_user
    # захватываем фото 
    photo_file = update.message.photo[-1].get_file() 
    # скачиваем фото 
    photo_file.download(f'{user.first_name}_photo.jpg')
    # Пишем в журнал сведения о фото
    logger.info("Фотография %s: %s", user.first_name, f'{user.first_name}_photo.jpg')
    # Отвечаем на сообщение с фото
    update.message.reply_text(
        'Спасибо! Журнальная запись сохранена и отправлена Хэду твоего департмента ;)'
        'Спишемся через неделю'
    )
    return ConversationHandler.END

def skip_journal(update, _):
    # определяем пользователя
    user = update.message.from_user
    # Пишем в журнал сведения о местоположении
    logger.info("User %s did not write a jounal.", user.first_name)
    # Отвечаем на сообщение с пропущенным местоположением
    update.message.reply_text(
        'Ну что-ж... Я все равно напишу тебе перед дедлайном'
    )
    return ConversationHandler.END

# Обрабатываем команду /cancel если пользователь отменил разговор
def cancel(update, _):
    # определяем пользователя
    user = update.message.from_user
    # Пишем в журнал о том, что пользователь не разговорчивый
    logger.info("Пользователь %s отменил разговор.", user.first_name)
    # Отвечаем на отказ поговорить
    update.message.reply_text(
        'Мое дело предложить - Ваше отказаться'
        ' Будет скучно - пиши.', 
        reply_markup=ReplyKeyboardRemove()
    )
    # Заканчиваем разговор.
    return ConversationHandler.END 

if __name__ == '__main__':
    # Создаем Updater и передаем ему токен вашего бота.
    updater = Updater(TOKEN)
    # получаем диспетчера для регистрации обработчиков
    dispatcher = updater.dispatcher

    # Определяем обработчик разговоров `ConversationHandler` 
    # с состояниями GENDER, PHOTO, LOCATION и BIO
    conv_handler = ConversationHandler( # здесь строится логика разговора
        # точка входа в разговор
        entry_points=[CommandHandler('start', start)],
        # этапы разговора, каждый со своим списком обработчиков сообщений
        states={
            FULLNAME: [MessageHandler(Filters.text & ~Filters.command, fullname)],
            STUDENTID: [MessageHandler(Filters.text & ~Filters.command, studentid)],
            DEPARTMENT: [MessageHandler(Filters.regex('^(GLV|Management|Chassis|Suspension|Tractive|CV)$'), department)],
            JOURNAL: [MessageHandler(Filters.text & ~Filters.command, journal), CommandHandler('skip', skip_journal)],
            FILEUPLOAD: [MessageHandler(Filters.photo, fileupload)],
        },
        # точка выхода из разговора
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    # Добавляем обработчик разговоров `conv_handler`
    dispatcher.add_handler(conv_handler)

    # Запуск бота
    updater.start_polling()
    updater.idle()