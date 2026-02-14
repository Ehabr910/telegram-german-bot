from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatAction
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
import os
import time
import json

# ================== الإعدادات ==================
TOKEN = os.getenv("BOT_TOKEN")
BASE_PATH = "files"
LINKS_FILE = "links.json"
USERS_FILE = "users.json"
BANNED_FILE = "banned.json"
ADMIN_ID = 5037555049  # ضع معرف تيليجرام للادمن

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN غير موجود")

# ================== تحميل روابط الملفات ==================
def load_links():
    if not os.path.exists(LINKS_FILE):
        return {}
    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

FILE_LINKS = load_links()

# ================== حفظ المستخدم ==================
def save_user(user):
    users = []
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
    if not any(u["id"] == user.id for u in users):
        users.append({"id": user.id, "name": user.full_name})
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)

# ================== التحقق من الحظر ==================
def is_banned(user_id):
    if not os.path.exists(BANNED_FILE):
        return False
    with open(BANNED_FILE, "r", encoding="utf-8") as f:
        banned = json.load(f)
    return user_id in banned

def ban_user(user_id):
    banned = []
    if os.path.exists(BANNED_FILE):
        with open(BANNED_FILE, "r", encoding="utf-8") as f:
            banned = json.load(f)
    if user_id not in banned:
        banned.append(user_id)
        with open(BANNED_FILE, "w", encoding="utf-8") as f:
            json.dump(banned, f)

def unban_user(user_id):
    banned = []
    if os.path.exists(BANNED_FILE):
        with open(BANNED_FILE, "r", encoding="utf-8") as f:
            banned = json.load(f)
    if user_id in banned:
        banned.remove(user_id)
        with open(BANNED_FILE, "w", encoding="utf-8") as f:
            json.dump(banned, f)

# ================== /start ==================
def start(update, context):
    user = update.message.from_user
    if is_banned(user.id):
        update.message.reply_text("❌ أنت محظور من استخدام البوت.")
        return
    save_user(user)
    keyboard = [
        [InlineKeyboardButton("📘 السنة الأولى", callback_data="year_year1")],
        [InlineKeyboardButton("📗 السنة الثانية", callback_data="year_year2")],
        [InlineKeyboardButton("📙 السنة الثالثة", callback_data="year_year3")]
    ]
    update.message.reply_text(
        "👋 أهلاً بك في بوت مجتمع اللغة الألمانية 🇩🇪\n"
        "✨ اختر السنة للمتابعة:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================== أوامر الادمن ==================
def admin_command(update, context):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        update.message.reply_text("❌ ليس لديك صلاحية الوصول.")
        return
    keyboard = [
        [InlineKeyboardButton("عدد المستخدمين", callback_data="admin_users_count")],
        [InlineKeyboardButton("قائمة المستخدمين", callback_data="admin_users_list")],
        [InlineKeyboardButton("إرسال رسالة جماعية", callback_data="admin_broadcast")],
        [InlineKeyboardButton("حظر مستخدم", callback_data="admin_ban_user")],
        [InlineKeyboardButton("فك حظر مستخدم", callback_data="admin_unban_user")],
        [InlineKeyboardButton("معلومات البوت", callback_data="admin_bot_info")]
    ]
    update.message.reply_text("🔧 لوحة تحكم الادمن:", reply_markup=InlineKeyboardMarkup(keyboard))

def users_command(update, context):
    if not os.path.exists(USERS_FILE):
        update.message.reply_text("لا يوجد مستخدمين مسجلين.")
        return
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
    text = "قائمة المستخدمين:\n\n" + "\n".join([f"{u['id']} - {u['name']}" for u in users])
    update.message.reply_text(text)

# ================== معالج الأزرار ==================
def button_handler(update, context):
    query = update.callback_query
    query.answer()
    data = query.data

    if data.startswith("year_"):
        show_semesters(query, data.split("_")[1])

    elif data.startswith("sem_"):
        year, sem = data.split("_")[1:3]
        show_files(query, year, sem, context)

    elif data.startswith("file_"):
        ask_file_or_link(query, data.split("_")[1], context)

    elif data.startswith("sendfile_"):
        send_file(query, data.split("_")[1], context)

    elif data.startswith("sendlink_"):
        send_link(query, data.split("_")[1], context)

    elif data.startswith("back_"):
        parts = data.split("_")
        if parts[1] == "year":
            start_over(query)
        elif parts[1] == "sem":
            show_semesters(query, parts[2])
        elif parts[1] == "files":
            show_files(query, parts[2], parts[3], context)

    elif data.startswith("admin_"):
        handle_admin_buttons(query, data, context)

# ================== عرض الفصول ==================
def show_semesters(query, year):
    semesters = {
        "year1": ["sem1", "sem2"],
        "year2": ["sem1", "sem2"],
        "year3": ["sem1"]
    }
    keyboard = [
        [InlineKeyboardButton(f"📚 الفصل {s[-1]}", callback_data=f"sem_{year}_{s}")]
        for s in semesters.get(year, [])
    ]
    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_year")])
    safe_edit(query, "اختر الفصل:", keyboard)

def start_over(query):
    keyboard = [
        [InlineKeyboardButton("📘 السنة الأولى", callback_data="year_year1")],
        [InlineKeyboardButton("📗 السنة الثانية", callback_data="year_year2")],
        [InlineKeyboardButton("📙 السنة الثالثة", callback_data="year_year3")]
    ]
    safe_edit(query, "اختر السنة:", keyboard)

# ================== عرض الملفات ==================
def show_files(query, year, sem, context):
    folder = os.path.join(BASE_PATH, year, f"semester{sem[-1]}")
    keyboard = []
    files_map = {}
    idx = 0

    local_files = []
    if os.path.exists(folder):
        local_files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]

    for f in local_files:
        files_map[str(idx)] = {"year": year, "sem": sem, "file": f}
        keyboard.append([InlineKeyboardButton(f"📄 {f}", callback_data=f"file_{idx}")])
        idx += 1

    prefix = f"{year}/semester{sem[-1]}/"
    for key in FILE_LINKS:
        if not key.startswith(prefix):
            continue
        fname = key.split("/")[-1]
        if fname in local_files:
            continue
        files_map[str(idx)] = {"year": year, "sem": sem, "file": fname}
        keyboard.append([InlineKeyboardButton(f"🔗 {fname}", callback_data=f"file_{idx}")])
        idx += 1

    if not keyboard:
        safe_edit(query, "❌ لا توجد ملفات أو روابط.", [[InlineKeyboardButton("⬅️ رجوع", callback_data=f"back_sem_{year}")]])
        return

    context.user_data["files"] = files_map
    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data=f"back_sem_{year}")])
    safe_edit(query, "اختر الملف:", keyboard)

