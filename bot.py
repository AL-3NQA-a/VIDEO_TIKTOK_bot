import os
import re
import requests
import telebot
from telebot import types
import json
import logging
from urllib.parse import quote
import time
import sys

# إعدادات البوت - سيتم أخذ التوكن من متغير البيئة
API_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
bot = telebot.TeleBot(API_TOKEN)

# إعداد السجل logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# استخدام واجهات برمجة حديثة
def get_tiktok_video_info(url):
    try:
        logger.info(f"معالجة الرابط: {url}")
        
        # تنظيف الرابط
        if "?" in url:
            url = url.split("?")[0]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Origin': 'https://snaptik.app',
            'Connection': 'keep-alive',
        }
        
        # محاولة واجهات برمجة متعددة
        apis = [
            f"https://api.tikmate.app/api/lookup?url={quote(url)}",
            f"https://api.douyin.wtf/api?url={quote(url)}",
            f"https://www.tikwm.com/api/?url={quote(url)}",
        ]
        
        for api_url in apis:
            try:
                logger.info(f"جرب واجهة برمجة التطبيقات: {api_url}")
                response = requests.get(api_url, headers=headers, timeout=15)
                data = response.json()
                
                if api_url.startswith("https://api.tikmate.app"):
                    if data.get('success'):
                        logger.info("تم الحصول على بيانات من tikmate.app")
                        return {
                            'title': 'فيديو تيك توك',
                            'author': {'nickname': data.get('author_name', 'مجهول')},
                            'play': data['url'],
                            'digg_count': 0,
                            'share_count': 0,
                            'comment_count': 0,
                            'play_count': 0
                        }
                
                elif api_url.startswith("https://api.douyin.wtf"):
                    if data.get('status') == 'success':
                        logger.info("تم الحصول على بيانات من douyin.wtf")
                        return {
                            'title': data.get('desc', 'فيديو تيك توك'),
                            'author': {'nickname': data.get('author', 'مجهول')},
                            'play': data['video']['play_addr'],
                            'digg_count': data.get('digg_count', 0),
                            'share_count': data.get('share_count', 0),
                            'comment_count': data.get('comment_count', 0),
                            'play_count': data.get('play_count', 0)
                        }
                
                elif api_url.startswith("https://www.tikwm.com"):
                    if data.get('code') == 0:
                        logger.info("تم الحصول على بيانات من tikwm.com")
                        return data['data']
            
            except Exception as e:
                logger.error(f"فشلت واجهة برمجة التطبيقات: {api_url}, الخطأ: {e}")
                continue
        
        return None
        
    except Exception as e:
        logger.error(f"خطأ في الحصول على معلومات تيك توك: {e}")
        return None

