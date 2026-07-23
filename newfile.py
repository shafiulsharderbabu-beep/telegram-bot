import telebot
from telebot import types
import sqlite3
import time

# ==========================
# SETTINGS
# ==========================
BOT_TOKEN = "8013091386:AAFhyV16xspDCBTDMx18c3kgomFkYG4g6ik"
ADMIN_ID = "8379634906"     # আপনার Telegram User ID
CHANNEL = "@WORK_FROM_HOME_57"

REF_BONUS = 2
WITHDRAW_MIN = 10

bot = telebot.TeleBot(BOT_TOKEN)
bot.delete_webhook()

# ==========================
# DATABASE
# ==========================

db = sqlite3.connect("bot.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
user_id INTEGER PRIMARY KEY,
balance REAL DEFAULT 0,
referrals INTEGER DEFAULT 0,
referred_by INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS withdraw(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
amount REAL,
method TEXT,
number TEXT,
status TEXT
)
""")

db.commit()

# ==========================
# FUNCTIONS
# ==========================

def add_user(user_id, ref=None):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO users(user_id,referred_by) VALUES(?,?)",
            (user_id, ref),
        )
        db.commit()


def get_balance(user_id):
    cursor.execute(
        "SELECT balance FROM users WHERE user_id=?",
        (user_id,),
    )
    row = cursor.fetchone()
    if row:
        return row[0]
    return 0


def is_member(user_id):
    try:
        x = bot.get_chat_member(CHANNEL, user_id)
        return x.status in ["member", "administrator", "creator"]
    except:
        return False


def menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    m.add(
        types.KeyboardButton("💰 ব্যালেন্স"),
        types.KeyboardButton("📂 FILE SUBMIT")
    )

    m.add(
        types.KeyboardButton("📤 উত্তোলন"),
        types.KeyboardButton("👨‍💼 সাপোর্ট")
    )

    m.add(
        types.KeyboardButton("⚠️ RULES"),
        types.KeyboardButton("📄 REPORT")
    )

    m.add(
        types.KeyboardButton("👥 আমার রেফারেল"),
        types.KeyboardButton("💬 আমি নতুন?")
    )

    return m

# ==========================
# START
# ==========================

@bot.message_handler(commands=['start'])
def start(message):

    uid = message.from_user.id

    if not is_member(uid):

        markup = types.InlineKeyboardMarkup()

        markup.add(
            types.InlineKeyboardButton(
                "✅ Join Channel",
                url=f"https://t.me/{CHANNEL.replace('@','')}"
            )
        )

        bot.send_message(
            uid,
            "❌ আগে আমাদের চ্যানেলে Join করুন।",
            reply_markup=markup
        )

        return

    add_user(uid)

    bot.send_message(
        uid,
        "🎉 Welcome",
        reply_markup=menu()
    )
    # ==========================
# BALANCE
# ==========================

@bot.message_handler(func=lambda m: m.text=="💰 ব্যালেন্স")
def balance(message):

    bal = get_balance(message.from_user.id)

    bot.send_message(
        message.chat.id,
        f"💰 আপনার বর্তমান ব্যালেন্স: {bal} ৳"
    )

# ==========================
# MY REFERRAL
# ==========================

@bot.message_handler(func=lambda m:m.text=="👥 আমার রেফারেল")
def referral(message):

    uid = message.from_user.id

    cursor.execute(
        "SELECT referrals FROM users WHERE user_id=?",
        (uid,)
    )

    data = cursor.fetchone()

    total = 0

    if data:
        total = data[0]

    link = f"https://t.me/{bot.get_me().username}?start={uid}"

    bot.send_message(
        uid,
        f"""👥 মোট রেফার: {total}

🔗 আপনার রেফার লিংক:

{link}

প্রতি রেফারে {REF_BONUS} টাকা পাবেন।"""
    )

# ==========================
# FILE SUBMIT
# ==========================

@bot.message_handler(func=lambda m:m.text=="📂 FILE SUBMIT")
def submit(message):

    msg = bot.send_message(
        message.chat.id,
        "📂 আপনার ফাইল অথবা Screenshot পাঠান।"
    )

    bot.register_next_step_handler(
        msg,
        receive_file
    )


def receive_file(message):

    if message.document:

        bot.forward_message(
            ADMIN_ID,
            message.chat.id,
            message.message_id
        )

        bot.reply_to(
            message,
            "✅ আপনার ফাইল সফলভাবে জমা হয়েছে।"
        )

    elif message.photo:

        bot.forward_message(
            ADMIN_ID,
            message.chat.id,
            message.message_id
        )

        bot.reply_to(
            message,
            "✅ Screenshot সফলভাবে জমা হয়েছে।"
        )

    else:

        bot.reply_to(
            message,
            "❌ শুধুমাত্র ছবি অথবা File পাঠান।"
        )

# ==========================
# SUPPORT
# ==========================

@bot.message_handler(func=lambda m:m.text=="👨‍💼 সাপোর্ট")
def support(message):

    bot.send_message(
        message.chat.id,
        "👨‍💼 Support:\n\n@YourSupport"
    )

# ==========================
# RULES
# ==========================

@bot.message_handler(func=lambda m:m.text=="⚠️ RULES")
def rules(message):

    bot.send_message(
        message.chat.id,
        """📌 Rules

✅ Fake Account নয়

✅ Spam করবেন না

✅ ভুল তথ্য দিলে Account Block হবে

✅ Admin এর সিদ্ধান্তই চূড়ান্ত"""
    )

# ==========================
# REPORT
# ==========================

@bot.message_handler(func=lambda m:m.text=="📄 REPORT")
def report(message):

    msg = bot.send_message(
        message.chat.id,
        "আপনার অভিযোগ লিখুন।"
    )

    bot.register_next_step_handler(
        msg,
        send_report
    )

def send_report(message):

    bot.send_message(
        ADMIN_ID,
        f"📄 নতুন রিপোর্ট\n\nUser: {message.from_user.id}\n\n{message.text}"
    )

    bot.reply_to(
        message,
        "✅ রিপোর্ট পাঠানো হয়েছে।"
    )

# ==========================
# NEW USER
# ==========================

@bot.message_handler(func=lambda m:m.text=="💬 আমি নতুন?")
def help_new(message):

    bot.send_message(
        message.chat.id,
        """💬 নতুন ব্যবহারকারীদের জন্য

১. Channel Join করুন

২. কাজ সম্পন্ন করুন

৩. File Submit করুন

৪. Balance জমা হবে

৫. Minimum Withdraw হলে টাকা তুলুন"""
    )
    # ==========================
# WITHDRAW
# ==========================

@bot.message_handler(func=lambda m: m.text == "📤 উত্তোলন")
def withdraw(message):

    bal = get_balance(message.from_user.id)

    if bal < WITHDRAW_MIN:
        bot.reply_to(
            message,
            f"❌ Withdraw করতে কমপক্ষে {WITHDRAW_MIN} টাকা লাগবে।"
        )
        return

    msg = bot.send_message(
        message.chat.id,
        "কত টাকা Withdraw করবেন?"
    )

    bot.register_next_step_handler(msg, withdraw_amount)


def withdraw_amount(message):

    try:
        amount = float(message.text)
    except ValueError:
        bot.reply_to(message, "❌ সঠিক পরিমাণ লিখুন।")
        return

    msg = bot.send_message(
        message.chat.id,
        "Payment Method ও Number লিখুন\n\nউদাহরণ:\nbKash 01XXXXXXXXX"
    )

    bot.register_next_step_handler(
        msg,
        finish_withdraw,
        amount
    )


def finish_withdraw(message, amount):

    cursor.execute(
        "INSERT INTO withdraw(user_id,amount,method,number,status) VALUES(?,?,?,?,?)",
        (
            message.from_user.id,
            amount,
            "Manual",
            message.text,
            "Pending"
        )
    )

    db.commit()

    bot.send_message(
        ADMIN_ID,
        f"💸 নতুন Withdraw Request\n\n"
        f"User ID: {message.from_user.id}\n"
        f"Amount: {amount}\n"
        f"Info: {message.text}"
    )

    bot.reply_to(
        message,
        "✅ আপনার Withdraw Request পাঠানো হয়েছে।"
    )

# ==========================
# RUN BOT
# ==========================

print("Bot Running...")
bot.infinity_polling(skip_pending=True)