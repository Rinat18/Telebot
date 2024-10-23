import telebot
from telebot import types
import sqlite3

bot = telebot.TeleBot('7336167231:AAEsPAJOoek8P7Rlbu0OZjIhQHXIRX8Xedc')  # Замените на свой токен

# Подключение к базе данных
conn = sqlite3.connect('real_estate.db', check_same_thread=False)
cursor = conn.cursor()

# Создание таблицы для хранения данных (если её ещё нет)
cursor.execute('''
CREATE TABLE IF NOT EXISTS apartments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_ids TEXT,
    name TEXT,
    rooms INTEGER,
    price REAL
)
''')
conn.commit()

user_data = {}  # Храним временные данные пользователя
user_state = {}  # Храним состояние пользователя (поиск или добавление квартиры)

# Обработка команды /start
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Добавить квартиру")
    btn2 = types.KeyboardButton("Поиск")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "👋 Привет! Я твой бот-помошник!", reply_markup=markup)

# Обработка нажатия на кнопку "Добавить квартиру"
@bot.message_handler(func=lambda message: message.text == "Добавить квартиру")
def add_apartment(message):
    user_state[message.chat.id] = 'adding'  # Устанавливаем состояние на добавление квартиры
    user_data[message.chat.id] = {'photos': []}  # Инициализируем временное хранилище для фото
    bot.send_message(message.chat.id, "Отправьте фотографии квартиры.")

# Обработка нажатия на кнопку "Поиск"
@bot.message_handler(func=lambda message: message.text == "Поиск")
def start_search(message):
    user_state[message.chat.id] = 'searching'  # Устанавливаем состояние на поиск
    bot.send_message(message.chat.id, "Введите название квартиры, количество комнат или цену для поиска.")

# Обработка фотографий
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id

    if user_state.get(chat_id) == 'adding':  # Проверяем, что пользователь в режиме добавления
        photo_file_id = message.photo[-1].file_id  # Получаем файл последней фотографии
        user_data[chat_id]['photos'].append(photo_file_id)  # Сохраняем фотографию

        bot.send_message(chat_id, "Фотография получена. Можете отправить еще фото или введите название квартиры.")
    else:
        bot.send_message(chat_id, "Для начала выберите 'Добавить квартиру'.")

# Обработка текстовых сообщений в режиме добавления или поиска
@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = message.chat.id

    if user_state.get(chat_id) == 'adding':  # Обработка добавления квартиры
        user_info = user_data[chat_id]

        if not user_info['photos']:  # Проверяем, что получены фотографии
            bot.send_message(chat_id, "Сначала отправьте фотографии.")
            return

        if 'name' not in user_info:  # Проверяем название квартиры
            user_info['name'] = message.text
            bot.send_message(chat_id, "Введите количество комнат.")
        elif 'rooms' not in user_info:  # Проверяем количество комнат
            if message.text.isdigit():  # Проверяем, что количество комнат это число
                user_info['rooms'] = int(message.text)
                bot.send_message(chat_id, "Введите цену квартиры.")
            else:
                bot.send_message(chat_id, "Пожалуйста, введите количество комнат в виде числа.")
        elif 'price' not in user_info:  # Проверяем цену
            try:
                user_info['price'] = float(message.text)

                # Сохраняем квартиру в базу данных
                cursor.execute('''
                    INSERT INTO apartments (file_ids, name, rooms, price)
                    VALUES (?, ?, ?, ?)
                ''', (','.join(user_info['photos']), user_info['name'], user_info['rooms'], user_info['price']))
                conn.commit()

                bot.send_message(chat_id, "Квартира успешно добавлена в базу!")
                del user_data[chat_id]  # Удаляем временные данные пользователя
                del user_state[chat_id]  # Сбрасываем состояние
            except ValueError:
                bot.send_message(chat_id, "Пожалуйста, введите цену в виде числа.")
    elif user_state.get(chat_id) == 'searching':  # Обработка поиска квартир
        query = message.text.strip()  # Получаем поисковый запрос

        if query.isdigit():  # Если запрос - это число, ищем по количеству комнат или цене
            cursor.execute('''
                SELECT file_ids, name, rooms, price FROM apartments 
                WHERE rooms = ? OR price = ?
            ''', (query, query))
        else:  # Иначе ищем по названию квартиры
            cursor.execute('''
                SELECT file_ids, name, rooms, price FROM apartments 
                WHERE name LIKE ?
            ''', (f'%{query}%',))

        results = cursor.fetchall()

        if results:
            for file_ids, name, rooms, price in results:
                photos = file_ids.split(',')  # Извлекаем список фото
                caption = f"Название: {name}\nКомнат: {rooms}\nЦена: {price}"
                for photo in photos:
                    bot.send_photo(message.chat.id, photo=photo, caption=caption)
        else:
            bot.send_message(chat_id, "Ничего не найдено.")
    else:
        bot.send_message(chat_id, "Для начала выберите 'Добавить квартиру' или 'Поиск'.")

print("Бот запущен и слушает команды...")
bot.polling(none_stop=True, interval=0)