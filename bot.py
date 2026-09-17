import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from flask import Flask
from threading import Thread

# ⚠️ لا تنسى تخلي التوكن مالتك هنا بين علامات التنصيص بدل هاي الكلمة
TOKEN = "8845568658:AAE-99JyBv0nDDJo2kU5J-XzS62j44QKlEg"

# إعداد خادم الويب الوهمي حتى السيرفر ما يطفي البوت
app_web = Flask(__name__)
@app_web.route('/')
def home():
    return "البوت يعمل بنجاح 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app_web.run(host="0.0.0.0", port=port)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    
    if not ("youtube.com" in url or "youtu.be" in url):
        await update.message.reply_text("❌ يرجى إرسال رابط من يوتيوب فقط.")
        return

    msg = await update.message.reply_text("⏳ جاري فحص الرابط...")
    ydl_opts_info = {'quiet': True, 'extract_flat': True}

    try:
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(url, download=False)
            
        if 'entries' in info:
            entries = list(info['entries'])
            await msg.edit_text(f"📁 تم اكتشاف قائمة تشغيل تحتوي على {len(entries)} مقطع.\n⏳ جاري التحميل...")
            urls_to_download = [entry.get('url', f"https://www.youtube.com/watch?v={entry.get('id')}") for entry in entries]
        else:
            await msg.edit_text("🎵 جاري تحميل الصوت بأعلى جودة...")
            urls_to_download = [url]

        ydl_opts_download = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': '%(id)s.%(ext)s',
            'quiet': True,
            'noplaylist': True
        }

        for vid_url in urls_to_download:
            try:
                with yt_dlp.YoutubeDL(ydl_opts_download) as ydl:
                    vid_info = ydl.extract_info(vid_url, download=True)
                    filename = ydl.prepare_filename(vid_info)
                
                await context.bot.send_audio(
                    chat_id=update.effective_chat.id, 
                    audio=open(filename, 'rb'),
                    title=vid_info.get('title', 'صوتيات يوتيوب'),
                    read_timeout=60, write_timeout=60
                )
                os.remove(filename)
            except Exception as e:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"⚠️ لم أتمكن من تحميل أحد المقاطع، جاري إكمال الباقي...")
                
        await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ تمت عملية التحميل بنجاح!")
        
    except Exception as e:
        await msg.edit_text(f"❌ عذراً، حدث خطأ: {str(e)}")

def main():
    # تشغيل خادم الويب في الخلفية
    Thread(target=run_web).start()
    
    # تشغيل البوت
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
