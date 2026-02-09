from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ChatAction
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
import os
import time
import json

# ================== الإعدادات ==================
TOKEN = os.getenv("BOT_TOKEN")  # مهم لــ Railway
BASE_PATH = "files"
LINKS_FILE = "links.json"

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
        [InlineKeyboardButton("📘 السنة الأولى", callback_data="year1")],
        [InlineKeyboardButton("📗 السنة الثانية", callback_data="year2")],
        [InlineKeyboardButton("📙 السنة الثالثة", callback_data="year3")]
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

    if data in ["year1", "year2", "year3"]:
        show_semesters(query, data)

    elif data == "back":
        start_over(query)

    # ✅ الإصلاح هنا (عرض الملفات)
    elif "_sem" in data and not data.startswith(("choose_", "sendfile_", "sendlink_")):
        show_files(query, data)

    elif data.startswith("choose_"):
        ask_file_or_link(query, data)

    elif data.startswith("sendfile_"):
        send_file(query, data, context)

    elif data.startswith("sendlink_"):
        send_link(query, data)

# ================== الفصول ==================
def show_semesters(query, year):
    semesters = {
        "year1": ["sem1", "sem2"],
        "year2": ["sem1", "sem2"],
        "year3": ["sem1"]
    }

    keyboard = []
    for sem in semesters.get(year, []):
        keyboard.append([
            InlineKeyboardButton(
                f"📚 الفصل {sem[-1]}",
                callback_data=f"{year}_{sem}"
            )
        ])

    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back")])
    query.edit_message_text("اختر الفصل:", reply_markup=InlineKeyboardMarkup(keyboard))

# ================== الرجوع ==================
def start_over(query):
    keyboard = [
        [InlineKeyboardButton("📘 السنة الأولى", callback_data="year1")],
        [InlineKeyboardButton("📗 السنة الثانية", callback_data="year2")],
        [InlineKeyboardButton("📙 السنة الثالثة", callback_data="year3")]
    ]
    query.edit_message_text("اختر السنة:", reply_markup=InlineKeyboardMarkup(keyboard))

# ================== عرض الملفات ==================
def show_files(query, data):
    year, sem = data.split("_")
    folder_path = os.path.join(BASE_PATH, year, f"semester{sem[-1]}")

    keyboard = []

    # ملفات موجودة محليًا
    if os.path.exists(folder_path):
        for file in os.listdir(folder_path):
            keyboard.append([
                InlineKeyboardButton(
                    f"📄 {file}",
                    callback_data=f"choose_{year}_{sem}_{file}"
                )
            ])

    # ملفات لها روابط فقط
    for key in FILE_LINKS:
        if key.startswith(f"{year}/semester{sem[-1]}/"):
            file_name = key.split("/")[-1]
            if not any(file_name in btn[0].text for btn in keyboard):
                keyboard.append([
                    InlineKeyboardButton(
                        f"🔗 {file_name}",
                        callback_data=f"choose_{year}_{sem}_{file_name}"
                    )
                ])

    if not keyboard:
        query.edit_message_text("❌ لا توجد ملفات أو روابط.")
        return

    keyboard.append([InlineKeyboardButton("⬅️ رجوع", callback_data=year)])
    query.edit_message_text("اختر الملف:", reply_markup=InlineKeyboardMarkup(keyboard))

# ================== سؤال ملف أم رابط ==================
def ask_file_or_link(query, data):
    _, year, sem, file_name = data.split("_", 3)

    keyboard = [
        [InlineKeyboardButton("⬇️ تحميل الملف", callback_data=f"sendfile_{year}_{sem}_{file_name}")],
        [InlineKeyboardButton("🔗 فتح الرابط", callback_data=f"sendlink_{year}_{sem}_{file_name}")],
        [InlineKeyboardButton("⬅️ رجوع", callback_data=f"{year}_{sem}")]
    ]

    query.edit_message_text(
        f"📄 {file_name}\n\nاختر طريقة الحصول:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ================== إرسال الملف ==================
def send_file(query, data, context):
    _, year, sem, file_name = data.split("_", 3)
    file_path = os.path.join(BASE_PATH, year, f"semester{sem[-1]}", file_name)

    if not os.path.exists(file_path):
        query.message.reply_text(
            "⚠️ الملف غير موجود محليًا.\n"
            "يمكنك استخدام خيار الرابط."
        )
        return

    context.bot.send_chat_action(query.message.chat_id, ChatAction.UPLOAD_DOCUMENT)
    time.sleep(0.3)

    with open(file_path, "rb") as f:
        query.message.reply_document(f, caption=f"✅ {file_name}")

# ================== إرسال الرابط ==================
def send_link(query, data):
    _, year, sem, file_name = data.split("_", 3)
    key = f"{year}/semester{sem[-1]}/{file_name}"

    link = FILE_LINKS.get(key)
    if not link:
        query.message.reply_text("❌ لا يوجد رابط لهذا الملف.")
        return

    query.message.reply_text(f"🔗 رابط الملف:\n{link}")

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