# ================== اختيار طريقة الإرسال ==================
def ask_file_or_link(query, fid, context):
    info = context.user_data["files"].get(fid)
    if not info:
        query.message.reply_text("❌ الملف غير معروف.")
        return
    buttons = []
    file_path = os.path.join(BASE_PATH, info["year"], f"semester{info['sem'][-1]}", info["file"])
    key = f"{info['year']}/semester{info['sem'][-1]}/{info['file']}"

    if os.path.exists(file_path):
        buttons.append([InlineKeyboardButton("⬇️ تحميل الملف", callback_data=f"sendfile_{fid}")])
    if key in FILE_LINKS:
        buttons.append([InlineKeyboardButton("🔗 فتح الرابط", callback_data=f"sendlink_{fid}")])

    buttons.append([InlineKeyboardButton("⬅️ رجوع", callback_data=f"back_files_{info['year']}_{info['sem']}")])
    safe_edit(query, f"📄 {info['file']}\n\nاختر طريقة الحصول:", buttons)

# ================== إرسال الملف ==================
def send_file(query, fid, context):
    info = context.user_data["files"].get(fid)
    path = os.path.join(BASE_PATH, info["year"], f"semester{info['sem'][-1]}", info["file"])
    if not os.path.exists(path):
        query.message.reply_text("⚠️ الملف غير موجود.")
        return
    context.bot.send_chat_action(query.message.chat_id, ChatAction.UPLOAD_DOCUMENT)
    time.sleep(0.3)
    with open(path, "rb") as f:
        query.message.reply_document(f)

# ================== إرسال الرابط ==================
def send_link(query, fid, context):
    info = context.user_data["files"].get(fid)
    key = f"{info['year']}/semester{info['sem'][-1]}/{info['file']}"
    link = FILE_LINKS.get(key)
    if not link:
        query.message.reply_text("❌ لا يوجد رابط.")
        return
    query.message.reply_text(f"🔗 رابط الملف:\n{link}")

# ================== تعديل آمن ==================
def safe_edit(query, text, keyboard=None):
    try:
        query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None)
    except:
        pass

# ================== أزرار الادمن ==================
def handle_admin_buttons(query, data, context):
    if data == "admin_users_count":
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                users = json.load(f)
            query.edit_message_text(f"👥 عدد المستخدمين: {len(users)}")
        else:
            query.edit_message_text("لا يوجد مستخدمين.")
    elif data == "admin_users_list":
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                users = json.load(f)
            text = "\n".join([f"{u['id']} - {u['name']}" for u in users])
            query.edit_message_text(f"قائمة المستخدمين:\n{text}")
        else:
            query.edit_message_text("لا يوجد مستخدمين.")
    elif data == "admin_broadcast":
        query.edit_message_text("💬 الرجاء إرسال الرسالة المراد إرسالها جماعياً.")
        context.user_data["broadcast_mode"] = True
    elif data == "admin_ban_user":
        query.edit_message_text("🚫 أرسل معرف المستخدم المراد حظره.")
        context.user_data["ban_mode"] = True
    elif data == "admin_unban_user":
        query.edit_message_text("✅ أرسل معرف المستخدم لفك الحظر عنه.")
        context.user_data["unban_mode"] = True
    elif data == "admin_bot_info":
        users_count = 0
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                users_count = len(json.load(f))
        query.edit_message_text(f"🤖 معلومات البوت:\nعدد المستخدمين: {users_count}")
    else:
        query.edit_message_text("🔧 ميزة الادمن قيد التطوير...")

# ================== التعامل مع الرسائل أثناء وضع الادمن ==================
def message_handler(update, context):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        return
    text = update.message.text
    if context.user_data.get("broadcast_mode"):
        context.user_data["broadcast_mode"] = False
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                users = json.load(f)
            for u in users:
                try:
                    context.bot.send_message(u["id"], f"📢 رسالة جماعية:\n{text}")
                except:
                    continue
        update.message.reply_text("✅ تم إرسال الرسالة لجميع المستخدمين.")
    elif context.user_data.get("ban_mode"):
        context.user_data["ban_mode"] = False
        try:
            uid = int(text)
            ban_user(uid)
            update.message.reply_text(f"🚫 تم حظر المستخدم: {uid}")
        except:
            update.message.reply_text("❌ معرف غير صالح.")
    elif context.user_data.get("unban_mode"):
        context.user_data["unban_mode"] = False
        try:
            uid = int(text)
            unban_user(uid)
            update.message.reply_text(f"✅ تم فك حظر المستخدم: {uid}")
        except:
            update.message.reply_text("❌ معرف غير صالح.")

# ================== تشغيل البوت ==================
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("admin", admin_command))
    dp.add_handler(CommandHandler("users", users_command))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
