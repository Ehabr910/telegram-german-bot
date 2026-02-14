from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatAction
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import os
import time
import json

# ================== الإعدادات ==================
TOKEN = os.getenv("BOT_TOKEN")
BASE_PATH = "files"
LINKS_FILE = "links.json"

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN غير موجود")

# ================== تحميل روابط الملفات ==================
def load_links():
    if not os.path.exists(LINKS_FILE):
        return {}
    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

FILE_LINKS = load_links()

# ================== /start ==================
def start(update, context):
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
    safe_edit(query, "👋 أهلاً بك مجددًا! اختر السنة:", keyboard)

# ================== عرض الملفات ==================
def show_files(query, year, sem, context):
    folder = os.path.join(BASE_PATH, year, f"semester{sem[-1]}")
    keyboard = []
    files_map = {}
    idx = 0

    # ===== الملفات المحلية =====
    local_files = []
    if os.path.exists(folder):
        local_files = [
            f for f in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, f))
        ]

    for f in local_files:
        files_map[str(idx)] = {"year": year, "sem": sem, "file": f}
        keyboard.append([InlineKeyboardButton(f"📄 {f}", callback_data=f"file_{idx}")])
        idx += 1

    # ===== روابط links.json =====
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
        safe_edit(query, "❌ لا توجد ملفات أو روابط.", [
            [InlineKeyboardButton("⬅️ رجوع", callback_data=f"back_sem_{year}")]
        ])
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

# ================== تعديل آمن مع fallback ==================
def safe_edit(query, text, keyboard=None):
    try:
        query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
        )
    except:
        # لو فشل التعديل، أرسل رسالة جديدة
        query.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
        )

# ================== تشغيل البوت ==================
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
