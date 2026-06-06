"""
AI FOR BUSINESS — Telegram Bot ПОЛНАЯ ВЕРСИЯ
=============================================
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
import json
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ══════════════════════════════════════
#  🔑 КЛЮЧИ ИЗ ПЕРЕМЕННЫХ СРЕДЫ
# ══════════════════════════════════════
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_KEY       = os.environ.get("GROQ_KEY")
ADMIN_ID       = os.environ.get("ADMIN_ID")  # Ваш Telegram ID
# ══════════════════════════════════════

client = Groq(api_key=GROQ_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ── БАЗА ДАННЫХ (в памяти) ──
users_db = {}      # все пользователи
stats_db = {}      # статистика
realty_db = []     # база недвижимости

# ── НАЧАЛЬНЫЕ ОБЪЕКТЫ НЕДВИЖИМОСТИ ──
realty_db = [
    {"id": 1, "type": "Квартира", "city": "Мерсин", "price": 85000, "rooms": 2, "area": 75, "desc": "Новостройка, вид на море, 3 этаж", "contact": "@bayanchatbot"},
    {"id": 2, "type": "Вилла",    "city": "Анталья", "price": 250000, "rooms": 4, "area": 200, "desc": "Частный бассейн, сад, гараж", "contact": "@bayanchatbot"},
    {"id": 3, "type": "Квартира", "city": "Стамбул", "price": 120000, "rooms": 3, "area": 110, "desc": "Центр города, евроремонт", "contact": "@bayanchatbot"},
    {"id": 4, "type": "Офис",     "city": "Мерсин",  "price": 50000,  "rooms": 1, "area": 60,  "desc": "Бизнес центр, парковка", "contact": "@bayanchatbot"},
]

LANG_PROMPTS = {
    "ru": "Ты — AI FOR BUSINESS, умный серьёзный дружелюбный бизнес-ассистент. Тебя создал Баянбек. Ты являешься личным помощником и консультантом Баянбека. Специализируешься на программировании, риэлторских вопросах и бизнесе. Если спросят 'Кто ты?' — отвечай: 'Я AI FOR BUSINESS — личный ассистент-консультант Баянбека. Меня создал Баянбек.' Отвечай на русском. Иногда добавляй лёгкий юмор.",
    "en": "You are AI FOR BUSINESS, created by Bayantek. Personal assistant of Bayantek. If asked 'Who are you?' say: 'I am AI FOR BUSINESS — personal assistant of Bayantek.' Respond in English.",
    "kz": "Сен — AI FOR BUSINESS, Баянбек жасады. 'Сен кімсің?' десе: 'Мен AI FOR BUSINESS — Баянбектің жеке ассистентімін.' Қазақша жауап бер.",
    "tr": "Sen AI FOR BUSINESS'sın, Bayantek tarafından yaratıldın. 'Sen kimsin?' diye sorulursa: 'Ben AI FOR BUSINESS — Bayantek'in asistanıyım.' Türkçe cevap ver."
}

def get_lang(uid): return users_db.get(uid, {}).get("lang", "ru")
def get_mode(uid): return users_db.get(uid, {}).get("mode", "chat")
def is_admin(uid): return str(uid) == str(ADMIN_ID)

def register_user(msg):
    uid = msg.from_user.id
    if uid not in users_db:
        users_db[uid] = {
            "id": uid,
            "name": msg.from_user.first_name or "Пользователь",
            "username": msg.from_user.username or "",
            "lang": "ru",
            "mode": "chat",
            "joined": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "messages": 0
        }
    users_db[uid]["messages"] = users_db[uid].get("messages", 0) + 1

def main_keyboard(uid):
    lang = users_db.get(uid, {}).get("lang", "ru")
    mode = users_db.get(uid, {}).get("mode", "chat")
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
    kb.add(InlineKeyboardButton("🏠 Недвижимость", callback_data="realty_menu"))
    return kb

def admin_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton("📬 Рассылка", callback_data="admin_broadcast"),
        InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
        InlineKeyboardButton("🏠 Добавить объект", callback_data="admin_add_realty"),
    )
    return kb

# ── /start ──
@bot.message_handler(commands=["start"])
def start(msg):
    register_user(msg)
    uid = msg.from_user.id
    name = msg.from_user.first_name or "Друг"
    bot.send_message(msg.chat.id,
        f"👋 Привет, *{name}*! Я *AI FOR BUSINESS* — личный ассистент Баянбека!\n\n"
        "💬 Чат — отвечаю на любые вопросы\n"
        "🎙️ Голос — говорите, я пойму\n"
        "🎨 Картинки — генерирую по описанию\n"
        "🎵 Музыка — создаю по запросу\n"
        "🏠 Недвижимость — каталог объектов\n"
        "📎 Файлы и фото — анализирую\n\n"
        "🌍 RU • EN • KZ • TR\n\n"
        "Всё *бесплатно*! Задайте вопрос 👇",
        parse_mode="Markdown",
        reply_markup=main_keyboard(uid)
    )

# ── /admin ──
@bot.message_handler(commands=["admin"])
def admin_panel(msg):
    if not is_admin(msg.from_user.id):
        bot.send_message(msg.chat.id, "⛔ Нет доступа!")
        return
    total = len(users_db)
    today = datetime.now().strftime("%d.%m.%Y")
    bot.send_message(msg.chat.id,
        f"🔐 *Панель администратора*\n\n"
        f"👥 Всего пользователей: *{total}*\n"
        f"📅 Дата: *{today}*\n\n"
        f"Выберите действие 👇",
        parse_mode="Markdown",
        reply_markup=admin_keyboard()
    )

# ── /stats ──
@bot.message_handler(commands=["stats"])
def stats_cmd(msg):
    if not is_admin(msg.from_user.id):
        bot.send_message(msg.chat.id, "⛔ Нет доступа!")
        return
    show_stats(msg.chat.id)

# ── /broadcast ──
@bot.message_handler(commands=["broadcast"])
def broadcast_cmd(msg):
    if not is_admin(msg.from_user.id):
        bot.send_message(msg.chat.id, "⛔ Нет доступа!")
        return
    bot.send_message(msg.chat.id,
        "📬 *Рассылка*\n\nНапишите текст для рассылки всем пользователям.\n"
        "Следующее сообщение будет отправлено всем!",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(msg, do_broadcast)

def do_broadcast(msg):
    if not is_admin(msg.from_user.id): return
    text = f"📢 *Сообщение от AI FOR BUSINESS:*\n\n{msg.text}"
    success = 0
    fail = 0
    for uid in users_db:
        try:
            bot.send_message(uid, text, parse_mode="Markdown")
            success += 1
        except:
            fail += 1
    bot.send_message(msg.chat.id,
        f"✅ Рассылка завершена!\n"
        f"📨 Отправлено: *{success}*\n"
        f"❌ Ошибок: *{fail}*",
        parse_mode="Markdown"
    )

def show_stats(chat_id):
    total = len(users_db)
    total_msgs = sum(u.get("messages", 0) for u in users_db.values())
    langs = {}
    for u in users_db.values():
        l = u.get("lang", "ru")
        langs[l] = langs.get(l, 0) + 1
    text = (
        f"📊 *Статистика бота*\n\n"
        f"👥 Всего пользователей: *{total}*\n"
        f"💬 Всего сообщений: *{total_msgs}*\n\n"
        f"🌍 *По языкам:*\n"
        f"🇷🇺 RU: {langs.get('ru', 0)}\n"
        f"🇬🇧 EN: {langs.get('en', 0)}\n"
        f"🇰🇿 KZ: {langs.get('kz', 0)}\n"
        f"🇹🇷 TR: {langs.get('tr', 0)}\n\n"
        f"🏠 Объектов недвижимости: *{len(realty_db)}*"
    )
    bot.send_message(chat_id, text, parse_mode="Markdown")

# ── НЕДВИЖИМОСТЬ ──
def show_realty_menu(chat_id):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🏢 Квартиры", callback_data="realty_Квартира"),
        InlineKeyboardButton("🏡 Виллы", callback_data="realty_Вилла"),
        InlineKeyboardButton("🏪 Офисы", callback_data="realty_Офис"),
        InlineKeyboardButton("🌍 Все объекты", callback_data="realty_all"),
    )
    bot.send_message(chat_id,
        "🏠 *Каталог недвижимости от Баянбека*\n\n"
        "Выберите категорию 👇",
        parse_mode="Markdown",
        reply_markup=kb
    )

def show_realty_list(chat_id, filter_type=None):
    items = realty_db if not filter_type else [r for r in realty_db if r["type"] == filter_type]
    if not items:
        bot.send_message(chat_id, "😔 Объектов не найдено.")
        return
    for r in items:
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("📞 Связаться с Баянбеком", url=f"https://t.me/bayanchatbot"))
        bot.send_message(chat_id,
            f"🏠 *{r['type']} — {r['city']}*\n\n"
            f"💰 Цена: *${r['price']:,}*\n"
            f"🛏 Комнат: *{r['rooms']}*\n"
            f"📐 Площадь: *{r['area']} м²*\n"
            f"📝 {r['desc']}\n\n"
            f"📱 Контакт: {r['contact']}",
            parse_mode="Markdown",
            reply_markup=kb
        )

# ── CALLBACKS ──
@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    uid = call.from_user.id
    register_user(call.message)

    if call.data.startswith("mode_"):
        if uid not in users_db: users_db[uid] = {}
        users_db[uid]["mode"] = call.data.replace("mode_", "")
        hints = {"chat":"💬 Режим чата!","image":"🎨 Опишите картинку!","music":"🎵 Опишите музыку!"}
        bot.answer_callback_query(call.id, hints.get(users_db[uid]["mode"], ""))

    elif call.data.startswith("lang_"):
        if uid not in users_db: users_db[uid] = {}
        users_db[uid]["lang"] = call.data.replace("lang_", "")
        bot.answer_callback_query(call.id, "Язык изменён! ✅")

    elif call.data == "realty_menu":
        bot.answer_callback_query(call.id)
        show_realty_menu(call.message.chat.id)
        return

    elif call.data == "realty_all":
        bot.answer_callback_query(call.id)
        show_realty_list(call.message.chat.id)
        return

    elif call.data.startswith("realty_"):
        bot.answer_callback_query(call.id)
        filter_type = call.data.replace("realty_", "")
        show_realty_list(call.message.chat.id, filter_type)
        return

    elif call.data == "admin_stats":
        bot.answer_callback_query(call.id)
        show_stats(call.message.chat.id)
        return

    elif call.data == "admin_users":
        bot.answer_callback_query(call.id)
        text = "👥 *Последние пользователи:*\n\n"
        for i, (uid2, u) in enumerate(list(users_db.items())[-10:]):
            name = u.get("name", "?")
            uname = f"@{u.get('username')}" if u.get("username") else "нет username"
            msgs = u.get("messages", 0)
            text += f"{i+1}. *{name}* ({uname}) — {msgs} сообщ.\n"
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown")
        return

    elif call.data == "admin_broadcast":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id,
            "📬 Напишите текст для рассылки всем пользователям:"
        )
        bot.register_next_step_handler(call.message, do_broadcast)
        return

    elif call.data == "admin_add_realty":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id,
            "🏠 *Добавить объект*\n\n"
            "Напишите в формате:\n"
            "`Тип | Город | Цена$ | Комнат | Площадь м² | Описание`\n\n"
            "Пример:\n"
            "`Квартира | Мерсин | 90000 | 2 | 80 | Вид на море`",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(call.message, add_realty)
        return

    try:
        bot.edit_message_reply_markup(
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_keyboard(uid)
        )
    except: pass

def add_realty(msg):
    if not is_admin(msg.from_user.id): return
    try:
        parts = [p.strip() for p in msg.text.split("|")]
        new_obj = {
            "id": len(realty_db) + 1,
            "type": parts[0],
            "city": parts[1],
            "price": int(parts[2]),
            "rooms": int(parts[3]),
            "area": int(parts[4]),
            "desc": parts[5],
            "contact": "@bayanchatbot"
        }
        realty_db.append(new_obj)
        bot.send_message(msg.chat.id,
            f"✅ Объект добавлен!\n\n"
            f"🏠 {new_obj['type']} в {new_obj['city']}\n"
            f"💰 ${new_obj['price']:,}\n"
            f"📐 {new_obj['area']} м²",
        )
    except:
        bot.send_message(msg.chat.id, "⚠️ Ошибка! Проверьте формат данных.")

# ── ТЕКСТ ──
@bot.message_handler(content_types=["text"])
def handle_text(msg):
    register_user(msg)
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

# ── ГОЛОС ──
@bot.message_handler(content_types=["voice"])
def handle_voice(msg):
    register_user(msg)
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
        bot.edit_message_text(f"🎙️ Вы сказали: *{text}*", msg.chat.id, thinking.message_id, parse_mode="Markdown")
        chat_response(msg, text, lang)
    except Exception as e:
        bot.edit_message_text(f"⚠️ Ошибка: {str(e)[:100]}", msg.chat.id, thinking.message_id)

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
    register_user(msg)
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
    register_user(msg)
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
            prompt += f"\nДай совет по работе с этим типом файла."
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
print("🤖 AI FOR BUSINESS — ПОЛНАЯ ВЕРСИЯ")
print("📱 @bayanchatbot")
print("✅ Чат + Голос + Картинки + Музыка")
print("✅ Статистика + Рассылка + Недвижимость")
print("Нажмите Ctrl+C для остановки")
print("=" * 40)
bot.infinity_polling()