# أمر البدء /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = """
    🎵 مرحباً بك في بوت تحميل فيديوهات TikTok! 🎵

    فقط أرسل رابط فيديو TikTok وسأقوم بتحميله لك بدون علامة مائية.

    📌 مثال: 
    https://vm.tiktok.com/ZSExample/
    أو
    https://www.tiktok.com/@user/video/1234567890

    ❗ ملاحظة: قد لا تعمل بعض الروابط بسبب قيود TikTok.
    
    📊 لفحص حالة البوت: /status
    """
    bot.send_message(message.chat.id, welcome_text)

# أمر المساعدة /help
@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = """
    📋 قائمة الأوامر المتاحة:
    
    /start - بدء التشغيل
    /help - عرض المساعدة
    /status - فحص حالة البوت
    
    فقط أرسل رابط فيديو TikTok لتحميله بدون علامة مائية.
    """
    bot.send_message(message.chat.id, help_text)

# أمر فحص الحالة /status
@bot.message_handler(commands=['status'])
def check_status(message):
    try:
        bot.send_message(message.chat.id, "✅ البوت يعمل بشكل طبيعي! أرسل رابط فيديو TikTok لتحميله.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ هناك مشكلة في البوت: {str(e)}")

# معالجة روابط TikTok المختلفة
@bot.message_handler(regexp="(http|https)://(vm|www|vt)\.(tiktok|douyin)\.com/|tiktok\.com/.+/video/")
def handle_tiktok_link(message):
    try:
        # استخراج الرابط من الرسالة
        url_match = re.search(r'(https?://[^\s]+)', message.text)
        if not url_match:
            bot.send_message(message.chat.id, "❌ لم أتمكن العثور على رابط صحيح في رسالتك.")
            return
            
        url = url_match.group(1)
        logger.info(f"تم استقبال رابط: {url} من المستخدم: {message.from_user.id}")
        
        # إظهار رسالة الانتظار
        wait_msg = bot.send_message(message.chat.id, "⏳ جاري معالجة الرابط...")
        
        # استخراج معلومات الفيديو
        video_info = get_tiktok_video_info(url)
        
        if not video_info:
            bot.edit_message_text("❌ لم أتمكن من تحميل الفيديو. قد يكون الرابط غير صحيح أو هناك مشكلة في الخادم.", 
                                 message.chat.id, wait_msg.message_id)
            return
        
        # تحميل الفيديو
        bot.edit_message_text("⏳ جاري تحميل الفيديو بدون علامة مائية...", 
                             message.chat.id, wait_msg.message_id)
        
        video_url = video_info.get('play')
        if not video_url:
            bot.edit_message_text("❌ لم أتمكن من الحصول على رابط الفيديو.", 
                                 message.chat.id, wait_msg.message_id)
            return
        
        # تحميل الفيديو
        response = requests.get(video_url, stream=True, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }, timeout=30)
        
        if response.status_code != 200:
            bot.edit_message_text("❌ فشل في تحميل الفيديو. حاول مرة أخرى لاحقاً.", 
                                 message.chat.id, wait_msg.message_id)
            return
        
        # إرسال الفيديو مباشرة من الرابط بدون حفظ
        bot.edit_message_text("✅ تم تحميل الفيديو بنجاح! جاري الإرسال...", 
                             message.chat.id, wait_msg.message_id)
        
        caption = f"""
📝 {video_info.get('title', 'لا يوجد وصف')}

👤 بواسطة: {video_info.get('author', {}).get('nickname', 'مستخدم مجهول')}
❤️ الإعجابات: {video_info.get('digg_count', 0)}
🔁 المشاركات: {video_info.get('share_count', 0)}
💬 التعليقات: {video_info.get('comment_count', 0)}
▶️ المشاهدات: {video_info.get('play_count', 0)}
        """
        
        try:
            # إرسال الفيديو مباشرة من الرابط
            bot.send_video(message.chat.id, video_url, caption=caption, 
                          reply_to_message_id=message.message_id, timeout=100)
            
            logger.info(f"تم إرسال الفيديو بنجاح للمستخدم: {message.from_user.id}")
            
        except Exception as e:
            logger.error(f"خطأ في إرسال الفيديو: {e}")
            bot.edit_message_text("❌ فشل في إرسال الفيديو. قد يكون حجم الفيديو كبير جداً.", 
                                 message.chat.id, wait_msg.message_id)
        
        # حذف رسالة الانتظار
        try:
            bot.delete_message(message.chat.id, wait_msg.message_id)
        except:
            pass
        
    except Exception as e:
        logger.error(f"خطأ في معالجة فيديو تيك توك: {e}")
        bot.send_message(message.chat.id, "❌ حدث خطأ أثناء معالجة الفيديو. حاول مرة أخرى.")

# معالجة الرسائل الأخرى
@bot.message_handler(func=lambda message: True)
def handle_other_messages(message):
    if message.text.startswith('/'):
        bot.send_message(message.chat.id, "❌ أمر غير معروف. استخدم /start لمعرفة كيفية الاستخدام.")
    else:
        bot.send_message(message.chat.id, "📨 لإرسال فيديو TikTok، يرجى إرسال رابط الفيديو فقط.")

# وظيفة لإعادة التشغيل التلقائي في حالة الفشل
def start_bot():
    while True:
        try:
            logger.info("✅ بدء تشغيل بوت تحميل فيديوهات TikTok...")
            print("✅ بدء تشغيل بوت تحميل فيديوهات TikTok...")
            bot.polling(none_stop=True, interval=1, timeout=60)
        except Exception as e:
            logger.error(f"❌ انتهت عملية البوت بالخطأ: {e}")
            logger.info("🔄 إعادة تشغيل البوت خلال 10 ثوان...")
            time.sleep(10)

# تشغيل البوت
if __name__ == '__main__':
    start_bot()
