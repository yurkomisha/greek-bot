import pandas as pd
import random
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# 👉 Токен берём из Railway (переменная BOT_TOKEN)
TOKEN = os.getenv("BOT_TOKEN")

# Загружаем файл
df = pd.read_excel("greek A2 600 words.xlsx")
df = df.dropna(subset=["Греческое слово", "Перевод"])

words = df.to_dict(orient="records")

user_data = {}

keyboard = [["Знаю ✅", "Не знаю ❌"], ["Сменить режим 🔄", "Статистика 📊"]]
markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# --- старт ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    user_data[user_id] = {
        "current": None,
        "errors": {},
        "mode": "gr_to_ru",
        "correct": 0,
        "wrong": 0
    }

    await update.message.reply_text("Стартуем 🚀", reply_markup=markup)
    await send_word(update, context)


# --- выбор слова ---
def get_word(user_id):
    errors = user_data[user_id]["errors"]

    if errors and random.random() < 0.7:
        difficult = sorted(errors.items(), key=lambda x: -x[1])
        word_text = difficult[0][0]

        for w in words:
            if w["Греческое слово"] == word_text:
                return w

    return random.choice(words)


# --- отправка слова ---
async def send_word(update, context):
    user_id = update.effective_user.id
    user = user_data[user_id]

    word = get_word(user_id)
    user["current"] = word

    if user["mode"] == "gr_to_ru":
        text = f"🇬🇷 {word['Греческое слово']}"
    else:
        text = f"🇷🇺 {word['Перевод']}"

    await update.message.reply_text(text, reply_markup=markup)


# --- обработка ---
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    user = user_data[user_id]
    word = user["current"]

    if text == "Сменить режим 🔄":
        user["mode"] = "ru_to_gr" if user["mode"] == "gr_to_ru" else "gr_to_ru"
        await update.message.reply_text(f"Режим: {user['mode']}")
        await send_word(update, context)
        return

    if text == "Статистика 📊":
        await update.message.reply_text(
            f"✅ Правильно: {user['correct']}\n❌ Ошибки: {user['wrong']}"
        )
        return

    if not word:
        await send_word(update, context)
        return

    answer = f"""
Правильный ответ:
🇬🇷 {word['Греческое слово']}
🇷🇺 {word['Перевод']}

Пример:
{word['Пример (греч.)']}
{word['Пример (рус.)']}
"""

    if text == "Знаю ✅":
        user["correct"] += 1
    else:
        user["wrong"] += 1

        key = word["Греческое слово"]
        errors = user["errors"]
        errors[key] = errors.get(key, 0) + 1

    await update.message.reply_text(answer)
    await send_word(update, context)


# --- запуск ---
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.run_polling()
