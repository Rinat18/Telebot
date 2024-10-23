import asyncio
from telegram import Update
import sqlite3
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

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

# 7336167231:AAEsPAJOoek8P7Rlbu0OZjIhQHXIRX8Xedc

# Функция для обработки команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне фото с подписью и ценой.")
    print("Команда /start получена.")  # Отладочное сообщение

# Функция для обработки фотографий
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

# Функция для поиска фотографий по названию
async def search_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = ' '.join(context.args)  # Получаем поисковый запрос от пользователя
    cursor.execute('SELECT file_id, name, price FROM photos WHERE name LIKE ?', (f'%{query}%',))
    results = cursor.fetchall()

    if results:
        for file_id, name, price in results:
            await update.message.reply_photo(photo=file_id, caption=f"Название: {name}\nЦена: {price}")
    else:
        await update.message.reply_text(f"Ничего не найдено по запросу: {query}")

# Функция для поиска фотографий по цене
async def search_by_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        min_price, max_price = map(float, context.args)  # Ожидаем диапазон цен
    except ValueError:
        await update.message.reply_text("Введите диапазон цен, например: /search_by_price 100 500")
        return

    cursor.execute('SELECT file_id, name, price FROM photos WHERE price BETWEEN ? AND ?', (min_price, max_price))
    results = cursor.fetchall()

    if results:
        for file_id, name, price in results:
            await update.message.reply_photo(photo=file_id, caption=f"Название: {name}\nЦена: {price}")
    else:
        await update.message.reply_text(f"Ничего не найдено в диапазоне цен: {min_price} - {max_price}")

# Главная функция для запуска бота
async def main():
    application = ApplicationBuilder().token('YOUR_BOT_TOKEN').build()

    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CommandHandler("search_by_name", search_by_name))
    application.add_handler(CommandHandler("search_by_price", search_by_price))

    # Инициализация и запуск бота с опросом обновлений
    await application.initialize()
    await application.start()
    
    await application.updater.start_polling()  # Запуск опроса обновлений

    # Остановка бота
    await application.stop()

# Запуск основного события
if __name__ == '__main__':
    asyncio.run(main())