from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatAction, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import os
import time
import json

# ================== الإعدادات ==================
TOKEN = os.getenv("BOT_TOKEN")
BASE_PATH = "files"
LINKS_FILE = "links.json"
USERS_FILE = "users.json"
BANNED_FILE = "banned.json"

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN غير موجود")

# ================== تحميل البيانات ==================
def load_json(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

FILE_LINKS = load_json(LINKS_FILE)
USERS = load_json(USERS_FILE)
BANNED = load_json(BANNED_FILE)

BROADCAST_WAITING = {}  # انتظار رسالة جماعية

# ================== /start ==================
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    if str(user.id) not in USERS and str(user.id) not in BANNED:
        USERS[str(user.id)] = {"id": user.id, "name": user.full_name}
        save_json(USERS_FILE, USERS)

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

# ================== لوحة الأدمن ==================
ADMIN_IDS = [5037555049]  # ضع هنا رقم معرف الأدمن

def admin_panel(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        update.message.reply_text("❌ أنت لست الأدمن!")
        return

    keyboard = [
        [InlineKeyboardButton("✉️ رسالة جماعية", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📋 قائمة المستخدمين", callback_data="admin_users")],
        [InlineKeyboardButton("🚫 حظر مستخدم", callback_data="admin_ban_user")],
        [InlineKeyboardButton("✅ فك حظر مستخدم", callback_data="admin_unban_user")],
        [InlineKeyboardButton("ℹ️ معلومات البوت", callback_data="admin_info")]
    ]
    update.message.reply_text(
        "⚙️ لوحة تحكم الأدمن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================== معالج الأزرار ==================
def button_handler(update: Update, context: CallbackContext):
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
    elif data == "admin_broadcast":
        user_id = query.from_user.id
        BROADCAST_WAITING[user_id] = True
        query.edit_message_text("✉️ أرسل الآن الرسالة التي تريد بثها لجميع المستخدمين:")
    elif data == "admin_users":
        text = "👥 قائمة المستخدمين:\n"
        for u in USERS.values():
            text += f"- {u['name']} ({u['id']})\n"
        query.edit_message_text(text)
    elif data == "admin_ban_user":
        query.edit_message_text("🚫 أرسل الآن معرف المستخدم الذي تريد حظره:")
        context.user_data["waiting_ban"] = True
    elif data == "admin_unban_user":
        query.edit_message_text("✅ أرسل الآن معرف المستخدم الذي تريد فك الحظر عنه:")
        context.user_data["waiting_unban"] = True
    elif data == "admin_info":
        text = (
            f"ℹ️ معلومات البوت:\n"
            f"- عدد الملفات: {sum([len(files) for files in FILE_LINKS.values()])}\n"
            f"- عدد المستخدمين: {len(USERS)}\n"
            f"- عدد المحظورين: {len(BANNED)}"
        )
        query.edit_message_text(text)

# ================== التعامل مع حظر وفك الحظر ==================
def handle_text(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    if BROADCAST_WAITING.get(user_id):
        # البث الجماعي
        count = 0
        for u in USERS.values():
            try:
                context.bot.send_message(chat_id=u["id"], text=text)
                count += 1
            except:
                continue
        update.message.reply_text(f"✅ تم إرسال الرسالة إلى {count} مستخدم/مستخدمين.")
        BROADCAST_WAITING.pop(user_id)
    elif context.user_data.get("waiting_ban"):
        BANNED[text] = {"id": text}
        if text in USERS:
            USERS.pop(text)
        save_json(BANNED_FILE, BANNED)
        save_json(USERS_FILE, USERS)
        update.message.reply_text(f"🚫 تم حظر المستخدم {text}.")
        context.user_data["waiting_ban"] = False
    elif context.user_data.get("waiting_unban"):
        if text in BANNED:
            BANNED.pop(text)
            save_json(BANNED_FILE, BANNED)
            update.message.reply_text(f"✅ تم فك الحظر عن المستخدم {text}.")
        else:
            update.message.reply_text("❌ هذا المستخدم غير محظور.")
        context.user_data["waiting_unban"] = False

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
    user_name = query.from_user.full_name
    with open(path, "rb") as f:
        query.message.reply_document(f, caption=f"📄 الملف: {info['file']}\n👤 طلبه: {user_name}")

# ================== إرسال الرابط ==================
def send_link(query, fid, context):
    info = context.user_data["files"].get(fid)
    key = f"{info['year']}/semester{info['sem'][-1]}/{info['file']}"
    link = FILE_LINKS.get(key)
    if not link:
        query.message.reply_text("❌ لا يوجد رابط.")
        return
    user_name = query.from_user.full_name
    query.message.reply_text(f"🔗 رابط الملف: {link}\n👤 طلبه: {user_name}")

# ================== تعديل آمن ==================
def safe_edit(query, text, keyboard=None):
    try:
        query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None)
    except:
        pass

# ================== تشغيل البوت ==================
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("admin", admin_panel))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
