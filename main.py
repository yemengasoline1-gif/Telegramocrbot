import os
import sys
import logging
import asyncio
import re
import random
import string
from datetime import datetime
from io import BytesIO

# مكتبات Telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler
)

# مكتبات معالجة الصور
from PIL import Image, ImageEnhance
import pytesseract
import cv2
import numpy as np

# مكتبة Flask للإبقاء حياً
from flask import Flask, render_template_string
from threading import Thread

# ==================== إعدادات البوت ====================
TOKEN = os.environ.get("8306427606:AAFxuu9WuABegJETDrIS65MinArciurmOvg")

# إعداد التسجيل
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== خادم ويب للإبقاء حياً ====================
app = Flask(__name__)

@app.route('/')
def home():
    html = """
    <!DOCTYPE html>
    <html dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🤖 بوت استخراج بيانات الجوازات</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }

            body {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }

            .container {
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 800px;
                width: 100%;
                text-align: center;
            }

            .status-badge {
                display: inline-block;
                background: #10b981;
                color: white;
                padding: 8px 20px;
                border-radius: 50px;
                font-size: 18px;
                margin-bottom: 20px;
                animation: pulse 2s infinite;
            }

            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.05); }
                100% { transform: scale(1); }
            }

            h1 {
                color: #333;
                margin-bottom: 20px;
                font-size: 32px;
            }

            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }

            .feature-card {
                background: #f8fafc;
                padding: 20px;
                border-radius: 12px;
                border: 2px solid #e2e8f0;
                transition: all 0.3s ease;
            }

            .feature-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            }

            .icon {
                font-size: 40px;
                margin-bottom: 10px;
            }

            .stats {
                background: #f1f5f9;
                padding: 25px;
                border-radius: 15px;
                margin: 30px 0;
            }

            .bot-link {
                display: inline-block;
                background: #3b82f6;
                color: white;
                padding: 15px 30px;
                border-radius: 10px;
                text-decoration: none;
                font-size: 18px;
                margin-top: 20px;
                transition: all 0.3s ease;
            }

            .bot-link:hover {
                background: #2563eb;
                transform: scale(1.05);
            }

            .footer {
                margin-top: 30px;
                color: #64748b;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="status-badge">✅ البوت يعمل بنجاح</div>
            <h1>🤖 بوت استخراج بيانات الجوازات</h1>

            <div class="stats">
                <p>🕒 وقت التشغيل: <strong>مستمر</strong></p>
                <p>🚀 الحالة: <strong style="color: #10b981;">نشط</strong></p>
                <p>📊 المنصة: <strong>Render.com</strong></p>
            </div>

            <div class="features">
                <div class="feature-card">
                    <div class="icon">📸</div>
                    <h3>استخراج النصوص</h3>
                    <p>استخراج النصوص العربية والإنجليزية من الصور</p>
                </div>

                <div class="feature-card">
                    <div class="icon">📧</div>
                    <h3>إنشاء بريد إلكتروني</h3>
                    <p>إنشاء بريد إلكتروني تلقائي مقتبس من الاسم</p>
                </div>

                <div class="feature-card">
                    <div class="icon">🔐</div>
                    <h3>كلمات مرور آمنة</h3>
                    <p>توليد كلمات مرور قوية ومقتبسة من الاسم</p>
                </div>

                <div class="feature-card">
                    <div class="icon">⚡</div>
                    <h3>معالجة سريعة</h3>
                    <p>معالجة الصور خلال ثواني معدودة</p>
                </div>
            </div>

            <a href="https://t.me/your_bot_username" class="bot-link">
                💬 ابدأ المحادثة مع البوت
            </a>

            <div class="footer">
                <p>⏰ آخر تحديث: {{ time }}</p>
                <p>📞 للدعم: @your_username</p>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

@app.route('/health')
def health():
    return {"status": "healthy", "service": "telegram-bot", "timestamp": datetime.now().isoformat()}

@app.route('/ping')
def ping():
    return "pong"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# بدء Flask في thread منفصل
Thread(target=run_flask, daemon=True).start()

# ==================== دوال البوت ====================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر /start"""
    user = update.effective_user

    welcome_text = f"""
🎉 *مرحباً {user.first_name}!*

*🤖 بوت استخراج بيانات الجوازات والبطاقات*

*📋 *ماذا يمكنني فعل؟:*
1️⃣ استخراج النصوص العربية من الصور
2️⃣ استخراج النصوص الإنجليزية من الصور  
3️⃣ إنشاء بريد إلكتروني تلقائي
4️⃣ إنشاء كلمات مرور آمنة

*📸 *كيفية الاستخدام:*
1. أرسل صورة واضحة للجواز أو البطاقة
2. انتظر ثواني للمعالجة
3. احصل على النتائج كاملة

*⚡ *نصائح للحصول على أفضل نتيجة:*
• تأكد من وضوح الصورة
• إضاءة جيدة
• خلفية فاتحة
• صورة أفقية

*🔒 *خصوصيتك مهمة:*
• الصور تُحذف تلقائياً بعد المعالجة
• لا نخزن أي بيانات
• النتائج للاستخدام التعليمي فقط

*🚀 *لتبدأ، أرسل لي صورة الآن!*
"""

    keyboard = [
        [InlineKeyboardButton("📸 أرسل صورة", callback_data="send_photo")],
        [InlineKeyboardButton("❓ المساعدة", callback_data="help"),
         InlineKeyboardButton("🔒 الخصوصية", callback_data="privacy")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الصور المرسلة"""
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id

        # إرسال رسالة الانتظار
        processing_msg = await update.message.reply_text(
            "⏳ *جاري معالجة الصورة...*",
            parse_mode="Markdown"
        )

        # الحصول على الصورة
        photo_file = await update.message.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()

        # تحديث الرسالة
        await processing_msg.edit_text("🔄 *جاري تحسين جودة الصورة...*")

        # تحويل bytes إلى صورة
        nparr = np.frombuffer(photo_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # تحويل إلى تدرج الرمادي
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # تحسين التباين
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)

        # تحديث الرسالة
        await processing_msg.edit_text("🔍 *جاري قراءة النصوص...*")

        # استخراج النصوص
        arabic_text = pytesseract.image_to_string(enhanced, lang='ara')
        english_text = pytesseract.image_to_string(enhanced, lang='eng')

        # تنظيف النصوص
        arabic_text = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\s\d]', '', arabic_text)
        english_text = re.sub(r'[^a-zA-Z0-9\s\.\-]', '', english_text)

        # تحديث الرسالة
        await processing_msg.edit_text("👤 *جاري استخراج الاسم...*")

        # استخراج الاسم (مثال مبسط)
        name = "محمد أحمد"

        # تحديث الرسالة
        await processing_msg.edit_text("📧 *جاري إنشاء البريد الإلكتروني...*")

        # إنشاء بريد إلكتروني
        name_clean = re.sub(r'[^a-zA-Z]', '', name)
        if len(name_clean) < 2:
            name_clean = "user"

        email = f"{name_clean[:4].lower()}{random.randint(1000, 9999)}@gmail.com"

        # تحديث الرسالة
        await processing_msg.edit_text("🔑 *جاري إنشاء كلمات المرور...*")

        # إنشاء كلمات مرور
        suggested_password = f"{name_clean[:3].lower()}{random.randint(100, 999)}!"

        strong_password = ''.join(
            random.choices(string.ascii_letters + string.digits + "!@#$%", k=12)
        )

        # حذف رسالة الانتظار
        await processing_msg.delete()

        # إرسال النتائج
        results_text = f"""
✅ *تم استخراج البيانات بنجاح!*

*📍 *النص العربي:*