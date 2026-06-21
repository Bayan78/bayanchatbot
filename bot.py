"""
SALYTRAVEL — Telegram-ассистент
=================================================
Путешествия: Билеты · Отели · eSIM · Трансфер · Страховка · Туры
Услуги: Разработка сайтов, Telegram-ботов, программирование
Сайт: https://bayanchatbot.netlify.app

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
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ══════════════════════════════════════
#  КЛЮЧИ ИЗ ПЕРЕМЕННЫХ СРЕДЫ
# ══════════════════════════════════════
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GROQ_KEY       = os.environ.get("GROQ_KEY")
ADMIN_ID       = os.environ.get("ADMIN_ID")

# ── САЙТ ──
SITE_URL = "https://bayanchatbot.netlify.app"
WHATSAPP_NUMBER = "87773907576"

client = Groq(api_key=GROQ_KEY)
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ── БАЗА ПОЛЬЗОВАТЕЛЕЙ ──
users_db = {}

# ── ПРОМПТЫ ──
# По умолчанию режим travel. Если человек спрашивает про разработку/сайты/ботов — режим услуг.
TRAVEL_PROMPT = {
    "ru": (
        "Ты — SALYTRAVEL, дружелюбный ассистент по путешествиям. "
        "Помогаешь находить дешёвые авиабилеты, отели, eSIM, трансферы, страховку и туры по миру. "
        "Отвечай тепло и просто. "
        "Когда спрашивают про билеты, цены, маршруты, отели или поездку — дай совет и в конце добавь: "
        "'Найти самую низкую цену можно здесь: " + SITE_URL + "'. "
        "Советы: гибкие даты, вторник-среда дешевле, стыковки через хабы (Стамбул, Дубай) выгоднее. "
        "Не выдумывай конкретные цены — за реальными ценами отправляй на сайт. "
        "Если человек спрашивает про разработку сайтов, ботов или программирование — "
        "скажи, что это делает Баянбек, и предложи команду /services. "
        "Отвечай на русском языке."
    ),
    "en": (
        "You are SALYTRAVEL, a friendly travel assistant. "
        "You help find cheap flights, hotels, eSIM, transfers, insurance and tours worldwide. "
        "For tickets/prices/routes/hotels give tips and add: 'Find the lowest price here: " + SITE_URL + "'. "
        "Don't invent prices — send users to the site. "
        "If asked about website/bot development or programming — suggest the /services command. "
        "Respond in English."
    ),
    "kz": (
        "Сен — SALYTRAVEL, саяхат көмекшісің. Арзан билет, қонақүй, eSIM, трансфер, сақтандыру, тур табуға көмектесесің. "
        "Билет/баға/бағыт сұраса кеңес бер де қос: 'Ең төмен бағаны осы жерден тап: " + SITE_URL + "'. "
        "Нақты баға үшін сайтқа жібер. Сайт/бот жасау туралы сұраса — /services командасын ұсын. Қазақша жауап бер."
    ),
    "tr": (
        "Sen SALYTRAVEL'sın, seyahat asistanısın. Ucuz bilet, otel, eSIM, transfer, sigorta, tur bulmaya yardım edersin. "
        "Bilet/fiyat/rota sorulursa ipucu ver ve ekle: 'En düşük fiyatı burada bul: " + SITE_URL + "'. "
        "Fiyat uydurma — siteye yönlendir. Web/bot geliştirme sorulursa /services komutunu öner. Türkçe cevap ver."
    ),
}

SERVICES_PROMPT = {
    "ru": (
        "Ты — ассистент Баянбека по услугам разработки. Баянбек делает сайты, Telegram-ботов и занимается программированием. "
        "Отвечай вежливо и профессионально. "
        "Если спросят про цены или услуги — отвечай ТОЧНО ТАК: "
        "'Наши услуги и цены:\n\n"
        "🌐 Сайты: от 30 000 до 60 000 тенге, срок 3-7 дней.\n\n"
        "🤖 Telegram-боты: от 10 000 до 30 000 тенге, срок 3-7 дней.\n\n"
        "🎬 Программа для видеомонтажа: 200 000 тенге.\n\n"
        "Цена зависит от сложности. Опишите проект для точного расчёта.' "
        "Для заказа предложи связаться напрямую. Отвечай на русском языке."
    ),
    "en": (
        "You are Bayanbek's development services assistant. He builds websites, Telegram bots and does programming. "
        "If asked about prices say EXACTLY: '🌐 Websites: 30,000-60,000 tenge, 3-7 days. "
        "🤖 Telegram bots: 10,000-30,000 tenge, 3-7 days. 🎬 Video editing software: 200,000 tenge.' "
        "Respond in English."
    ),
    "kz": (
        "Сен Баянбектің әзірлеу қызметтері бойынша көмекшісің. Ол сайт, Telegram-бот жасайды, программалаумен айналысады. "
        "Баға сұраса ДӘЛ айт: '🌐 Сайттар: 30 000-60 000 теңге, 3-7 күн. "
        "🤖 Боттар: 10 000-30 000 теңге, 3-7 күн. 🎬 Бейне монтаж бағдарламасы: 200 000 теңге.' Қазақша жауап бер."
    ),
    "tr": (
        "Sen Bayanbek'in yazılım hizmetleri asistanısın. Web sitesi, Telegram botu yapar, programlama yapar. "
        "Fiyat sorulursa: '🌐 Web siteleri: 30.000-60.000 tenge. 🤖 Botlar: 10.000-30.000 tenge. "
        "🎬 Video düzenleme: 200.000 tenge.' Türkçe cevap ver."
    ),
}


# ── РЕКЛАМНЫЙ БАННЕР УСЛУГ (ненавязчиво) ──
AD_BANNER = {
    "ru": "\n\n— — —\n💻 *Реклама:* нужен сайт или Telegram-бот? Баянбек сделает за 3-7 дней. Команда /services",
    "en": "\n\n— — —\n💻 *Ad:* need a website or Telegram bot? Done in 3-7 days. /services",
    "kz": "\n\n— — —\n💻 *Жарнама:* сайт не Telegram-бот керек пе? 3-7 күнде. /services",
    "tr": "\n\n— — —\n💻 *Reklam:* web sitesi veya Telegram botu mu lazım? 3-7 günde. /services",
}

# ── ВСПОМОГАТЕЛЬНЫЕ ──
def get_lang(uid): return users_db.get(uid, {}).get("lang", "ru")
def get_mode(uid): return users_db.get(uid, {}).get("mode", "travel")  # travel | services
def is_admin(uid): return str(uid) == str(ADMIN_ID)

def register_user(msg):
    uid = msg.from_user.id
    if uid not in users_db:
        users_db[uid] = {
            "id": uid,
            "name": msg.from_user.first_name or "Гость",
            "username": msg.from_user.username or "",
            "lang": "ru",
            "mode": "travel",
            "joined": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "messages": 0
        }
        if ADMIN_ID:
            try:
                name = msg.from_user.first_name or "Гость"
                uname = f"@{msg.from_user.username}" if msg.from_user.username else "нет username"
                bot.send_message(ADMIN_ID,
                    f"🔔 *Новый пользователь!*\n\n👤 *{name}*\n📱 {uname}\n🆔 `{uid}`\n"
                    f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}", parse_mode="Markdown")
            except: pass
    users_db[uid]["messages"] = users_db[uid].get("messages", 0) + 1

def site_button(lang="ru"):
    labels = {"ru":"✈️ Найти дешёвые билеты","en":"✈️ Find cheap flights",
              "kz":"✈️ Арзан билет табу","tr":"✈️ Ucuz bilet bul"}
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(labels.get(lang, labels["ru"]), url=SITE_URL))
    return kb

def main_keyboard(uid):
    lang = users_db.get(uid, {}).get("lang", "ru")
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("✈️ Найти билеты", url=SITE_URL))
    kb.add(InlineKeyboardButton("💻 Реклама: сайты и боты от Баянбека", callback_data="services"))
    kb.add(
        InlineKeyboardButton("🇷🇺 RU" + (" ✅" if lang=="ru" else ""), callback_data="lang_ru"),
        InlineKeyboardButton("🇬🇧 EN" + (" ✅" if lang=="en" else ""), callback_data="lang_en"),
        InlineKeyboardButton("🇰🇿 KZ" + (" ✅" if lang=="kz" else ""), callback_data="lang_kz"),
        InlineKeyboardButton("🇹🇷 TR" + (" ✅" if lang=="tr" else ""), callback_data="lang_tr"),
    )
    kb.add(InlineKeyboardButton("ℹ️ Что умеет SALYTRAVEL", callback_data="about"))
    return kb

def admin_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📊 Статистика", callback_data="admin_stats"),
        InlineKeyboardButton("📬 Рассылка", callback_data="admin_broadcast"),
        InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
    )
    return kb

ABOUT_TEXT = (
    "🌍 *SALYTRAVEL* — всё для поездки в одном месте:\n\n"
    "✈️ *Билеты* — сравнение цен по всем системам сразу\n"
    "🏨 *Отели* — в любом городе мира\n"
    "📱 *eSIM* — интернет сразу после прилёта\n"
    "🚐 *Трансфер* — машина встречает в аэропорту\n"
    "🛡 *Страховка* — нужна для визы, оформляется онлайн\n"
    "🌴 *Туры* — «всё включено» одним пакетом\n\n"
    "Открой сайт и найди самую низкую цену за пару секунд 👇"
)

SERVICES_TEXT = (
    "💻 *Услуги разработки от Баянбека*\n\n"
    "🌐 *Сайты* — от 30 000 до 60 000 тенге, срок 3-7 дней\n"
    "🤖 *Telegram-боты* — от 10 000 до 30 000 тенге, срок 3-7 дней\n"
    "🎬 *Программа для видеомонтажа* — 200 000 тенге\n\n"
    "Цена зависит от сложности проекта. Опишите задачу — рассчитаю точно.\n"
    "Просто напишите сюда, что нужно 👇"
)

# ── /start ──
@bot.message_handler(commands=["start"])
def start(msg):
    register_user(msg)
    uid = msg.from_user.id
    users_db[uid]["mode"] = "travel"
    name = msg.from_user.first_name or "Друг"
    bot.send_message(msg.chat.id,
        f"👋 Привет, *{name}*!\n\n"
        "Я *SALYTRAVEL* — твой помощник по путешествиям ✈️\n\n"
        "Помогу найти:\n"
        "✈️ дешёвые авиабилеты по всему миру\n"
        "🏨 отели · 📱 eSIM · 🚐 трансфер\n"
        "🛡 страховку · 🌴 туры «всё включено»\n\n"
        "_💻 реклама: нужен сайт или Telegram-бот? жми кнопку ниже или /services_\n\n"
        "Спроси о поездке или выбери ниже 👇",
        parse_mode="Markdown",
        reply_markup=main_keyboard(uid))

# ── /bilety ──
@bot.message_handler(commands=["bilety", "travel", "salytravel", "site"])
def site_cmd(msg):
    register_user(msg)
    users_db[msg.from_user.id]["mode"] = "travel"
    bot.send_message(msg.chat.id,
        "🌍 *SALYTRAVEL* — билеты, отели, eSIM, трансфер, страховка и туры в одном месте.\n\n"
        "Сравни цены и поймай самую низкую 👇",
        parse_mode="Markdown",
        reply_markup=site_button(get_lang(msg.from_user.id)))

# ── /services — разработка ──
@bot.message_handler(commands=["services", "uslugi", "razrabotka", "site_order"])
def services_cmd(msg):
    register_user(msg)
    users_db[msg.from_user.id]["mode"] = "services"
    bot.send_message(msg.chat.id, SERVICES_TEXT, parse_mode="Markdown")

# ── /menu ──
@bot.message_handler(commands=["menu"])
def menu(msg):
    register_user(msg)
    bot.send_message(msg.chat.id, "⚙️ Меню:", reply_markup=main_keyboard(msg.from_user.id))

# ── /admin ──
@bot.message_handler(commands=["admin"])
def admin_panel(msg):
    if not is_admin(msg.from_user.id):
        bot.send_message(msg.chat.id, "⛔ Нет доступа!")
        return
    bot.send_message(msg.chat.id,
        f"🔐 *Панель администратора*\n\n👥 Всего пользователей: *{len(users_db)}*\n\nВыберите 👇",
        parse_mode="Markdown", reply_markup=admin_keyboard())

# ── /stats ──
@bot.message_handler(commands=["stats"])
def stats_cmd(msg):
    if not is_admin(msg.from_user.id):
        bot.send_message(msg.chat.id, "⛔ Нет доступа!")
        return
    show_stats(msg.chat.id)

def show_stats(chat_id):
    total = len(users_db)
    total_msgs = sum(u.get("messages", 0) for u in users_db.values())
    langs = {}
    for u in users_db.values():
        l = u.get("lang", "ru"); langs[l] = langs.get(l, 0) + 1
    bot.send_message(chat_id,
        f"📊 *Статистика*\n\n👥 Пользователей: *{total}*\n💬 Сообщений: *{total_msgs}*\n\n"
        f"🌍 По языкам:\n🇷🇺 RU: {langs.get('ru',0)}\n🇬🇧 EN: {langs.get('en',0)}\n"
        f"🇰🇿 KZ: {langs.get('kz',0)}\n🇹🇷 TR: {langs.get('tr',0)}",
        parse_mode="Markdown")

# ── РАССЫЛКА ──
def do_broadcast(msg):
    if not is_admin(msg.from_user.id): return
    text = f"📢 *SALYTRAVEL:*\n\n{msg.text}"
    success = 0; fail = 0
    for uid in users_db:
        try:
            bot.send_message(uid, text, parse_mode="Markdown",
                             reply_markup=site_button(users_db[uid].get("lang","ru")))
            success += 1
        except:
            fail += 1
    bot.send_message(msg.chat.id,
        f"✅ Рассылка завершена!\n📨 Отправлено: *{success}*\n❌ Ошибок: *{fail}*",
        parse_mode="Markdown")

# ── CALLBACKS ──
@bot.callback_query_handler(func=lambda c: True)
def handle_callback(call):
    uid = call.from_user.id
    if uid not in users_db:
        users_db[uid] = {"lang":"ru","mode":"travel","messages":0}

    if call.data.startswith("lang_"):
        users_db[uid]["lang"] = call.data.replace("lang_","")
        bot.answer_callback_query(call.id, "Язык изменён! ✅")
        try:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id,
                                          reply_markup=main_keyboard(uid))
        except: pass
        return
    elif call.data == "about":
        bot.answer_callback_query(call.id)
        users_db[uid]["mode"] = "travel"
        bot.send_message(call.message.chat.id, ABOUT_TEXT, parse_mode="Markdown",
                         reply_markup=site_button(get_lang(uid)))
        return
    elif call.data == "services":
        bot.answer_callback_query(call.id)
        users_db[uid]["mode"] = "services"
        bot.send_message(call.message.chat.id, SERVICES_TEXT, parse_mode="Markdown")
        return
    elif call.data == "admin_stats":
        bot.answer_callback_query(call.id); show_stats(call.message.chat.id); return
    elif call.data == "admin_users":
        bot.answer_callback_query(call.id)
        text = "👥 *Последние пользователи:*\n\n"
        for i,(uid2,u) in enumerate(list(users_db.items())[-10:]):
            name = u.get("name","?")
            uname = f"@{u.get('username')}" if u.get("username") else "нет"
            text += f"{i+1}. *{name}* ({uname}) — {u.get('messages',0)} сообщ.\n"
        bot.send_message(call.message.chat.id, text, parse_mode="Markdown"); return
    elif call.data == "admin_broadcast":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📬 Напишите текст для рассылки:")
        bot.register_next_step_handler(call.message, do_broadcast); return
    bot.answer_callback_query(call.id)

# ── ТЕКСТ ──
DEV_WORDS = ["сайт","бот","разработ","программ","website","bot","develop","код","code","приложение","app","видеомонтаж"]

@bot.message_handler(content_types=["text"])
def handle_text(msg):
    register_user(msg)
    uid = msg.from_user.id
    text = msg.text
    if text.startswith("/"): return
    # авто-переключение в режим услуг, если человек явно про разработку
    if any(w in text.lower() for w in DEV_WORDS):
        users_db[uid]["mode"] = "services"
    chat_response(msg, text, get_lang(uid), get_mode(uid))

def chat_response(msg, text, lang, mode):
    thinking = bot.send_message(msg.chat.id, "⏳ Думаю...")
    try:
        prompts = SERVICES_PROMPT if mode == "services" else TRAVEL_PROMPT
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role":"system","content":prompts.get(lang, prompts["ru"])},
                {"role":"user","content":text}
            ],
            max_tokens=1000)
        reply = response.choices[0].message.content
        bot.delete_message(msg.chat.id, thinking.message_id)
        markup = None if mode == "services" else site_button(lang)
        # ненавязчивая реклама услуг: примерно каждый 4-й travel-ответ
        if mode != "services":
            cnt = users_db.get(msg.from_user.id, {}).get("messages", 0)
            if cnt % 4 == 0:
                reply = reply + AD_BANNER.get(lang, AD_BANNER["ru"])
        bot.send_message(msg.chat.id, reply, reply_markup=markup, parse_mode="Markdown")
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
            f.write(file_data); tmp_path = f.name
        with open(tmp_path,"rb") as af:
            transcription = client.audio.transcriptions.create(
                file=("voice.ogg", af, "audio/ogg"),
                model="whisper-large-v3",
                language={"ru":"ru","en":"en","kz":"kk","tr":"tr"}.get(lang,"ru"))
        os.unlink(tmp_path)
        text = transcription.text
        bot.edit_message_text(f"🎙️ Вы сказали: *{text}*", msg.chat.id, thinking.message_id, parse_mode="Markdown")
        if any(w in text.lower() for w in DEV_WORDS):
            users_db[uid]["mode"] = "services"
        chat_response(msg, text, lang, get_mode(uid))
    except Exception as e:
        bot.edit_message_text(f"⚠️ Ошибка голоса: {str(e)[:100]}", msg.chat.id, thinking.message_id)

print("=" * 40)
print("SALYTRAVEL — Travel + Разработка")
print("@bayanchatbot")
print(SITE_URL)
print("Groq + Whisper")
print("=" * 40)
bot.infinity_polling()
