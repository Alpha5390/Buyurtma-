import logging
import random
from aiogram import Bot, Dispatcher, executor, types
from datetime import datetime, timedelta
import pytz
import asyncio

API_TOKEN = '8004408093:AAFXn45c4OH9cBcA81ga_FloeEy2sUyL2uM'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# ➡️ Foydalanuvchi ma'lumotlarini saqlash uchun dict
users = {}
last_signal_time = {}

# ➡️ O'zbekiston timezone
uzbekistan_tz = pytz.timezone('Asia/Tashkent')

# ➡️ Start komandasi
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🛡️ Hisobingizni ulash", url="https://betandres.com"))
    text = ("👋 Assalomu alaykum!\n\n"
            "Aviator 70%+ taxliliy signal botiga xush kelibsiz.\n\n"
            "🔑 Botdan foydalanish uchun avval Betandres hisobingizga kiring va parolingizni shu yerga yozing.\nMisol uchun :\nIsm:abdug'ani1234\nParol:12345678")
    await message.answer(text, reply_markup=keyboard)
    users[message.from_user.id] = {"registered": False}

# ➡️ Parol yuborganda
@dp.message_handler(lambda message: message.from_user.id in users and not users[message.from_user.id]["registered"])
async def get_password(message: types.Message):
    password = message.text
    if len(password) < 4:
        await message.answer("❗ Parol noto‘g‘ri ko‘rinyapti. Iltimos, to‘liq parolingizni kiriting.")
        return

    users[message.from_user.id]["registered"] = True
    users[message.from_user.id]["password"] = password

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🚀 Signal olish", callback_data="get_signal"))

    await message.answer("✅ Parolingiz qabul qilindi.\nEndi signal olishingiz mumkin.", reply_markup=keyboard)

# ➡️ Signal tugmasi bosilganda
@dp.callback_query_handler(lambda c: c.data == 'get_signal')
async def send_signal(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    # ➡️ Agar ro'yxatdan o'tmagan bo'lsa
    if user_id not in users or not users[user_id]["registered"]:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("🛡️ Hisobingizni ulash", url="https://betandres.com"))
        await bot.send_message(user_id, "❗ Avval hisobingizga kirib, parolingizni yuboring.", reply_markup=keyboard)
        return

    now_uz = datetime.now(uzbekistan_tz)

    # ➡️ Har bir signal olish uchun 2 daqiqa kutish
    if user_id in last_signal_time:
        diff = (now_uz - last_signal_time[user_id]).total_seconds()
        if diff < 120:
            wait_time = int(120 - diff)
            await bot.answer_callback_query(callback_query.id, text=f"❗ Yangi signal taxlil qilinyapti, {wait_time} sekund kuting.", show_alert=True)
            return

    last_signal_time[user_id] = now_uz

    await bot.answer_callback_query(callback_query.id)

    # 🔷 ⏳ Tahlil qilinyapti xabari
    analyzing_message = await bot.send_message(user_id, "⏳ Signal tahlil qilinyapti...\nIltimos, biroz kuting.")

    # 🔷 Kutish (3 sekund)
    await asyncio.sleep(3)

    # 🔢 Minimal, o‘rtacha, maksimal koeffitsientlarni generatsiya qilish
    min_k = round(random.uniform(0, 2.7), 2)
    mid_k = round(random.uniform(2.7, 3.5), 2)
    max_k = round(random.uniform(3.5, 7.0), 2)

    # ⏰ Vaqt oralig'i (2 daqiqa keyin boshlanadi, 3 daqiqa davom etadi)
    start_time = now_uz + timedelta(minutes=2)
    end_time = start_time + timedelta(minutes=3)
    time_range = f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')} (O'zbekiston vaqti)"

    text = (f"📊 <b>70%+ taxliliy Aviator signali</b>\n\n"
            f"🕒 Shu vaqt oralig'ida tiking (15 soniya farq qiladi): <b>{time_range}</b>\n\n"
            f"1️⃣ 70%+ taxlil: <b>{min_k}x</b>\n"
            f"2️⃣ 50%+ taxlil: <b>{mid_k}x</b>\n"
            f"3️⃣ 45%+ taxlil: <b>{max_k}x</b>\n\n"
            "✅ Tahlil qilingan koeffitsientlar.\n"
            "Bu vaqt oralig'ida tiking. Omad tilaymiz! 🍀")

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🚀 Yana signal", callback_data="get_signal"))

    # 🔷 Avvalgi 'Tahlil qilinyapti' xabarini o'chirish
    await bot.delete_message(user_id, analyzing_message.message_id)

    # 🔷 Signal yuborish
    await bot.send_message(user_id, text, parse_mode="HTML", reply_markup=keyboard)

# ➡️ Xatoliklar uchun umumiy handler
@dp.message_handler()
async def fallback(message: types.Message):
    user_id = message.from_user.id
    if user_id in users and not users[user_id]["registered"]:
        await message.answer("❗ Iltimos, Betandres hisobingiz parolini yuboring.")
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("🚀 Signal olish", callback_data="get_signal"))
        await message.answer("❗ Iltimos, menyudan foydalaning.", reply_markup=keyboard)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
