import os
import threading
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask

# هنا نجيب التوكن من متغير بيئي
BOT_TOKEN = os.environ.get("7572622704:AAHEnQI4UVB9H7yLmaHWBG2ZQXuKPrzaVng")

# خيارات السنة والفصل والمواد
YEARS = ["سنة أولى", "سنة ثانية", "سنة ثالثة", "سنة رابعة"]
SEMESTERS = ["الفصل الدراسي الأول", "الفصل الدراسي الثاني"]
# المواد ممكن تغيّرها حسب تخصصك
SUBJECTS = {
    "سنة أولى": ["رياضيات", "برمجة"],
    "سنة ثانية": ["إحصاء", "شبكات"],
    "سنة ثالثة": ["ذكاء اصطناعي"],
    "سنة رابعة": ["مشروع تخرج"]
}
TYPES = ["نظري", "عملي"]

# نحفظ حالة كل مستخدم
user_state = {}

# الأمر /start يبدأ المحادثة
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(y, callback_data=y)] for y in YEARS]
    await update.message.reply_text("اختر السنة:", reply_markup=InlineKeyboardMarkup(keyboard))

# هذا يعالج ضغطات الأزرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id
    data = query.data

    state = user_state.get(uid, {"step": 1})
    step = state["step"]

    if data == "رجوع":
        step = max(1, step - 1)
    else:
        if step == 1:
            state["year"] = data; step = 2
        elif step == 2:
            state["semester"] = data; step = 3
        elif step == 3:
            state["subject"] = data; step = 4
        elif step == 4:
            state["type"] = data
            await send_files(query, state)
            user_state[uid] = {"step": 1}
            return

    state["step"] = step
    user_state[uid] = state
    await show_next(query, state)

async def show_next(query, state):
    step = state["step"]
    if step == 2:
        choices = SEMESTERS
        text = "اختر الفصل الدراسي:"
    elif step == 3:
        choices = SUBJECTS.get(state["year"], [])
        text = "اختر المادة:"
    elif step == 4:
        choices = TYPES
        text = "اختر نوع الملف:"
    else:
        return

    keyboard = [[InlineKeyboardButton(c, callback_data=c)] for c in choices]
    keyboard.append([InlineKeyboardButton("رجوع", callback_data="رجوع")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def send_files(query, state):
    base = f"data/{state['year']}/{state['semester']}/{state['subject']}/{state['type']}"
    if not os.path.exists(base):
        await query.edit_message_text("لا توجد ملفات.")
        return
    files = os.listdir(base)
    if not files:
        await query.edit_message_text("لا توجد ملفات.")
        return
    await query.edit_message_text("جاري إرسال الملفات...")
    for fname in files:
        path = os.path.join(base, fname)
        with open(path, "rb") as f:
            await query.message.bot.send_document(chat_id=query.message.chat.id, document=f)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    # start Flask so Render ping
    flask_app = Flask("")

    @flask_app.route("/")
    def home():
        return "Alive"

    threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=8080)).start()

    app.run_polling()

if __name__ == "__main__":
    main()
