import os
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# لا تنسى تحط التوكن مالتك هنا بين علامات التنصيص
TOKEN = "8845568658:AAE-99JyBv0nDDJo2kU5J-XzS62j44QKlEg"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    
    # 1. فلترة الروابط: نقبل يوتيوب فقط
    if not ("youtube.com" in url or "youtu.be" in url):
        await update.message.reply_text("❌ يرجى إرسال رابط من يوتيوب فقط.")
        return

    msg = await update.message.reply_text("⏳ جاري فحص الرابط...")

    # إعدادات مبدئية لمعرفة هل الرابط مقطع واحد لو لسته (قائمة تشغيل)
    ydl_opts_info = {
        'quiet': True,
        'extract_flat': True, # لجلب محتوى قائمة التشغيل بسرعة بدون تحميل
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
            info = ydl.extract_info(url, download=False)
            
        # 2. فحص إذا كان الرابط قائمة تشغيل أو مقطع
        if 'entries' in info:
            entries = list(info['entries'])
            await msg.edit_text(f"📁 تم اكتشاف قائمة تشغيل تحتوي على {len(entries)} مقطع.\n⏳ جاري تحميل الصوت بأعلى جودة، سيتم إرسالها تباعاً...")
            # استخراج روابط المقاطع من القائمة
            urls_to_download = [entry.get('url', f"https://www.youtube.com/watch?v={entry.get('id')}") for entry in entries]
        else:
            await msg.edit_text("🎵 جاري تحميل الصوت بأعلى جودة...")
            urls_to_download = [url]

        # 3. إعدادات تحميل الصوت فقط بأعلى جودة
        ydl_opts_download = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best', # سحب الصوت بصيغة m4a لتعمل في تليكرام كموسيقى
            'outtmpl': '%(id)s.%(ext)s',
            'quiet': True,
            'noplaylist': True # نوقف تحميل القوائم هنا لأن الكود هو اللي راح يمر عليها واحد واحد
        }

        # لوب (دورة) للتحميل: إذا مقطع واحد راح يمر مرة وحدة، وإذا لسته راح يمر عليها كلها
        for vid_url in urls_to_download:
            try:
                with yt_dlp.YoutubeDL(ydl_opts_download) as ydl:
                    vid_info = ydl.extract_info(vid_url, download=True)
                    filename = ydl.prepare_filename(vid_info)
                
                # إرسال الملف كملف صوتي (موسيقى) للتليكرام
                await context.bot.send_audio(
                    chat_id=update.effective_chat.id, 
                    audio=open(filename, 'rb'),
                    title=vid_info.get('title', 'صوتيات يوتيوب'),
                    read_timeout=60,
                    write_timeout=60
                )
                
                os.remove(filename) # مسح الملف من الحاسبة بعد الإرسال
            except Exception as e:
                # إذا فشل مقطع معين (مثلاً محذوف أو خاص) يبلغك ويكمل باقي اللستة
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"⚠️ لم أتمكن من تحميل أحد المقاطع. قد يكون محذوفاً أو خاصاً.")
                
        await context.bot.send_message(chat_id=update.effective_chat.id, text="✅ تمت عملية التحميل بنجاح!")
        
    except Exception as e:
        await msg.edit_text(f"❌ عذراً، حدث خطأ: {str(e)}")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("البوت يشتغل هسه... روح جربه بالتليكرام!")
    app.run_polling()

if __name__ == '__main__':
    main()