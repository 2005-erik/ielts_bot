import json
import random
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties

# === Настройки ===
TOKEN = "8492348483:AAHsdxy_3NOhfiKI-k-pwCTF_PlQ4km_2H0"  # вставь сюда свой токен
ADMIN_ID = 6479398726  # вставь свой Telegram ID

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# === Глобальные переменные ===
user_levels = {}
user_languages = {}
words = []
quiz_data = []
support_waiting = set()

# === Загрузка данных ===
def load_data():
    global words, quiz_data
    try:
        with open("vocabulary.json", "r", encoding="utf-8") as f:
            words = json.load(f)
        with open("quiz.json", "r", encoding="utf-8") as f:
            quiz_data = json.load(f)
    except Exception as e:
        print("Ошибка загрузки данных:", e)

load_data()

# === Основные клавиатуры ===
def level_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 A1", callback_data="set_A1"),
         InlineKeyboardButton(text="🟡 A2", callback_data="set_A2")],
        [InlineKeyboardButton(text="🟠 B1", callback_data="set_B1"),
         InlineKeyboardButton(text="🔵 B2", callback_data="set_B2")],
        [InlineKeyboardButton(text="🟣 C1", callback_data="set_C1")]
    ])

def continue_keyboard(section: str):
    """Кнопка 'Продолжить'"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Продолжить", callback_data=f"continue_{section}")]
    ])

def language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇰🇿 Қазақша", callback_data="lang_kk"),
         InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru")]
    ])

# === Команда /start ===
@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        f"Сәлем, {message.from_user.first_name}! 👋\n"
        f"Выберите язык / Тілді таңдаңыз:",
        reply_markup=language_keyboard()
    )

# === Выбор языка ===
@dp.callback_query(lambda c: c.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    user_languages[callback.from_user.id] = lang
    if lang == "kk":
        text = "🇰🇿 Тілді таңдадыңыз: Қазақша.\n\nДеңгейіңізді таңдаңыз:"
    else:
        text = "🇷🇺 Язык выбран: Русский.\n\nВыберите свой уровень:"
    await callback.message.edit_text(text, reply_markup=level_keyboard())

# === Обработка выбора уровня ===
@dp.callback_query(lambda c: c.data.startswith("set_"))
async def set_level(callback: types.CallbackQuery):
    level = callback.data.split("_")[1]
    user_levels[callback.from_user.id] = level
    lang = user_languages.get(callback.from_user.id, "kk")

    if lang == "kk":
        msg = f"✅ Сіздің деңгейіңіз орнатылды: <b>{level}</b>\nҚазір /vocabulary немесе /quiz командасын қолдана аласыз!"
    else:
        msg = f"✅ Ваш уровень установлен: <b>{level}</b>\nТеперь вы можете использовать /vocabulary или /quiz!"
    await callback.message.edit_text(msg)

# === /help ===
@dp.message(Command("help"))
async def help_command(message: types.Message):
    text = (
        "📘 <b>Команды:</b>\n"
        "/start — начать заново\n"
        "/help — помощь\n"
        "/vocabulary — слова на сегодня\n"
        "/quiz — викторина\n"
        "/change_level — сменить уровень\n"
        "/faq — часто задаваемые вопросы\n"
        "/support — написать администратору\n"
        "/language — сменить язык"
    )
    await message.answer(text)

# === /language ===
@dp.message(Command("language"))
async def change_language(message: types.Message):
    await message.answer("Выберите язык / Тілді таңдаңыз:", reply_markup=language_keyboard())

# === /faq ===
@dp.message(Command("faq"))
async def faq_command(message: types.Message):
    text = (
        "💬 <b>Жиі қойылатын сұрақтар / Часто задаваемые вопросы:</b>\n\n"
        "1️⃣ Бұл бот не үшін? / Для чего бот?\n"
        "➡ IELTS сөздерін жаттауға және тест арқылы тексеруге арналған.\n\n"
        "2️⃣ Викторина қалай жұмыс істейді? / Как работает викторина?\n"
        "➡ Дұрыс жауап берсеңіз, бот келесі сұрақты береді.\n\n"
        "3️⃣ Қайта деңгейді қалай өзгертуге болады? / Как сменить уровень?\n"
        "➡ /change_level командасын қолданыңыз.\n\n"
        "4️⃣ Қолдау керек пе? / Нужна помощь?\n"
        "➡ /support командасын пайдаланыңыз."
    )
    await message.answer(text)

# === /change_level ===
@dp.message(Command("change_level"))
async def change_level(message: types.Message):
    await message.answer("Қай деңгейді таңдаңыз:", reply_markup=level_keyboard())

# === /vocabulary ===
@dp.message(Command("vocabulary"))
async def send_vocabulary(message: types.Message):
    user_id = message.from_user.id
    level = user_levels.get(user_id)

    if not level:
        await message.answer("⚠️ Алдымен деңгейді таңдаңыз / Сначала выберите уровень.")
        return

    level_words = [w for w in words if w["level"] == level]
    if not level_words:
        await message.answer("Бұл деңгейге сөздер қосылмаған 😔")
        return

    sample = random.sample(level_words, min(3, len(level_words)))
    text = f"📚 <b>{level} деңгейіндегі сөздер:</b>\n\n"
    for w in sample:
        text += f"<b>{w['word']}</b> — {w['translation']}\n<i>{w['example']}</i>\n\n"

    await message.answer(text, reply_markup=continue_keyboard("vocabulary"))

# === /quiz ===
@dp.message(Command("quiz"))
async def quiz_command(message: types.Message):
    user_id = message.from_user.id
    level = user_levels.get(user_id)

    if not level:
        await message.answer("⚠️ Алдымен деңгейді таңдаңыз / Сначала выберите уровень.")
        return

    level_quiz = [q for q in quiz_data if q["level"] == level]
    if not level_quiz:
        await message.answer("❌ Бұл деңгейге викторина қосылмаған.")
        return

    q = random.choice(level_quiz)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=o, callback_data=f"ans_{o}_{q['answer']}")] for o in q["options"]
        ]
    )

    await message.answer(f"🧠 {q['question']}", reply_markup=keyboard)

# === Проверка ответов викторины ===
@dp.callback_query(lambda c: c.data.startswith("ans_"))
async def quiz_answer(callback: types.CallbackQuery):
    _, chosen, correct = callback.data.split("_", 2)
    if chosen == correct:
        await callback.message.edit_text(f"✅ Дұрыс жауап! <b>{correct}</b>", reply_markup=continue_keyboard("quiz"))
    else:
        await callback.message.edit_text(f"❌ Қате. Дұрыс жауап: <b>{correct}</b>", reply_markup=continue_keyboard("quiz"))

# === Новые функции для callback-кнопок ===
async def vocabulary_from_callback(user_id, message):
    level = user_levels.get(user_id)
    if not level:
        await message.edit_text("⚠️ Алдымен деңгейді таңдаңыз / Сначала выберите уровень.")
        return

    level_words = [w for w in words if w["level"] == level]
    if not level_words:
        await message.edit_text("Бұл деңгейге сөздер қосылмаған 😔")
        return

    sample = random.sample(level_words, min(3, len(level_words)))
    text = f"📚 <b>{level} деңгейіндегі сөздер:</b>\n\n"
    for w in sample:
        text += f"<b>{w['word']}</b> — {w['translation']}\n<i>{w['example']}</i>\n\n"

    await message.edit_text(text, reply_markup=continue_keyboard("vocabulary"))

async def quiz_command_from_callback(user_id, message):
    level = user_levels.get(user_id)
    if not level:
        await message.edit_text("⚠️ Алдымен деңгейді таңдаңыз / Сначала выберите уровень.")
        return

    level_quiz = [q for q in quiz_data if q["level"] == level]
    if not level_quiz:
        await message.edit_text("❌ Бұл деңгейге викторина қосылмаған.")
        return

    q = random.choice(level_quiz)
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=o, callback_data=f"ans_{o}_{q['answer']}")] for o in q["options"]
        ]
    )

    await message.edit_text(f"🧠 {q['question']}", reply_markup=keyboard)

# === Продолжить после слов или викторины ===
@dp.callback_query(lambda c: c.data.startswith("continue_"))
async def continue_action(callback: types.CallbackQuery):
    section = callback.data.split("_")[1]
    user_id = callback.from_user.id
    message = callback.message

    if section == "vocabulary":
        await quiz_command_from_callback(user_id, message)
    elif section == "quiz":
        await vocabulary_from_callback(user_id, message)

# === /support ===
@dp.message(Command("support"))
async def support_command(message: types.Message):
    support_waiting.add(message.from_user.id)
    await message.answer("💬 Сұрағыңызды жазыңыз — әкімшіге жіберемін.")

# === Сообщения в поддержку ===
@dp.message(lambda m: m.from_user.id not in [ADMIN_ID])
async def handle_support_message(message: types.Message):
    if message.from_user.id in support_waiting:
        await bot.send_message(
            ADMIN_ID,
            f"📩 <b>Хабарлама от {message.from_user.full_name}</b>\n🆔 <code>{message.from_user.id}</code>\n\n{message.text}"
        )
        await message.answer("✅ Сұрағыңыз жіберілді. Әкімшінің жауабын күтіңіз.")
        support_waiting.remove(message.from_user.id)

# === /reply (ответ администратора) ===
@dp.message(Command("reply"))
async def admin_reply(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Сізде бұл командаға рұқсат жоқ.")
        return

    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("Қолдану түрі: /reply user_id жауап_мәтіні")
        return

    user_id, reply_text = parts[1], parts[2]
    try:
        await bot.send_message(user_id, f"💬 <b>Әкімшіден жауап:</b>\n{reply_text}")
        await message.answer("✅ Хабарлама жіберілді.")
    except Exception as e:
        await message.answer(f"⚠️ Жіберу қатесі: {e}")

# === Регистрация команд Telegram (для подсказок как у BotFather) ===
async def set_bot_commands():
    commands = [
        BotCommand(command="start", description="Бастау / Start"),
        BotCommand(command="help", description="Көмек / Help"),
        BotCommand(command="vocabulary", description="Сөздер / Words"),
        BotCommand(command="quiz", description="Викторина / Quiz"),
        BotCommand(command="change_level", description="Деңгейді өзгерту / Change level"),
        BotCommand(command="faq", description="FAQ / Сұрақтар"),
        BotCommand(command="support", description="Қолдау / Support"),
        BotCommand(command="language", description="Тілді өзгерту / Change language"),
    ]
    await bot.set_my_commands(commands)

# === Запуск ===
async def main():
    print("🤖 Бот іске қосылды және дайын жұмысқа...")
    await set_bot_commands()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
