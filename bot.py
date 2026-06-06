"""
AI FOR BUSINESS — Telegram Bot (Groq API - БЕСПЛАТНО)
======================================================
Установка:
  pip install pyTelegramBotAPI groq requests

Запуск:
  python bot.py
"""

import telebot
from groq import Groq
import requests
import os
import tempfile
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ══════════════════════════════════════
#  🔑 КЛЮЧИ БЕРУТСЯ ИЗ ПЕРЕМЕННЫХ СРЕДЫ
# ══════════════════════════════════════
import os
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_KEY       = os.environ.get("GROQ_KEY")
# ══════════════════════════════════════

client = Groq(api_key=GROQ_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

user_lang = {}
user_mode = {}

LANG_PROMPTS = {
    "ru": "Ты — AI FOR BUSINESS, умный серьёзный дружелюбный бизнес-ассистент. Специализируешься на программировании, риэлторских вопросах и бизнесе. Если спросят 'Кто ты?' — скажи: 'Я AI FOR BUSINESS — ваш персональный бизнес-ассистент.' Отвечай на русском. Иногда добавляй лёгкий юмор.",
    "en": "You are AI FOR BUSINESS, a smart friendly business assistant specializing in programming, real estate, business. If asked 'Who are you?' say: 'I am AI FOR BUSINESS — your personal business assistant.' Respond in English.",
    "kz": "Сен — AI FOR BUSINESS, ақылды бизнес-көмекшісің. Бағдарламалау, жылжымайтын мүлік, бизнес. 'Сен кімсің?' десе: 'Мен AI FOR BUSINESS — сіздің бизнес-көмекшіңізмін.' Қазақша жауап бер.",
    "tr": "Sen AI FOR BUSINESS'sın, akıllı bir iş asistanısın. Programlama, gayrimenkul, iş. 'Sen kimsin?' diye sorulursa: 'Ben AI FOR BUSINESS — kişisel iş asistanınım.' Türkçe cevap ver."
}

def get_lang(uid): return user_lang.get(uid, "ru")
def get_mode(uid): return user_mode.get(uid, "chat")

def main_keyboard(uid):
    lang = get_lang(uid)
    mode = get_mode(uid)
    kb = InlineKeyboardMarkup(row_width=3)
    kb.add(
        InlineKeyboardButton("💬 Чат" + (" ✅" if mode=="chat" else ""), callback_data="mode_chat"),
        InlineKeyboardButton("🎨 Картинка" + (" ✅" if mode=="image" else ""), callback_data="mode_image"),
        InlineKeyboardButton("🎵 Музыка" + (" ✅" if mode=="music" else ""), callback_data="mode_music"),
    )
    kb.add(
        InlineKeyboardButton("🇷🇺 RU" + (" ✅" if lang=="ru" else ""), callback_data="lang_ru"),
        InlineKeyboardButton("🇬🇧 EN" + (" ✅" if lang=="en" else ""), callback_data="lang_en"),
        InlineKeyboardButton("🇰🇿 KZ" + (" ✅" if lang=="kz" else ""), callback_data="lang_kz"),
        InlineKeyboardButton("🇹🇷 TR" + (" ✅" if lang=="tr" else ""), callback_data="lang_tr"),
    )
    return kb

# ── /start ──
@bot.message_handler(commands=["start"])
def start(msg):
    uid = msg.from_user.id
    user_lang[uid] = "ru"
    user_mode[uid] = "chat"
    bot.send_message(msg.chat.id,
        "👋 Привет! Я *AI FOR BUSINESS* — ваш умный бизнес-ассистент!\n\n"
        "💬 Чат • 🎨 Картинки • 🎵 Музыка\n"
        "📎 Документы • 🖼️ Анализ фото\n"
        "🇷🇺 RU • 🇬🇧 EN • 🇰🇿 KZ • 🇹🇷 TR\n\n"
        "Выберите режим и язык 👇",
        parse_mode="Markdown",
        reply_markup=main_keyboard(uid)
    )

# ── /menu ──
@bot.message_handler(commands=["menu"])
def menu(msg):
    bot.send_message(msg.chat.id, "⚙️ Настройки:", reply_markup=main_keyboard(msg.from_user.id))

# ── CALLBACKS ──
@bot.callback_query_handler(func=lambda c: c.data.startswith("mode_") or c.data.startswith("lang_"))
def handle_callback(call):
    uid = call.from_user.id
    if call.data.startswith("mode_"):
        user_mode[uid] = call.data.replace("mode_", "")
        mode = user_mode[uid]
        hints = {
            "chat": "💬 Режим чата. Задайте вопрос!",
            "image": "🎨 Режим картинок. Опишите что нарисовать!",
            "music": "🎵 Режим музыки. Опишите какую музыку создать!"
        }
        bot.answer_callback_query(call.id, hints.get(mode, ""))
    elif call.data.startswith("lang_"):
        user_lang[uid] = call.data.replace("lang_", "")
        bot.answer_callback_query(call.id, "Язык изменён! ✅")
    try:
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_keyboard(uid)
        )
    except: pass

