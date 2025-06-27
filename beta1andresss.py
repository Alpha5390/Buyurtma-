import requests
import time
import numpy as np
from bs4 import BeautifulSoup
from sklearn.ensemble import RandomForestRegressor
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes,
    CallbackQueryHandler, filters
)
from datetime import datetime
import logging
import asyncio

# Logging sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================== BETANDREAS PARSER ==================
class BetAndreasParser:
    def __init__(self):
        self.base_url = "https://betandreas.com"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36"
        })
    
    def get_aviator_data(self):
        try:
            response = self.session.get(f"{self.base_url}/aviator", timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Sayt strukturasiga qarab bu qismni tekshiring
            coefficient = float(soup.find('div', class_='coefficient').text)
            round_id = soup.find('span', class_='round-id').text
            
            return {
                "status": "success",
                "coefficient": coefficient,
                "round_id": round_id,
                "time": datetime.now().strftime("%H:%M:%S")
            }
        except Exception as e:
            logger.error(f"BetAndreas parsing error: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

# ================== TAXLILCHI ==================
class AviatorAnalyzer:
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100)
        self.history = []
        self.stats = {
            "total_predictions": 0,
            "correct_predictions": 0,
            "accuracy": 0.0,
            "last_10_predictions": []
        }
    
    def add_to_history(self, coefficient: float):
        self.history.append(coefficient)
        if len(self.history) > 100:
            self.history.pop(0)
    
    def analyze_next_round(self) -> dict:
        if len(self.history) < 10:
            return {
                "status": "error",
                "message": "Yetarli ma'lumot yo'q"
            }
        
        X = np.array(range(len(self.history))).reshape(-1, 1)
        y = np.array(self.history)
        self.model.fit(X, y)
        
        next_x = len(self.history)
        predictions = [estimator.predict([[next_x]])[0] for estimator in self.model.estimators_]
        
        return {
            "minimal": max(1.1, np.percentile(predictions, 25)),
            "medium": max(1.3, np.percentile(predictions, 50)),
            "maximal": max(1.5, np.percentile(predictions, 75)),
            "confidence": min(99, int(70 + 30 * (1 - np.std(predictions)/0.3))),
            "time": datetime.now().strftime("%H:%M:%S"),
            "status": "success"
        }
    
    def update_stats(self, predicted: float, actual: float):
        is_correct = abs(predicted - actual) < 0.2
        self.stats["total_predictions"] += 1
        if is_correct:
            self.stats["correct_predictions"] += 1
        self.stats["accuracy"] = (
            self.stats["correct_predictions"] / self.stats["total_predictions"]
        ) * 100 if self.stats["total_predictions"] > 0 else 0
        
        self.stats["last_10_predictions"].append(is_correct)
        if len(self.stats["last_10_predictions"]) > 10:
            self.stats["last_10_predictions"].pop(0)

# ================== ASOSIY BOT ==================
class BetAndreasAviatorBot:
    def __init__(self, token: str):
        self.bot = Bot(token=token)
        self.parser = BetAndreasParser()
        self.analyzer = AviatorAnalyzer()
        self.active_monitoring = {}
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("📡 Signallar", callback_data='signal_menu')],
            [InlineKeyboardButton("📊 Statistika", callback_data='stats')],
            [InlineKeyboardButton("ℹ️ Yordam", callback_data='help')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎮 BetAndreas Aviator Signal Botiga Xush Kelibsiz!\n\n"
            "Quyidagi menyudan kerakli bo'limni tanlang:",
            reply_markup=reply_markup
        )
    
    async def show_signal_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("🚀 Hozirgi Signal", callback_data='get_signal')],
            [InlineKeyboardButton("🔍 Monitoringni Boshlash", callback_data='start_monitoring')],
            [InlineKeyboardButton("🛑 Monitoringni To'xtatish", callback_data='stop_monitoring')],
            [InlineKeyboardButton("🔙 Orqaga", callback_data='main_menu')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query = update.callback_query
        await query.edit_message_text(
            "📡 Signal Menyusi - Quyidagilardan birini tanlang:",
            reply_markup=reply_markup
        )
    
    async def get_signal(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        game_data = self.parser.get_aviator_data()
        if game_data["status"] != "success":
            await query.edit_message_text("❌ Aviator ma'lumotlarini olishda xato! Keyinroq urinib ko'ring.")
            return
        
        self.analyzer.add_to_history(game_data["coefficient"])
        
        analysis = self.analyzer.analyze_next_round()
        if analysis["status"] != "success":
            await query.edit_message_text("❌ Hozircha yetarli ma'lumot yo'q. Iltimos, keyinroq urinib ko'ring.")
            return
        
        message = (
            f"🕒 Vaqt: {analysis['time']}\n"
            f"🔢 Raund ID: {game_data['round_id']}\n"
            f"📈 Hozirgi koeffitsient: {game_data['coefficient']:.2f}x\n\n"
            f"📊 Tahlil Natijalari (Ishonchlilik: {analysis['confidence']}%):\n"
            f"1️⃣ Minimal Uchish: {analysis['minimal']:.2f}x\n"
            f"2️⃣ O'rtacha Uchish: {analysis['medium']:.2f}x\n"
            f"3️⃣ Maksimal Uchish: {analysis['maximal']:.2f}x\n\n"
            f"📊 Bot Aniqlik Darajasi: {self.analyzer.stats['accuracy']:.1f}%\n"
            f"⚠️ Diqqat: Bu faqat bashorat, kafolat emas!"
        )
        
        await query.edit_message_text(message)
        self.analyzer.update_stats(analysis['medium'], game_data['coefficient'])
    
    async def start_monitoring(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        
        if user_id in self.active_monitoring:
            await query.edit_message_text("❌ Monitoring allaqachon boshlandi!")
            return
        
        self.active_monitoring[user_id] = True
        await query.edit_message_text("🔍 Monitoring boshlandi... Yangi signallar avtomatik yuboriladi.")
        
        asyncio.create_task(self._monitor_user(user_id))
    
    async def _monitor_user(self, user_id: int):
        while self.active_monitoring.get(user_id, False):
            game_data = self.parser.get_aviator_data()
            
            if game_data["status"] == "success":
                self.analyzer.add_to_history(game_data["coefficient"])
                analysis = self.analyzer.analyze_next_round()
                
                if analysis["status"] == "success" and analysis['confidence'] >= 70:
                    message = (
                        f"🚨 YANGI SIGNAL ({analysis['time']})\n\n"
                        f"🔢 Raund ID: {game_data['round_id']}\n"
                        f"📈 Hozirgi koeffitsient: {game_data['coefficient']:.2f}x\n\n"
                        f"📊 Tahlil (Ishonchlilik: {analysis['confidence']}%):\n"
                        f"1️⃣ Minimal: {analysis['minimal']:.2f}x\n"
                        f"2️⃣ O'rtacha: {analysis['medium']:.2f}x\n"
                        f"3️⃣ Maksimal: {analysis['maximal']:.2f}x\n\n"
                        f"📊 Bot Aniqlik Darajasi: {self.analyzer.stats['accuracy']:.1f}%\n"
                        f"⏳ Keyingi tekshiruv: 30 soniyadan keyin"
                    )
                    
                    await self.bot.send_message(chat_id=user_id, text=message)
                    self.analyzer.update_stats(analysis['medium'], game_data['coefficient'])
            
            await asyncio.sleep(30)
    
    async def stop_monitoring(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        
        if user_id in self.active_monitoring:
            self.active_monitoring[user_id] = False
            await query.edit_message_text("✅ Monitoring to'xtatildi.")
        else:
            await query.edit_message_text("ℹ️ Monitoring allaqachon to'xtatilgan.")
    
    async def show_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        stats = self.analyzer.stats
        message = (
            f"📊 Bot Statistikasi:\n\n"
            f"🔢 Jami Bashoratlar: {stats['total_predictions']}\n"
            f"✅ To'g'ri Bashoratlar: {stats['correct_predictions']}\n"
            f"📈 Aniqlik Darajasi: {stats['accuracy']:.1f}%\n\n"
            f"⚡ So'ngi 10 bashoratdan {sum(stats['last_10_predictions'])} tasi to'g'ri"
        )
        
        await query.edit_message_text(message)
    
    async def show_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        message = (
            "ℹ️ BetAndreas Aviator Signal Boti Yordami\n\n"
            "🔹 Bot BetAndreas saytidagi Aviator o'yinini tahlil qiladi\n"
            "🔹 Signallar 3 turda beriladi: Minimal, O'rtacha va Maksimal\n"
            "🔹 Har bir signal ishonchlilik foizi bilan birga keladi\n"
            "🔹 Monitoring rejimida yangi signallar avtomatik yuboriladi\n\n"
            "⚠️ Eslatma: Bu faqat tahlil vositasi, kafolat bermaydi!"
        )
        
        await query.edit_message_text(message)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        data = query.data
        
        handlers = {
            'main_menu': self.start,
            'signal_menu': self.show_signal_menu,
            'get_signal': self.get_signal,
            'start_monitoring': self.start_monitoring,
            'stop_monitoring': self.stop_monitoring,
            'stats': self.show_stats,
            'help': self.show_help
        }
        
        if data in handlers:
            await handlers[data](update, context)
    
    def run(self):
        application = ApplicationBuilder().token(BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        application.run_polling()

# ========== BOT TOKEN ==========
BOT_TOKEN = "7774077829:AAEFcmt_ivYPiPrmoZCEqZrkk-5fttn4dVg"

if __name__ == "__main__":
    bot = BetAndreasAviatorBot(BOT_TOKEN)
    bot.run()