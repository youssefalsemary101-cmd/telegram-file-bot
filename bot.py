
import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "أهلاً بك في بوت البحث عن الملفات 📚\n"
        "اكتب اسم الملف الذي تبحث عنه."
    )

async def search_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    await update.message.reply_text(
        f"🔎 طلب البحث: {query}\n\n"
        "البوت جاهز مبدئيًا، وسنضيف فهرس ملفات القناة في الخطوة التالية."
    )

def main():
    if not TOKEN:
        raise RuntimeError("لم يتم ضبط TELEGRAM_BOT_TOKEN في إعدادات التشغيل.")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, search_files)
    )
    app.run_polling()

if __name__ == "__main__":
    main()
