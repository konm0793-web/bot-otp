import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Import fungsi & config ASLI dari main.py
import main

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

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

# 2. Klik "📞 Get Number" -> Ambil dari COUNTRIES asli di main.py (Termasuk Zimbabwe, Mali, Peru, dll)
async def handle_get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    row = []
    
    # Ambil COUNTRIES dari main.py
    countries = getattr(main, 'COUNTRIES', {})
    
    for code, info in countries.items():
        name = info.get('name', code.capitalize())
        flag = info.get('flag', '🌐')
        btn_text = f"{name} {flag}"
        row.append(InlineKeyboardButton(btn_text, callback_data=f"country_{code}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
            
    if row:
        keyboard.append(row)
        
    if not keyboard:
        await update.message.reply_text("❌ Tidak ada negara/range aktif di main.py.")
        return
        
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select a Country:", reply_markup=reply_markup)

# 3. Handle Klik Pilih Negara
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("country_"):
        country_code = query.data.replace("country_", "")
        countries = getattr(main, 'COUNTRIES', {})
        country_info = countries.get(country_code, {})
        
        c_name = country_info.get("name", country_code.capitalize())
        await query.edit_message_text(f"⏳ Sedang mengambil nomor <b>{c_name}</b> dari IVAS...", parse_mode="HTML")

        accounts = getattr(main, 'accounts', [])
        acc = accounts[0] if accounts else None

        if not acc:
            await query.edit_message_text("❌ Error: Akun IVAS belum terhubung / session mati.")
            return

        rng = country_info.get("rng", f"{country_code}_range")
        numbers = main.get_numbers(acc, rng)

        if not numbers:
            text = f"❌ Gagal/Stok Habis untuk <b>{c_name}</b>. Coba klik lagi!"
        else:
            num_list = "\n".join([f"➕{num}" for num in numbers])
            text = (
                f"<b>WhatsApp Number Selected Successfully!</b>\n\n"
                f"<b>Country: {c_name}</b>\n"
                f"Waiting For OTP...\n\n"
                f"{num_list}"
            )

        keyboard = [
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
    
