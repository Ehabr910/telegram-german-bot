from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import os
import json

# ================== الإعدادات ==================
TOKEN = os.getenv("BOT_TOKEN")
LINKS_FILE = "links.json"

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN غير موجود")

# ================== تحميل الروابط ==================
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
        "اختر السنة:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================== الأزرار ==================
def button_handler(update, context):
    query = update.callback_query
    query.answer()
    data = query.data

    if data.startswith("year_"):
        year = data.split("_")[1]
        show_semesters(query, year)

    elif data.startswith("sem_"):
        year, sem = data.split("_")[1:3]
        show_files(query, year, sem, context)

    elif data.startswith("file_"):
        key = data.replace("file_", "")
        send_link(query, key)

    elif data == "back_year":
        start_over(query)

    elif data.startswith("back_sem_"):
        year = data.split("_")[2]
        show_semesters(query, year)

# ================== الفصول ==================
def show_semesters(query, year):
    semesters = {
        "year1": ["semester1", "semester2"],
        "year2": ["semester1", "semester2"],
        "year3": ["semester1"]
    }

    keyboard = [
        [InlineKeyboardButton(f"📚 الفصل {s[-1]}", callback_data=f"sem_{year}_{s}")]
        for s in semesters.get(year, [])
    ]
    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back_year")])

    safe_edit(query, "اختر الفصل:", keyboard)

# ================== عرض الملفات (روابط فقط) ==================
def show_files(query, year, sem, context):
    keyboard = []

    for path in FILE_LINKS:
        if path.startswith(f"{year}/{sem}/"):
            filename = path.split("/")[-1]
            keyboard.append([
                InlineKeyboardButton(f"🔗 {filename}", callback_data=f"file_{path}")
            ])

    if not keyboard:
        safe_edit(query, "❌ لا توجد روابط لهذا الفصل.")
        return

    keyboard.append([
        InlineKeyboardButton("⬅️ رجوع", callback_data=f"back_sem_{year}")
    ])

    safe_edit(query, "اختر الملف:", keyboard)

# ================== إرسال الرابط ==================
def send_link(query, key):
    link = FILE_LINKS.get(key)
    if not link:
        query.message.reply_text("❌ الرابط غير موجود.")
        return

    query.message.reply_text(f"🔗 رابط الملف:\n{link}")

# ================== رجوع للبداية ==================
def start_over(query):
    keyboard = [
        [InlineKeyboardButton("📘 السنة الأولى", callback_data="year_year1")],
        [InlineKeyboardButton("📗 السنة الثانية", callback_data="year_year2")],
        [InlineKeyboardButton("📙 السنة الثالثة", callback_data="year_year3")]
    ]
    safe_edit(query, "اختر السنة:", keyboard)

# ================== تعديل آمن ==================
def safe_edit(query, text, keyboard=None):
    try:
        query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
        )
    except:
        pass

# ================== تشغيل ==================
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
