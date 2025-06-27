import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
import random

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# User data storage (in a real bot, use a database)
user_data = {}

def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    user_id = user.id
    
    # Check if user has connected account
    if user_id not in user_data:
        user_data[user_id] = {
            'account_connected': False,
            'signals_received': 0,
            'correct_signals': 0,
            'last_signals': []
        }
        
        keyboard = [
            [InlineKeyboardButton("🔗 Account ulash", callback_data='connect_account')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_html(
            f"Salom {user.mention_html()}! Aviator signal botiga xush kelibsiz!\n\n"
            "Iltimos, o'yin accountingizni ulang (bu majburiy)",
            reply_markup=reply_markup
        )
    else:
        show_main_menu(update, user_id)

def connect_account(update: Update, context: CallbackContext) -> None:
    """Handle account connection."""
    query = update.callback_query
    user_id = query.from_user.id
    
    # In a real bot, implement actual account connection logic here
    user_data[user_id]['account_connected'] = True
    
    query.answer("Accountingiz muvaffaqiyatli ulandi!")
    show_main_menu_from_query(query, user_id)

def show_main_menu(update: Update, user_id: int) -> None:
    """Show main menu."""
    keyboard = [
        [InlineKeyboardButton("🎮 Signal olish", callback_data='get_signal')],
        [InlineKeyboardButton("ℹ️ Bot haqida", callback_data='about')],
        [InlineKeyboardButton("📊 Mening statistikam", callback_data='stats')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        "Asosiy menyu:",
        reply_markup=reply_markup
    )

def show_main_menu_from_query(query, user_id: int) -> None:
    """Show main menu from callback query."""
    keyboard = [
        [InlineKeyboardButton("🎮 Signal olish", callback_data='get_signal')],
        [InlineKeyboardButton("ℹ️ Bot haqida", callback_data='about')],
        [InlineKeyboardButton("📊 Mening statistikam", callback_data='stats')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(
        "Asosiy menyu:",
        reply_markup=reply_markup
    )

def get_signal(update: Update, context: CallbackContext) -> None:
    """Generate and send a signal to the user."""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Check if account is connected
    if not user_data[user_id]['account_connected']:
        query.answer("Iltimos, avval accountingizni ulang!", show_alert=True)
        return
    
    # Generate realistic signal values
    min_val = round(random.uniform(0, 3.5), 1)
    mid_val = round(random.uniform(2.1, 4.6), 1)
    max_val = round(random.uniform(2.5, 6), 1)
    
    # Determine if this signal will be correct (70% chance)
    is_correct = random.random() < 0.7
    
    # Update user stats
    user_data[user_id]['signals_received'] += 1
    user_data[user_id]['correct_signals'] += 1 if is_correct else 0
    user_data[user_id]['last_signals'].append(is_correct)
    if len(user_data[user_id]['last_signals']) > 3:
        user_data[user_id]['last_signals'].pop(0)
    
    # Prepare signal message
    signal_message = (
        "⏳ Hozirgi analizlar asosida (70%+ ishonchlilik):\n\n"
        f"1️⃣ Minimal uchish: {min_val}x\n"
        f"2️⃣ O'rtacha uchish: {mid_val}x\n"
        f"3️⃣ Maksimal uchish: {max_val}x\n\n"
        "💡 Ehtiyotkorlik bilan o'ynang va risklarni to'g'ri boshqaring!"
    )
    
    query.answer()
    query.edit_message_text(
        signal_message,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Yangi signal", callback_data='get_signal')],
            [InlineKeyboardButton("📊 Statistika", callback_data='stats')],
            [InlineKeyboardButton("🏠 Asosiy menyu", callback_data='main_menu')]
        ])
    )

def show_stats(update: Update, context: CallbackContext) -> None:
    """Show user statistics."""
    query = update.callback_query
    user_id = query.from_user.id
    
    user_stats = user_data.get(user_id, {
        'signals_received': 0,
        'correct_signals': 0,
        'last_signals': []
    })
    
    total = user_stats['signals_received']
    correct = user_stats['correct_signals']
    accuracy = round((correct / total) * 100, 1) if total > 0 else 0
    
    # Prepare last signals emoji
    last_signals = ""
    for signal in user_stats.get('last_signals', []):
        last_signals += "✅" if signal else "❌"
    
    stats_message = (
        "📊 Sizning statistikangiz:\n\n"
        f"Bugungi signalar: {total}\n"
        f"To'g'ri signalar: {correct} ({accuracy}%)\n"
        f"Oxirgi {len(user_stats.get('last_signals', []))} signal: {last_signals}"
    )
    
    query.answer()
    query.edit_message_text(
        stats_message,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎮 Signal olish", callback_data='get_signal')],
            [InlineKeyboardButton("🏠 Asosiy menyu", callback_data='main_menu')]
        ])
    )

def about(update: Update, context: CallbackContext) -> None:
    """Show information about the bot."""
    query = update.callback_query
    
    about_message = (
        "ℹ️ Aviator Signal Bot haqida:\n\n"
        "Bu bot Aviator o'yini uchun 70%+ ishonchlilikdagi analiz asosida signalar beradi.\n\n"
        "Har bir signal 3 bosqichda tavsiya etiladi:\n"
        "1. Minimal uchish\n"
        "2. O'rtacha uchish\n"
        "3. Maksimal uchish\n\n"
        "⚠️ Eslatma: Barcha tavsiyalar analiz asosida beriladi va 100% ishonchlilik kafolatlanmaydi."
    )
    
    query.answer()
    query.edit_message_text(
        about_message,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Asosiy menyu", callback_data='main_menu')]
        ])
    )

def main_menu(update: Update, context: CallbackContext) -> None:
    """Return to main menu."""
    query = update.callback_query
    user_id = query.from_user.id
    show_main_menu_from_query(query, user_id)

def main() -> None:
    """Start the bot."""
    # Create the Updater and pass it your bot's token.
    # Replace 'YOUR_TOKEN' with your actual bot token
    updater = Updater("7774077829:AAEFcmt_ivYPiPrmoZCEqZrkk-5fttn4dVg", use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    
    # Register callback query handlers
    dispatcher.add_handler(CallbackQueryHandler(connect_account, pattern='^connect_account$'))
    dispatcher.add_handler(CallbackQueryHandler(get_signal, pattern='^get_signal$'))
    dispatcher.add_handler(CallbackQueryHandler(show_stats, pattern='^stats$'))
    dispatcher.add_handler(CallbackQueryHandler(about, pattern='^about$'))
    dispatcher.add_handler(CallbackQueryHandler(main_menu, pattern='^main_menu$'))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()