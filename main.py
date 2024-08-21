import telebot
from telebot import types
import sqlite3
import os

# BotFather dan olingan haqiqiy tokenni 'YOUR_BOT_TOKEN' o'rniga qo'ying
bot = telebot.TeleBot('7460976537:AAEvfrR7NvIb_6vTNHmcXPmHhQcPcGjDbGE')

# SQLite ma'lumotlar bazasini sozlash
conn = sqlite3.connect('movies.db', check_same_thread=False)
cursor = conn.cursor()

# Agar mavjud bo'lmasa, kinolar jadvali yaratiladi
cursor.execute('''
    CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        code TEXT UNIQUE NOT NULL,
        description TEXT,
        year INTEGER,
        genre TEXT,
        file_id TEXT
    )
''')
conn.commit()

# Mavjud jadval strukturasini tekshirish va yangi ustunlarni qo'shish
cursor.execute("PRAGMA table_info(movies)")
columns = [column[1] for column in cursor.fetchall()]

if 'description' not in columns:
    cursor.execute("ALTER TABLE movies ADD COLUMN description TEXT")
if 'year' not in columns:
    cursor.execute("ALTER TABLE movies ADD COLUMN year INTEGER")
if 'genre' not in columns:
    cursor.execute("ALTER TABLE movies ADD COLUMN genre TEXT")
if 'file_id' not in columns:
    cursor.execute("ALTER TABLE movies ADD COLUMN file_id TEXT")

conn.commit()

# Admin foydalanuvchi ID si (haqiqiy admin ID si bilan almashtiring)
ADMIN_USER_ID = 6179552075 # Bu yerga haqiqiy admin ID sini yozing

# Kanal usernamelari (@ belgisiz)
CHANNEL_USERNAMES = ['Shohruh_Abdurahmonov', 'JobsVacancyUz']

