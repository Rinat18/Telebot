import telebot
from telebot import types
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler
import sqlite3


bot = telebot.TeleBot('7336167231:AAEsPAJOoek8P7Rlbu0OZjIhQHXIRX8Xedc')  # Замените на свой токен

# Подключение к базе данных
conn = sqlite3.connect('photos.db')
cursor = conn.cursor()

# Создание таблицы для хранения данных (если её ещё нет)
cursor.execute('''
CREATE TABLE IF NOT EXISTS photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT,
    name TEXT,
    price REAL
)
''')
conn.commit()


@bot.message_handler(commands=['start'])
def start(message):
    print("Команда /start получена.")  # Логирование получения команды /start
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("👋 Поздороваться")
    markup.add(btn1)
    bot.send_message(message.from_user.id, "👋 Привет! Я твой бот-помошник!", reply_markup=markup)

# @bot.message_handler(content_types=['text', 'photo'])
# def get_text_messages(message):
#     print(f"Получено сообщение: {message.text}")  # Логирование полученного текста
#     print(f"Получено сообщение: {message.photo}")  # Логирование полученного текста

#     if message.text == '👋 Поздороваться':
#         markup = types.ReplyKeyboardMarkup(resize_keyboard=True)  # создание новых кнопок
#         btn1 = types.KeyboardButton('Как стать автором на Хабре?')
#         btn2 = types.KeyboardButton('Правила сайта')
#         btn3 = types.KeyboardButton('Советы по оформлению публикации')
#         markup.add(btn1, btn2, btn3)
#         bot.send_message(message.from_user.id, '❓ Задайте интересующий вас вопрос', reply_markup=markup)  # ответ бота
#     elif message.text == 'Как стать автором на Хабре?':
#         bot.send_message(message.from_user.id, 'Вы пишете первый пост, его проверяют модераторы, и, если всё хорошо, отправляют в основную ленту Хабра, где он набирает просмотры, комментарии и рейтинг. В дальнейшем премодерация уже не понадобится. Если с постом что-то не так, вас попросят его доработать.\n \nПолный текст можно прочитать по ' + '[ссылке](https://habr.com/ru/sandbox/start/)', parse_mode='Markdown')
#     elif message.text == 'Правила сайта':
#         bot.send_message(message.from_user.id, 'Прочитать правила сайта вы можете по ' + '[ссылке](https://habr.com/ru/docs/help/rules/)', parse_mode='Markdown')
#     elif message.text == 'Советы по оформлению публикации':
#         bot.send_message(message.from_user.id, 'Подробно про советы по оформлению публикаций прочитать по ' + '[ссылке](https://habr.com/ru/docs/companies/design/)', parse_mode='Markdown')
#     elif message.photo == 'photo':
#         bot.send_message(message.from_user.id, "Вы отправили фото!")

@bot.message_handler(content_types=['text', 'photo'])
def handle_message(message):
    if message.content_type == 'text':
        bot.send_message(message.chat.id, "Вы отправили текст!")
    elif message.content_type == 'photo':
        bot.send_message(message.chat.id, "Вы отправили фото!")


print("Бот запущен и слушает команды...")  # Лог о запуске бота
bot.polling(none_stop=True, interval=0)  # обязательная для работы бота часть

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = update.message.photo[-1].file_id  # Получаем файл фотографии
    caption = update.message.caption                   # Получаем подпись (название и цена)

    if caption:
        try:
            name, price = caption.split(',')           # Ожидаем, что пользователь вводит название и цену через запятую
            price = float(price.strip())
        except ValueError:
            await update.message.reply_text("Пожалуйста, отправьте название и цену через запятую.")
            return
    else:
        await update.message.reply_text("Пожалуйста, добавьте подпись с названием и ценой.")
        return

    # Сохраняем данные в базу данных
    cursor.execute('INSERT INTO photos (file_id, name, price) VALUES (?, ?, ?)', (photo_file, name.strip(), price))
    conn.commit()

    await update.message.reply_text(f"Фотография сохранена с названием '{name.strip()}' и ценой {price}.")