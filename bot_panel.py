import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Import fungsi & config dari main.py
try:
    from main import get_numbers, get_active_account, COUNTRIES_CONFIG
except ImportError:
    # Fallback dummy config jika main.py belum terhubung sempurna saat testing awal
    COUNTRIES_CONFIG = {
        "mali": {"name": "Mali", "flag": "🇲🇱", "rng": "mali_range"},
        "peru": {"name": "Peru", "flag": "🇵🇪", "rng": "peru_range"},
        "tajikistan": {"name": "Tajikistan", "flag": "🇹🇯", "rng": "tajik_range"},
        "congo": {"name": "DR Congo", "flag": "🇨🇩", "rng": "congo_range"}
    }
    def get_active_account(): return None
    def get_numbers(acc, rng): return ["+22371425382", "+22383637323", "+22390246755", "+22370560618", "+22376232450"]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Membaca token bot panel dari Environment Variable Railway
BOT_TOKEN = os.getenv("PANEL_BOT_TOKEN", "")

# 1. Start Command & Tombol Menu Utama (Bawah Chat)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["📞 Get Number"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    
    welcome_msg = (
        "<b>Verified! Welcome to OTP Service</b>\n\n"
        "Klik tombol <b>📞 Get Number</b> di bawah untuk mengambil nomor."
    )
    await update.message.reply_text(welcome_msg, parse_mode="HTML", reply_markup=markup)

# 2. Klik "📞 Get Number" -> Muncul Pilihan Negara
async def handle_get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    row = []
    for code, info in COUNTRIES_CONFIG.items():
        btn_text = f"{info['name']} {info.get('flag', '')}"
        row.append(InlineKeyboardButton(btn_text, callback_data=f"country_{code}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select a Country:", reply_markup=reply_markup)

# 3. Klik Negara -> Fetch 5 Nomor Auto & Tombol Copy All
async def handle_country_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    country_code = query.data.replace("country_", "")
    info = COUNTRIES_CONFIG.get(country_code, {})
    
    try:
        acc = get_active_account()
        raw_numbers = get_numbers(acc, info.get("rng", ""))
        top_5 = list(reversed(raw_numbers[-5:]))
    except Exception as e:
        await query.edit_message_text(f"Gagal mengambil nomor: {e}")
        return

    if not top_5:
        await query.edit_message_text("Stok nomor untuk negara ini sedang kosong.")
        return

    # Teks buat fitur Copy All
    all_numbers_text = "\n".join(top_5)
    
    msg_text = (
        f"<b>WhatsApp Number Selected Successfully!</b>\n\n"
        f"<b>Country:</b> {info.get('name', country_code)}\n"
        f"<b>Waiting For OTP...</b>\n\n"
    )
    for num in top_5:
        flag = info.get('flag', '📱')
        msg_text += f"{flag} <code>{num}</code>\n"

    keyboard = [
        [InlineKeyboardButton("📋 Copy All Numbers", copy_text={"text": all_numbers_text})],
        [InlineKeyboardButton("🔄 Change Country", callback_data="change_country")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(text=msg_text, parse_mode="HTML", reply_markup=reply_markup)

# Callback tombol Change Country
async def handle_change_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await handle_get_number(query, context)

def main():
    if not BOT_TOKEN:
        print("ERROR: PANEL_BOT_TOKEN belum diisi di Railway Environment Variables!")
        return
        
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Text(["📞 Get Number"]), handle_get_number))
    app.add_handler(CallbackQueryHandler(handle_country_selection, pattern="^country_"))
    app.add_handler(CallbackQueryHandler(handle_change_country, pattern="^change_country$"))

    print("Bot Panel is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
  