def check_subscription(user_id):
    for channel in CHANNEL_USERNAMES:
        try:
            member = bot.get_chat_member(f'@{channel}', user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except telebot.apihelper.ApiException:
            return False
    return True

def send_subscription_message(chat_id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for channel in CHANNEL_USERNAMES:
        markup.add(types.InlineKeyboardButton(f"Kanalga o'tish: @{channel}", url=f"https://t.me/{channel}"))
    markup.add(types.InlineKeyboardButton("✅ Tasdiqlash", callback_data="check_subscription"))
    bot.send_message(chat_id, "⚠️ Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "check_subscription")
def callback_check_subscription(call):
    if check_subscription(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ Siz kanallarga a'zo bo'ldingiz. Botdan foydalanishingiz mumkin!")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        send_welcome(call.message)
    else:
        bot.answer_callback_query(call.id, "❌ Siz hali barcha kanallarga a'zo bo'lmagansiz. Iltimos, a'zo bo'ling va qaytadan tekshiring.")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if not check_subscription(message.from_user.id):
        send_subscription_message(message.chat.id)
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    item1 = types.KeyboardButton("🔍 Kino qidirish")
    markup.add(item1)
    
    if message.from_user.id == ADMIN_USER_ID:
        item2 = types.KeyboardButton("➕ Kino qo'shish")
        markup.add(item2)

    welcome_text = (
        "🎬 *Assalomu alaykum!*\n\n"
        "Kino ma'lumotlari botiga xush kelibsiz.\n"
        "Nima qilishni xohlaysiz?"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if not check_subscription(message.from_user.id):
        send_subscription_message(message.chat.id)
        return

    if message.text == "➕ Kino qo'shish" and message.from_user.id == ADMIN_USER_ID:
        ask_for_movie_title(message)
    elif message.text == "🔍 Kino qidirish":
        ask_for_movie_code(message)
    else:
        search_movie_by_code(message)

def ask_for_movie_title(message):
    if message.from_user.id != ADMIN_USER_ID:
        bot.reply_to(message, "⚠️ Kechirasiz, faqat admin kino qo'sha oladi.")
        return
    bot.reply_to(message, "📝 Iltimos, qo'shmoqchi bo'lgan kino nomini kiriting:")
    bot.register_next_step_handler(message, process_movie_title)

def process_movie_title(message):
    if message.from_user.id != ADMIN_USER_ID:
        bot.reply_to(message, "⚠️ Kechirasiz, faqat admin kino qo'sha oladi.")
        return
    title = message.text
    bot.reply_to(message, "📝 Iltimos, kino haqida qisqacha ma'lumot kiriting:")
    bot.register_next_step_handler(message, process_movie_description, title)

def process_movie_description(message, title):
    description = message.text
    bot.reply_to(message, "📅 Iltimos, kino chiqarilgan yilni kiriting:")
    bot.register_next_step_handler(message, process_movie_year, title, description)

def process_movie_year(message, title, description):
    year = message.text
    bot.reply_to(message, "🎭 Iltimos, kino janrini kiriting:")
    bot.register_next_step_handler(message, process_movie_genre, title, description, year)

def process_movie_genre(message, title, description, year):
    genre = message.text
    bot.reply_to(message, "🔑 Iltimos, kino kodini kiriting:")
    bot.register_next_step_handler(message, process_movie_code, title, description, year, genre)

def process_movie_code(message, title, description, year, genre):
    code = message.text
    bot.reply_to(message, "📤 Iltimos, kino faylini yuklang (faqat video formatlar qabul qilinadi, masalan: .mp4, .avi, .mov):")
    bot.register_next_step_handler(message, process_movie_file, title, description, year, genre, code)

def process_movie_file(message, title, description, year, genre, code):
    if message.document or message.video:
        if message.document:
            file_id = message.document.file_id
            file_name = message.document.file_name
        else:
            file_id = message.video.file_id
            file_name = "video.mp4"  # Default name for video files
        
        file_extension = os.path.splitext(file_name)[1].lower()
        allowed_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv']
        
        if file_extension in allowed_extensions or message.video:
            try:
                cursor.execute("INSERT INTO movies (title, code, description, year, genre, file_id) VALUES (?, ?, ?, ?, ?, ?)", 
                               (title, code, description, year, genre, file_id))
                conn.commit()
                
                success_message = (
                    "✅ *Kino muvaffaqiyatli qo'shildi!*\n\n"
                    f"🎬 *Nomi:* {title}\n"
                    f"🔑 *Kodi:* {code}\n"
                    f"📝 *Ma'lumot:* {description}\n"
                    f"📅 *Yili:* {year}\n"
                    f"🎭 *Janri:* {genre}"
                )
                bot.reply_to(message, success_message, parse_mode="Markdown")
            except sqlite3.Error as e:
                bot.reply_to(message, f"❌ Xatolik yuz berdi: {str(e)}")
                cursor.execute("PRAGMA table_info(movies)")
                columns = cursor.fetchall()
                bot.reply_to(message, f"Jadval strukturasi: {columns}")
        else:
            bot.reply_to(message, "⚠️ Iltimos, faqat video formatdagi fayllarni yuklang (.mp4, .avi, .mov, .mkv, .wmv, .flv).")
            bot.register_next_step_handler(message, process_movie_file, title, description, year, genre, code)
    else:
        bot.reply_to(message, "⚠️ Iltimos, kino faylini yuklang (faqat video formatlar qabul qilinadi).")
        bot.register_next_step_handler(message, process_movie_file, title, description, year, genre, code)

def ask_for_movie_code(message):
    bot.reply_to(message, "🔍 Iltimos, qidirmoqchi bo'lgan kino kodini kiriting:")

def search_movie_by_code(message):
    if not check_subscription(message.from_user.id):
        send_subscription_message(message.chat.id)
        return

    code = message.text
    cursor.execute("SELECT title, description, year, genre, file_id FROM movies WHERE code = ?", (code,))
    result = cursor.fetchone()
    
    if result:
        title, description, year, genre, file_id = result
        response = (
            "🎬 *Topilgan kino:*\n\n"
            f"📌 *Nomi:* {title}\n"
            f"📝 *Ma'lumot:* {description}\n"
            f"📅 *Yili:* {year}\n"
            f"🎭 *Janri:* {genre}"
        )
        if file_id:
            bot.send_video(message.chat.id, file_id, caption=response, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, response, parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ Kechirasiz, bu kod bo'yicha kino topilmadi.")

# Botni ishga tushirish
bot.polling()
