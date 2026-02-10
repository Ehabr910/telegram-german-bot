from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatAction
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import os
import time
import json

# ================== الإعدادات ==================
TOKEN = os.getenv("BOT_TOKEN")  # Railway / Local
BASE_PATH = "files"
LINKS_FILE = "links.json"
ALLOWED_EXTS = (".png", ".jpg", ".jpeg", ".pdf")

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

    if data.startswith("year_"):       # اختيار سنة
        year = data.split("_")[1]
        show_semesters(query, year)
    elif data.startswith("sem_"):      # اختيار فصل
        year, sem = data.split("_")[1:3]
        show_files(query, year, sem, context)
    elif data.startswith("file_"):     # اختيار ملف
        fid = data.split("_")[1]
        ask_file_or_link(query, fid, context)
    elif data.startswith("sendfile_"): # إرسال ملف
        fid = data.split("_")[1]
        send_file(query, fid, context)
    elif data.startswith("sendlink_"): # إرسال رابط
        fid = data.split("_")[1]
        send_link(query, fid, context)
    elif data.startswith("back_"):     # زر رجوع
        action = data.split("_")[1]
        if action == "year":
            start_over(query)
        elif action == "sem":
            year = data.split("_")[2]
            show_semesters(query, year)
        elif action == "files":
            year, sem = data.split("_")[2:4]
            show_files(query, year, sem, context)

# ================== عرض الفصول ==================
def show_semesters(query, year):
    semesters = {
        "year1": ["sem1", "sem2"],
        "year2": ["sem1", "sem2"],
        "year3": ["sem1"]
    }
    keyboard = [[InlineKeyboardButton(f"📚 الفصل {s[-1]}", callback_data=f"sem_{year}_{s}")] for s in semesters.get(year, [])]
    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data=f"back_year")])
    safe_edit(query, "اختر الفصل:", keyboard)

# ================== الرجوع ==================
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

    # ملفات محلية
    if os.path.exists(folder):
        for f in os.listdir(folder):
            if not f.lower().endswith(ALLOWED_EXTS):
                continue
            fid = f"{idx}"
            files_map[fid] = {"year": year, "sem": sem, "file": f}
            keyboard.append([InlineKeyboardButton(f"📄 {f}", callback_data=f"file_{fid}")])
            idx += 1

    # ملفات روابط فقط
    existing_files = [v["file"] for v in files_map.values()]
    for key in FILE_LINKS:
        if key.startswith(f"{year}/semester{sem[-1]}/"):
            fname = key.split("/")[-1]
            if fname not in existing_files and fname.lower().endswith(ALLOWED_EXTS):
                fid = f"{idx}"
                files_map[fid] = {"year": year, "sem": sem, "file": fname}
                keyboard.append([InlineKeyboardButton(f"🔗 {fname}", callback_data=f"file_{fid}")])
                idx += 1

    if not keyboard:
        query.message.reply_text("❌ لا توجد ملفات أو روابط.")
        return

    context.user_data["files"] = files_map
    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data=f"back_sem_{year}")])
    safe_edit(query, "اختر الملف:", keyboard)

# ================== سؤال تحميل أم رابط ==================
def ask_file_or_link(query, fid, context):
    info = context.user_data["files"].get(fid)
    if not info:
        query.message.reply_text("❌ الملف غير معروف.")
        return

    keyboard = [
        [InlineKeyboardButton("⬇️ تحميل الملف", callback_data=f"sendfile_{fid}")],
        [InlineKeyboardButton("🔗 فتح الرابط", callback_data=f"sendlink_{fid}")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data=f"back_files_{info['year']}_{info['sem']}")]
    ]
    safe_edit(query, f"📄 {info['file']}\n\nاختر طريقة الحصول:", keyboard)

# ================== إرسال الملف ==================
def send_file(query, fid, context):
    info = context.user_data["files"].get(fid)
    if not info:
        query.message.reply_text("❌ الملف غير موجود.")
        return

    path = os.path.join(BASE_PATH, info["year"], f"semester{info['sem'][-1]}", info["file"])
    if not os.path.exists(path):
        query.message.reply_text("⚠️ الملف غير موجود محليًا. استخدم الرابط.")
        return

    context.bot.send_chat_action(query.message.chat_id, ChatAction.UPLOAD_DOCUMENT)
    time.sleep(0.3)
    with open(path, "rb") as f:
        query.message.reply_document(f, caption=f"✅ {info['file']}")

# ================== إرسال الرابط ==================
def send_link(query, fid, context):
    info = context.user_data["files"].get(fid)
    if not info:
        query.message.reply_text("❌ الملف غير معروف.")
        return

    key = f"{info['year']}/semester{info['sem'][-1]}/{info['file']}"
    link = FILE_LINKS.get(key)
    if not link:
        query.message.reply_text("❌ لا يوجد رابط لهذا الملف.")
        return

    query.message.reply_text(f"🔗 رابط الملف:\n{link}")

# ================== دالة آمنة لتعديل الرسالة ==================
def safe_edit(query, text, keyboard=None):
    try:
        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
        query.edit_message_text(text, reply_markup=reply_markup)
    except:
        pass  # تجاهل أي خطأ مثل "Message is not modified"

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
