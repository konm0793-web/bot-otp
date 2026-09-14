import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Import fungsi & config ASLI dari main.py
import main

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Token bot panel
BOT_TOKEN = os.getenv("PANEL_BOT_TOKEN", "")

# 1. Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_keyboard = [["📞 Get Number"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    welcome_msg = (
        "<b>Verified! Welcome to OTP Service</b>\n\n"
        "Klik tombol <b>📞 Get Number</b> di bawah untuk mengambil nomor."
    )
    await update.message.reply_text(welcome_msg, parse_mode="HTML", reply_markup=markup)

# 2. Klik "📞 Get Number" -> AUTO DETECT SEMUA RANGE/NEGARA YANG AKTIF DI IVAS
async def handle_get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    row = []
    
    # Ambil list akun aktif dari main.py
    accounts = getattr(main, 'accounts', [])
    acc = accounts[0] if accounts else None
    
    # Kumpulkan range yang ada di main.py / IVAS
    countries_config = getattr(main, 'COUNTRIES_CONFIG', {})
    
    # Jika tidak ada config manual, auto-detect dari key yang tersedia
    for key, info in countries_config.items():
        country_name = info.get('name', key.capitalize())
        flag = info.get('flag', '🌐')
        btn_text = f"{country_name} {flag}"
        
        # Simpan callback data pakai key range
        row.append(InlineKeyboardButton(btn_text, callback_data=f"rng_{key}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
            
    if row:
        keyboard.append(row)
        
    if not keyboard:
        await update.message.reply_text("❌ Tidak ada range/negara aktif yang terdeteksi di akun IVAS.")
        return
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select a Country / Range:", reply_markup=reply_markup)

# 3. Handle Klik Negara -> Tembak Scraper IVAS Asli
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("rng_"):
        range_key = query.data.replace("rng_", "")
        countries_config = getattr(main, 'COUNTRIES_CONFIG', {})
        info = countries_config.get(range_key, {"name": range_key.capitalize(), "rng": range_key})

        await query.edit_message_text(f"⏳ Sedang mengambil nomor <b>{info['name']}</b> dari IVAS...", parse_mode="HTML")

        # Ambil akun session IVAS aktif
        accounts = getattr(main, 'accounts', [])
        acc = accounts[0] if accounts else None

        if not acc:
            await query.edit_message_text("❌ Error: Akun IVAS belum terhubung/session mati.")
            return

        # Ambil nomor langsung pakai fungsi get_numbers asli main.py
        target_rng = info.get("rng", range_key)
        numbers = main.get_numbers(acc, target_rng)

        if not numbers:
            text = f"❌ Gagal/Stok Habis untuk <b>{info['name']}</b>. Coba klik lagi atau ganti range!"
        else:
            num_list = "\n".join([f"➕{num}" for num in numbers])
            text = (
                f"<b>WhatsApp Number Selected Successfully!</b>\n\n"
                f"<b>Country/Range: {info['name']}</b>\n"
                f"Waiting For OTP...\n\n"
                f"{num_list}"
            )

        keyboard = [
            [InlineKeyboardButton("📋 Copy All Numbers", callback_data="copy_all")],
            [InlineKeyboardButton("🔄 Change Country", callback_data="change_country")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)

    elif query.data == "change_country":
        await handle_get_number(query, context)

def main_panel():
    if not BOT_TOKEN:
        print("PANEL_BOT_TOKEN belum diset di Environment Variable!")
        return
        
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^📞 Get Number$"), handle_get_number))
    app.add_handler(CallbackQueryHandler(button_callback))
    
    print("Bot Panel is running...")
    app.run_polling()

if __name__ == "__main__":
    main_panel()
    
