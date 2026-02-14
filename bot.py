from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatAction
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
import os
import json

# ================== الإعدادات ==================
TOKEN = "PUT_YOUR_TOKEN_HERE"  # ضع توكن البوت هنا
ADMIN_ID = 5037555049           # ضع ID الأدمن هنا
LINKS_FILE = "links.json"
USERS_FILE = "users.json"
BANNED_FILE = "banned.json"

# ================== إدارة JSON ==================
def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ================== المستخدمين ==================
def save_user(user):
    users = load_json(USERS_FILE, {})
    uid = str(user.id)
    if uid not in users:
        users[uid] = {
            "name": user.full_name,
            "username": user.username
        }
    save_json(USERS_FILE, users)

# ================== /start ==================
def start(update, context):
    save_user(update.effective_user)
    keyboard = [
        [InlineKeyboardButton("📘 السنة الأولى", callback_data="year_year1")],
        [InlineKeyboardButton("📗 السنة الثانية", callback_data="year_year2")],
        [InlineKeyboardButton("📙 السنة الثالثة", callback_data="year_year3")]
    ]
    update.message.reply_text(
        "👋 أهلاً بك في بوت الملفات الدراسي 🇩🇪\nاختر السنة:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================== لوحة الأدمن ==================
def admin_panel(update, context):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        update.message.reply_text("⛔ هذا الأمر مخصص للأدمن فقط.")
        return
    keyboard = [
        [InlineKeyboardButton("➕ إضافة رابط", callback_data="admin_add_link")],
        [InlineKeyboardButton("👥 عرض المستخدمين", callback_data="admin_users")],
        [InlineKeyboardButton("🚫 حظر مستخدم", callback_data="admin_ban_user")],
        [InlineKeyboardButton("✅ فك حظر مستخدم", callback_data="admin_unban_user")],
        [InlineKeyboardButton("📢 إرسال رسالة جماعية", callback_data="admin_broadcast")]
    ]
    update.message.reply_text(
        "🛠 لوحة تحكم الأدمن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================== عرض المستخدمين ==================
def users_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("⛔ هذا الأمر مخصص للأدمن فقط.")
        return
    users = load_json(USERS_FILE, {})
    text = f"👥 عدد المستخدمين: {len(users)}\n\n"
    for u in users.values():
        name = u["name"]
        username = f"@{u['username']}" if u["username"] else ""
        text += f"- {name} {username}\n"
    update.message.reply_text(text)

# ================== أزرار البوت ==================
def buttons(update, context):
    query = update.callback_query
    query.answer()
    data = query.data

    # لوحة إدارة الروابط
    if data == "admin_add_link":
        keyboard = [
            [InlineKeyboardButton("📘 السنة الأولى", callback_data="add_year_year1")],
            [InlineKeyboardButton("📗 السنة الثانية", callback_data="add_year_year2")],
            [InlineKeyboardButton("📙 السنة الثالثة", callback_data="add_year_year3")],
            [InlineKeyboardButton("⬅ رجوع", callback_data="admin_back")]
        ]
        query.edit_message_text("اختر السنة لإضافة الرابط:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("add_year_"):
        year = data.split("_")[2]
        context.user_data["add_year"] = year
        semesters = {
            "year1": ["semester1", "semester2"],
            "year2": ["semester1", "semester2"],
            "year3": ["semester1"]
        }
        keyboard = [[InlineKeyboardButton(f"📚 الفصل {s[-1]}", callback_data=f"add_sem_{s}")] for s in semesters[year]]
        keyboard.append([InlineKeyboardButton("⬅ رجوع", callback_data="admin_add_link")])
        query.edit_message_text("اختر الفصل الدراسي:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("add_sem_"):
        context.user_data["add_sem"] = data.split("_")[2]
        context.user_data["step"] = "add_name"
        query.edit_message_text("✏ أدخل اسم الملف/الرابط:")

    elif data == "admin_users":
        users = load_json(USERS_FILE, {})
        text = f"👥 عدد المستخدمين: {len(users)}\n\n"
        for u in users.values():
            name = u["name"]
            username = f"@{u['username']}" if u["username"] else ""
            text += f"- {name} {username}\n"
        query.edit_message_text(text)

    elif data == "admin_broadcast":
        context.user_data["step"] = "broadcast"
        query.edit_message_text("✏ أدخل نص الرسالة الجماعية لإرسالها لجميع المستخدمين:")

    elif data == "admin_back":
        admin_panel(query, context)

    # عرض الملفات للمستخدم
    elif data.startswith("year_"):
        show_semesters(query, data.split("_")[1])
    elif data.startswith("sem_"):
        year, sem = data.split("_")[1:3]
        show_files(query, year, sem, context)
    elif data.startswith("sendlink_"):
        send_link(query, data.split("_")[1], context)

# ================== معالجة نص الأدمن ==================
def text_handler(update, context):
    user_id = update.effective_user.id
    step = context.user_data.get("step")

    if user_id != ADMIN_ID:
        return

    if step == "add_name":
        context.user_data["add_name"] = update.message.text
        context.user_data["step"] = "add_link"
        update.message.reply_text("🔗 أدخل رابط الملف:")

    elif step == "add_link":
        year = context.user_data["add_year"]
        sem = context.user_data["add_sem"]
        name = context.user_data["add_name"]
        link = update.message.text
        key = f"{year}/{sem}/{name}"
        links = load_json(LINKS_FILE, {})
        links[key] = link
        save_json(LINKS_FILE, links)
        update.message.reply_text("✅ تم إضافة الرابط بنجاح.")
        context.user_data.clear()

    elif step == "broadcast":
        msg = update.message.text
        users = load_json(USERS_FILE, {})
        count = 0
        for uid in users:
            try:
                context.bot.send_message(chat_id=int(uid), text=msg)
                count += 1
            except:
                continue
        update.message.reply_text(f"📢 تم إرسال الرسالة إلى {count} مستخدم/مستخدمين.")
        context.user_data.clear()

# ================== عرض الفصول ==================
def show_semesters(query, year):
    semesters = {
        "year1": ["semester1", "semester2"],
        "year2": ["semester1", "semester2"],
        "year3": ["semester1"]
    }
    keyboard = [[InlineKeyboardButton(f"📚 الفصل {s[-1]}", callback_data=f"sem_{year}_{s}")] for s in semesters[year]]
    query.edit_message_text("اختر الفصل الدراسي:", reply_markup=InlineKeyboardMarkup(keyboard))

# ================== عرض الملفات ==================
def show_files(query, year, sem, context):
    links = load_json(LINKS_FILE, {})
    keyboard = []
    files_map = {}
    idx = 0
    prefix = f"{year}/{sem}/"
    for key in links:
        if key.startswith(prefix):
            name = key.split("/", 2)[2]
            files_map[str(idx)] = key
            keyboard.append([InlineKeyboardButton(f"🔗 {name}", callback_data=f"sendlink_{idx}")])
            idx += 1
    context.user_data["files"] = files_map
    if not keyboard:
        query.edit_message_text("❌ لا توجد ملفات.")
        return
    query.edit_message_text("الملفات المتاحة:", reply_markup=InlineKeyboardMarkup(keyboard))

# ================== إرسال الرابط ==================
def send_link(query, fid, context):
    key = context.user_data["files"][fid]
    links = load_json(LINKS_FILE, {})
    user = query.from_user
    name = f"@{user.username}" if user.username else user.full_name
    query.message.reply_text(f"🔗 {links[key]}\n\n👤 أرسل بواسطة: {name}")

# ================== بدء البوت ==================
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("admin", admin_panel))
    dp.add_handler(CommandHandler("users", users_cmd))
    dp.add_handler(CallbackQueryHandler(buttons))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, text_handler))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
