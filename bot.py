import pandas as pd
import random
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# --- загрузка файла ---
df = pd.read_excel("greek A2 600 words.xlsx")

# чистим названия колонок
df.columns = df.columns.str.strip()

print("Колонки:", df.columns)

# ищем нужные колонки автоматически
greek_col = [col for col in df.columns if "греч" in col.lower()][0]
trans_col = [col for col in df.columns if "перев" in col.lower()][0]
example_gr = [col for col in df.columns if "пример" in col.lower() and "греч" in col.lower()]
example_ru = [col for col in df.columns if "пример" in col.lower() and "рус" in col.lower()]

example_gr = example_gr[0] if example_gr else None
example_ru = example_ru[0] if example_ru else None

# удаляем пустые строки
df = df.dropna(subset=[greek_col, trans_col])

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
            if w[greek_col] == word_text:
                return w

    return random.choice(words)


# --- отправка ---
async def send_word(update, context):
    user_id = update.effective_user.id
    user = user_data[user_id]

    word = get_word(user_id)
    user["current"] = word

    if user["mode"] == "gr_to_ru":
        text = f"🇬🇷 {word[greek_col]}"
    else:
        text = f"🇷🇺 {word[trans_col]}"

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

    # формируем ответ
    answer = f"""
Правильный ответ:
🇬🇷 {word[greek_col]}
🇷🇺 {word[trans_col]}
"""

    if example_gr:
        answer += f"\n{word[example_gr]}"
    if example_ru:
        answer += f"\n{word[example_ru]}"

    if text == "Знаю ✅":
        user["correct"] += 1
    else:
        user["wrong"] += 1

        key = word[greek_col]
        errors = user["errors"]
        errors[key] = errors.get(key, 0) + 1

    await update.message.reply_text(answer)
    await send_word(update, context)


# --- запуск ---
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.run_polling()
