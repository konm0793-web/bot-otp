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
    available_ranges = getattr(main, 'COUNTRIES', {})
    keyboard = []
    row = []
    
    for key, info in available_ranges.items():
        c_name = info.get('name', key.upper())
        flag = info.get('flag', '🌐')
        btn_text = f"{c_name} {flag}"
        row.append(InlineKeyboardButton(btn_text, callback_data=f"rng_{key}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
        
    if not keyboard:
        await update.message.reply_text("❌ Tidak ada range/negara aktif di main.py.")
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
    app.run_polling()
