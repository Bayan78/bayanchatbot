"""
AI FOR BUSINESS — Telegram Bot
================================
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
#  🔑 КЛЮЧИ ИЗ ПЕРЕМЕННЫХ СРЕДЫ
# ══════════════════════════════════════
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_KEY       = os.environ.get("GROQ_KEY")
# ══════════════════════════════════════

client = Groq(api_key=GROQ_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

user_lang = {}
user_mode = {}

LANG_PROMPTS = {
    "ru": "Ты — AI FOR BUSINESS, умный серьёзный дружелюбный бизнес-ассистент. Тебя создал Баянбек. Ты являешься личным помощником и консультантом Баянбека. Специализируешься на программировании, риэлторских вопросах и бизнесе. Если спросят 'Кто ты?' — отвечай: 'Я AI FOR BUSINESS — личный ассистент-консультант Баянбека. Меня создал Баянбек.' Отвечай на русском. Иногда добавляй лёгкий юмор.",
    "en": "You are AI FOR BUSINESS, created by Bayantek. You are the personal assistant and consultant of Bayantek. Specializing in programming, real estate, business. If asked 'Who are you?' say: 'I am AI FOR BUSINESS — personal assistant-consultant of Bayantek. I was created by Bayantek.' Respond in English.",
    "kz": "Сен — AI FOR BUSINESS, Баянбек жасады. Баянбектің жеке көмекші-кеңесшісісің. 'Сен кімсің?' десе: 'Мен AI FOR BUSINESS — Баянбектің жеке ассистентімін. Мені Баянбек жасады.' Қазақша жауап бер.",
    "tr": "Sen AI FOR BUSINESS'sın, Bayantek tarafından yaratıldın. 'Sen kimsin?' diye sorulursa: 'Ben AI FOR BUSINESS — Bayantek'in kişisel asistanıyım.' Türkçe cevap ver."
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
        "👋 Привет! Я *AI FOR BUSINESS* — личный ассистент Баянбека!\n\n"
        "💬 Чат — отвечаю на любые вопросы\n"
        "🎙️ Голос — говорите, я пойму\n"
        "🎨 Картинки — генерирую по описанию\n"
        "🎵 Музыка — создаю по запросу\n"
        "📎 Файлы и фото — анализирую\n\n"
        "🌍 RU • EN • KZ • TR\n\n"
        "Всё *бесплатно*! Задайте вопрос 👇",
        parse_mode="Markdown",
        reply_markup=main_keyboard(uid)
    )

@bot.message_handler(commands=["menu"])
def menu(msg):
    bot.send_message(msg.chat.id, "⚙️ Меню:", reply_markup=main_keyboard(msg.from_user.id))

# ── CALLBACKS ──
@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    uid = call.from_user.id
    if call.data.startswith("mode_"):
        user_mode[uid] = call.data.replace("mode_", "")
        hints = {
            "chat": "💬 Режим чата!",
            "image": "🎨 Опишите картинку!",
            "music": "🎵 Опишите музыку!"
        }
        bot.answer_callback_query(call.id, hints.get(user_mode[uid], ""))
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
    if mode == "image": generate_image(msg, text)
    elif mode == "music": generate_music(msg, text)
    else: chat_response(msg, text, lang)

# ── ЧАТ ──
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

# ── ГОЛОСОВЫЕ (Groq Whisper) ──
@bot.message_handler(content_types=["voice"])
def handle_voice(msg):
    uid = msg.from_user.id
    lang = get_lang(uid)
    thinking = bot.send_message(msg.chat.id, "🎙️ Распознаю голос...")
    try:
        file_info = bot.get_file(msg.voice.file_id)
        file_data = bot.download_file(file_info.file_path)
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
            f.write(file_data)
            tmp_path = f.name
        with open(tmp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=("voice.ogg", audio_file, "audio/ogg"),
                model="whisper-large-v3",
                language={"ru":"ru","en":"en","kz":"kk","tr":"tr"}.get(lang,"ru")
            )
        os.unlink(tmp_path)
        text = transcription.text
        bot.edit_message_text(
            f"🎙️ Вы сказали: *{text}*",
            msg.chat.id, thinking.message_id,
            parse_mode="Markdown"
        )
        chat_response(msg, text, lang)
    except Exception as e:
        bot.edit_message_text(
            f"⚠️ Ошибка распознавания голоса: {str(e)[:100]}",
            msg.chat.id, thinking.message_id
        )

# ── КАРТИНКИ ──
def generate_image(msg, prompt):
    thinking = bot.send_message(msg.chat.id, "🎨 Генерирую картинку...")
    try:
        import random
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?width=768&height=512&seed={random.randint(1,99999)}&nologo=true"
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            bot.delete_message(msg.chat.id, thinking.message_id)
            bot.send_photo(msg.chat.id, resp.content, caption=f"🎨 {prompt}")
        else:
            bot.edit_message_text("⚠️ Попробуйте другой запрос.", msg.chat.id, thinking.message_id)
    except Exception as e:
        bot.edit_message_text(f"⚠️ Ошибка: {str(e)[:100]}", msg.chat.id, thinking.message_id)

# ── МУЗЫКА ──
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
                bot.send_audio(msg.chat.id, open(f.name,"rb"), title=prompt[:50], performer="AI FOR BUSINESS")
            os.unlink(f.name)
        else:
            bot.edit_message_text("⚠️ Ошибка генерации.", msg.chat.id, thinking.message_id)
    except Exception as e:
        bot.edit_message_text(f"⚠️ Ошибка: {str(e)[:100]}", msg.chat.id, thinking.message_id)

# ── ФОТО ──
@bot.message_handler(content_types=["photo"])
def handle_photo(msg):
    uid = msg.from_user.id
    lang = get_lang(uid)
    thinking = bot.send_message(msg.chat.id, "🖼️ Анализирую фото...")
    try:
        caption = msg.caption or "Опиши что на фото профессионально."
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
            prompt += f"\nСодержимое:\n{text_content}\nАнализ:"
        else:
            prompt += f"\nДай совет по работе с этим типом файла в бизнесе."
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

print("=" * 40)
print("🤖 AI FOR BUSINESS Bot запущен!")
print("📱 @bayanchatbot")
print("✅ Groq + Whisper голос — БЕСПЛАТНО")
print("Нажмите Ctrl+C для остановки")
print("=" * 40)
bot.infinity_polling()