# ── ТЕКСТ ──
@bot.message_handler(content_types=["text"])
def handle_text(msg):
    uid = msg.from_user.id
    text = msg.text
    if text.startswith("/"): return
    mode = get_mode(uid)
    lang = get_lang(uid)
    if mode == "image":
        generate_image(msg, text)
    elif mode == "music":
        generate_music(msg, text)
    else:
        chat_response(msg, text, lang)

# ── ЧАТ через Groq ──
def chat_response(msg, text, lang):
    thinking = bot.send_message(msg.chat.id, "⏳ Думаю...")
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": LANG_PROMPTS.get(lang, LANG_PROMPTS["ru"])},
                {"role": "user", "content": text}
            ],
            max_tokens=1000
        )
        reply = response.choices[0].message.content
        bot.delete_message(msg.chat.id, thinking.message_id)
        for i in range(0, len(reply), 4000):
            bot.send_message(msg.chat.id, reply[i:i+4000])
    except Exception as e:
        bot.edit_message_text(f"⚠️ Ошибка: {str(e)[:150]}", msg.chat.id, thinking.message_id)

# ── КАРТИНКИ (Pollinations - бесплатно) ──
def generate_image(msg, prompt):
    thinking = bot.send_message(msg.chat.id, "🎨 Генерирую картинку...")
    try:
        import random
        seed = random.randint(1, 99999)
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?width=768&height=512&seed={seed}&nologo=true"
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            bot.delete_message(msg.chat.id, thinking.message_id)
            bot.send_photo(msg.chat.id, resp.content, caption=f"🎨 {prompt}")
        else:
            bot.edit_message_text("⚠️ Попробуйте другой запрос.", msg.chat.id, thinking.message_id)
    except Exception as e:
        bot.edit_message_text(f"⚠️ Ошибка: {str(e)[:100]}", msg.chat.id, thinking.message_id)

# ── МУЗЫКА (Pollinations - бесплатно) ──
def generate_music(msg, prompt):
    thinking = bot.send_message(msg.chat.id, "🎵 Создаю музыку...")
    try:
        url = f"https://audio.pollinations.ai/{requests.utils.quote(prompt)}"
        resp = requests.get(url, timeout=60)
        if resp.status_code == 200:
            bot.delete_message(msg.chat.id, thinking.message_id)
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                f.write(resp.content)
                f.flush()
                bot.send_audio(msg.chat.id, open(f.name, "rb"), title=prompt[:50], performer="AI FOR BUSINESS")
            os.unlink(f.name)
        else:
            bot.edit_message_text("⚠️ Ошибка генерации музыки.", msg.chat.id, thinking.message_id)
    except Exception as e:
        bot.edit_message_text(f"⚠️ Ошибка: {str(e)[:100]}", msg.chat.id, thinking.message_id)

# ── ФОТО ──
@bot.message_handler(content_types=["photo"])
def handle_photo(msg):
    uid = msg.from_user.id
    lang = get_lang(uid)
    thinking = bot.send_message(msg.chat.id, "🖼️ Анализирую фото...")
    try:
        caption = msg.caption or "Опиши что на фото. Если связано с бизнесом или недвижимостью — дай профессиональный комментарий."
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": LANG_PROMPTS.get(lang, LANG_PROMPTS["ru"])},
                {"role": "user", "content": caption}
            ],
            max_tokens=500
        )
        bot.delete_message(msg.chat.id, thinking.message_id)
        bot.send_message(msg.chat.id, response.choices[0].message.content)
    except Exception as e:
        bot.edit_message_text(f"⚠️ Ошибка: {str(e)[:100]}", msg.chat.id, thinking.message_id)

# ── ДОКУМЕНТЫ ──
@bot.message_handler(content_types=["document"])
def handle_doc(msg):
    uid = msg.from_user.id
    lang = get_lang(uid)
    fname = msg.document.file_name
    thinking = bot.send_message(msg.chat.id, f"📄 Анализирую {fname}...")
    try:
        file_info = bot.get_file(msg.document.file_id)
        file_data = bot.download_file(file_info.file_path)
        text_content = ""
        if fname.endswith(".txt"):
            text_content = file_data.decode("utf-8", errors="ignore")[:3000]
        prompt = f"Файл '{fname}' получен."
        if text_content:
            prompt += f"\nСодержимое:\n{text_content}\nПроанализируй и дай краткое резюме."
        else:
            prompt += f"\nДай совет по работе с таким типом файла в бизнесе."
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": LANG_PROMPTS.get(lang, LANG_PROMPTS["ru"])},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600
        )
        bot.delete_message(msg.chat.id, thinking.message_id)
        bot.send_message(msg.chat.id, response.choices[0].message.content)
    except Exception as e:
        bot.edit_message_text(f"⚠️ Ошибка: {str(e)[:100]}", msg.chat.id, thinking.message_id)

# ── ГОЛОС ──
@bot.message_handler(content_types=["voice"])
def handle_voice(msg):
    bot.send_message(msg.chat.id, "🎙️ Голосовое получено!\nПожалуйста напишите текстом. 📝")

# ── ЗАПУСК ──
print("=" * 40)
print("🤖 AI FOR BUSINESS Bot запущен!")
print("📱 @bayanchatbot")
print("✅ Groq API — БЕСПЛАТНО")
print("Нажмите Ctrl+C для остановки")
print("=" * 40)
bot.infinity_polling()
