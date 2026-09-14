import os
import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

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

# 2. Tombol Get Number
async def handle_get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # 1. Coba ambil dari fungsi/variabel dinamis IVAS yang ada di main.py
    available_ranges = {}
    
    if hasattr(main, 'get_available_ranges'):
        # Jika main.py punya fungsi pembaca range aktif dari IVAS
        available_ranges = main.get_available_ranges()
    elif hasattr(main, 'COUNTRIES'):
        available_ranges = main.COUNTRIES
    elif hasattr(main, 'RANGES'):
        available_ranges = main.RANGES
    
    keyboard = []
    row = []
    
    # 2. Susun tombol berdasarkan data dinamis IVAS
    if isinstance(available_ranges, dict):
        for key, info in available_ranges.items():
            name = info.get('name', str(key).upper()) if isinstance(info, dict) else str(info).upper()
            flag = info.get('flag', '🌐') if isinstance(info, dict) else '🌐'
            btn_text = f"{name} {flag}"
            row.append(InlineKeyboardButton(btn_text, callback_data=f"rng_{key}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
    elif isinstance(available_ranges, (list, tuple)):
        for item in available_ranges:
            btn_text = f"{str(item).upper()} 🌐"
            row.append(InlineKeyboardButton(btn_text, callback_data=f"rng_{item}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []

    if row:
        keyboard.append(row)

    # 3. Kalau belum ada range aktif di IVAS saat itu
    if not keyboard:
        await update.message.reply_text("❌ Tidak ada range/negara yang sedang aktif/high di IVAS saat ini.")
        return

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select a Country / Range:", reply_markup=reply_markup)
    

# 3. Handle Klik Tombol Negara
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("rng_"):
        range_key = query.data.replace("rng_", "")
        available_ranges = getattr(main, 'COUNTRIES', {})
        info = available_ranges.get(range_key, {"name": range_key.upper(), "rng": range_key})

        await query.edit_message_text(f"⏳ Sedang mengambil nomor <b>{info['name']}</b>...", parse_mode="HTML")

        acc = None
        if hasattr(main, 'get_active_account'):
            acc = main.get_active_account()
        elif hasattr(main, 'accounts') and main.accounts:
            acc = main.accounts[0]

        if not acc:
            await query.edit_message_text("❌ Session IVAS belum aktif / mati.")
            return

        rng_param = info.get("rng", range_key)

        try:
            numbers = await asyncio.to_thread(main.get_numbers, acc, rng_param)
        except Exception as e:
            numbers = []

        if not numbers:
            text = f"❌ Stok Habis / Gagal mengambil nomor <b>{info['name']}</b>."
        else:
            num_list = "\n".join([f"➕{num}" for num in numbers])
            text = (
                f"<b>WhatsApp Number Selected Successfully!</b>\n\n"
                f"<b>Country/Range: {info['name']}</b>\n"
                f"Waiting For OTP...\n\n"
                f"{num_list}"
            )

        keyboard = [[InlineKeyboardButton("🔄 Change Country", callback_data="change_country")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)

    elif query.data == "change_country":
        await handle_get_number(query, context)

def start_bot_panel():
    if not BOT_TOKEN:
        print("PANEL_BOT_TOKEN belum diset di Environment Variable!")
        return
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^📞 Get Number$"), handle_get_number))
    app.add_handler(CallbackQueryHandler(button_callback))
    print("Bot Panel is running...")
    
    # Tambahkan stop_signals=None supaya bisa jalan di background thread!
    app.run_polling(stop_signals=None)
    
