import os
import re
import random
import string
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import pytesseract
from PIL import Image
import cv2
import numpy as np

# تأكد من وجود التوكن
TOKEN = os.environ.get("BOT_TOKEN")

def extract_text_from_image(image_bytes):
    """استخراج النصوص من الصورة"""
    try:
        # تحويل bytes إلى صورة
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # تحويل إلى تدرج الرمادي
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # تحسين الصورة
        processed = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # استخراج النص العربي
        arabic_text = pytesseract.image_to_string(
            processed, 
            lang='ara',
            config='--psm 6 --oem 3'
        )
        
        # استخراج النص الإنجليزي
        english_text = pytesseract.image_to_string(
            processed,
            lang='eng',
            config='--psm 6 --oem 3'
        )
        
        return arabic_text.strip(), english_text.strip()
        
    except Exception as e:
        return f"خطأ في استخراج النص: {str(e)}", ""

def extract_name(arabic_text, english_text):
    """استخراج الاسم من النصوص"""
    try:
        # البحث في النص العربي
        arabic_patterns = [
            r'الاسم[:\s]+([^\n]+)',
            r'اسم[:\s]+([^\n]+)',
            r'حامل[:\s]+([^\n]+)',
            r'المسمى[:\s]+([^\n]+)'
        ]
        
        for pattern in arabic_patterns:
            match = re.search(pattern, arabic_text)
            if match:
                return match.group(1).strip()
        
        # البحث في النص الإنجليزي
        english_patterns = [
            r'Name[:\s]+([^\n]+)',
            r'Full Name[:\s]+([^\n]+)',
            r'Name of[:\s]+([^\n]+)',
            r'Given Name[:\s]+([^\n]+)'
        ]
        
        for pattern in english_patterns:
            match = re.search(pattern, english_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "غير معروف"
    except:
        return "غير معروف"

def generate_gmail(name):
    """إنشاء بريد Gmail"""
    try:
        # تنظيف الاسم
        clean_name = re.sub(r'[^a-zA-Z]', '', name).lower()
        if len(clean_name) < 3:
            clean_name = "user"
        
        # إنشاء اسم المستخدم
        username = f"{clean_name[:4]}{random.randint(1000, 9999)}"
        
        return f"{username}@gmail.com"
    except:
        return "user1234@gmail.com"

def generate_passwords(name):
    """إنشاء كلمات مرور"""
    try:
        clean_name = re.sub(r'[^a-zA-Z]', '', name).lower()
        if len(clean_name) < 3:
            clean_name = "user"
        
        # كلمة مرور مقتبسة من الاسم
        simple_pass = f"{clean_name[:3]}{random.randint(100, 999)}!"
        
        # كلمة مرور قوية
        strong_chars = string.ascii_letters + string.digits + "!@#$%^&*"
        strong_pass = ''.join(random.choices(strong_chars, k=12))
        
        return simple_pass, strong_pass
    except:
        return "Pass123!", "StrongPass123!@"

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الصور المرسلة"""
    try:
        # إعلام بالبدء
        message = await update.message.reply_text("📥 جاري معالجة الصورة...")
        
        # تحميل الصورة
        photo_file = await update.message.photo[-1].get_file()
        image_bytes = await photo_file.download_as_bytearray()
        
        # استخراج النصوص
        arabic_text, english_text = extract_text_from_image(image_bytes)
        
        # استخراج الاسم
        name = extract_name(arabic_text, english_text)
        
        # إنشاء بريد Gmail
        gmail_address = generate_gmail(name)
        
        # إنشاء كلمات المرور
        simple_password, strong_password = generate_passwords(name)
        
        # ✨ **هنا الجزء المهم - بناء الرسالة الصحيحة:**
        
        # تنظيف النصوص للعرض
        arabic_display = arabic_text[:300] if arabic_text and len(arabic_text) > 10 else "❌ لم يتم العثور على نص عربي واضح"
        english_display = english_text[:300] if english_text and len(english_text) > 10 else "❌ لم يتم العثور على نص إنجليزي واضح"
        
        # بناء الرسالة بشكل صحيح
        result_message = f"""
✅ *تم استخراج البيانات بنجاح!*

📋 *النص العربي:*
{arabic_display}

📋 *النص الإنجليزي:*
{english_display}

👤 *الاسم المستخرج:* {name}

📧 *بريد Gmail المقترح:*
`{gmail_address}`

🔑 *كلمات المرور:*
• مقتبس من الاسم: `{simple_password}`
• كلمة مرور قوية: `{strong_password}`

🔗 *لإنشاء الحساب على Gmail:*
https://accounts.google.com/signup

💡 *نصائح أمنية:*
• غير كلمة المرور فور إنشاء الحساب
• استخدم مدير كلمات المرور
• فعّل المصادقة الثنائية

⚠️ *تنبيه:*
هذه البيانات للاستخدام التعليمي فقط.
"""
        
        # إرسال النتائج
        await message.edit_text(result_message, parse_mode='Markdown')
        
        # إضافة أزرار للمساعدة
        keyboard = [
            [
                InlineKeyboardButton("📧 إنشاء Gmail", url="https://accounts.google.com/signup"),
                InlineKeyboardButton("🔄 صورة أخرى", callback_data="another")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "👇 يمكنك استخدام الأزرار أدناه:",
            reply_markup=reply_markup
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /start"""
    welcome_text = """
🚀 *مرحباً بك في بوت استخراج بيانات الجوازات!*

*🤖 ما يمكنني فعله:*
• استخراج النصوص العربية والإنجليزية من الصور
• إنشاء بريد Gmail مقترح
• إنشاء كلمات مرور آمنة

*📸 *كيفية الاستخدام:*
1. أرسل صورة جواز السفر أو البطاقة
2. انتظر ثواني للمعالجة
3. احصل على النتائج كاملة

*🔒 *ملاحظات:*
• الصور تحذف بعد المعالجة
• البيانات للاستخدام التعليمي فقط

📱 *لتبدأ، أرسل صورة الآن!*
"""
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء"""
    print(f"حدث خطأ: {context.error}")
    try:
        await update.message.reply_text("❌ حدث خطأ، يرجى المحاولة مرة أخرى.")
    except:
        pass

def main():
    """الدالة الرئيسية"""
    if not TOKEN:
        print("❌ BOT_TOKEN غير موجود!")
        print("📝 أضفه في Environment Variables في Render")
        return
    
    app = Application.builder().token(TOKEN).build()
    
    # إضافة ال handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # إضافة معالج الأخطاء
    app.add_error_handler(error_handler)
    
    print("🤖 البوت يعمل...")
    app.run_polling()

if __name__ == "__main__":
    main()
