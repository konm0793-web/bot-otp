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
    reply_keyboard = [["📞 Get Number"], ["Ambil Nomor"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)
    welcome_msg = (
        "<b> Verified! Welcome to OTP Service</b>\n\n"
        "Ketik <b>Ambil Nomor</b> atau klik tombol di bawah untuk mulai."
    )
    await update.message.reply_text(welcome_msg, parse_mode="HTML", reply_markup=markup)

# 2. Menu Pilih Negara / Service
async def handle_get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇿🇼 Zimbabwe (Auto All Prefix)", callback_data="get_zw_auto")],
        [InlineKeyboardButton("🔄 Refresh Session", callback_data="refresh_session")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = update.message if update.message else update.callback_query.message
    await msg.reply_text("<b>Pilih Layanan / Negara:</b>", parse_mode="HTML", reply_markup=reply_markup)

# 3. Callback Handler Utama (Narik Nomor & Tampilan UI Tombol)
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_zw_auto":
        await query.edit_message_text("⏳ <b>Sedang menarik semua prefix & nomor dari IVAS...</b>", parse_mode="HTML")

        # Ambil akun session IVAS yang aktif dari main.py
        acc = None
        if hasattr(main, 'get_active_account'):
            acc = main.get_active_account()
        elif hasattr(main, 'accounts') and main.accounts:
            acc = main.accounts[0]

        if not acc:
            await query.edit_message_text("❌ <b>Session IVAS mati / belum terhubung.</b>", parse_mode="HTML")
            return

        # Panggil fungsi auto-fetch milik main.py
        try:
            numbers = await asyncio.to_thread(main.get_all_numbers_auto, acc)
        except Exception as e:
            logging.error(f"Error fetching numbers: {e}")
            numbers = []

        if not numbers:
            keyboard = [[InlineKeyboardButton("🔙 Kembali ke Menu", callback_data="change_country")]]
            await query.edit_message_text("❌ <b>Stok Habis / Gagal mengambil nomor dari IVAS.</b>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
            return

        # Batasi tampilan max 20 nomor per UI pesan biar gak melebihi limit tombol Telegram
        display_numbers = numbers[:20]

        # Susun tombol-tombol nomor (mirip UI screenshot lu)
        keyboard = []
        for num in display_numbers:
            formatted_num = f"+{num}" if not str(num).startswith("+") else str(num)
            keyboard.append([InlineKeyboardButton(f"📋 {formatted_num}", callback_data=f"copy_{num}")])

        # Navigasi tombol bawah
        keyboard.append([
            InlineKeyboardButton("🔄 Ambil Ulang", callback_data="get_zw_auto"),
            InlineKeyboardButton("🌐 Ganti Negara", callback_data="change_country")
        ])
        keyboard.append([InlineKeyboardButton("🔍 Auto Checker On", callback_data="checker_toggle")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        header_text = (
            f"✅ <b>WhatsApp 🇿🇼 Zimbabwe</b>\n"
            f"<code>{len(numbers)} nomor berhasil diambil secara otomatis.</code>"
        )
        await query.edit_message_text(header_text, parse_mode="HTML", reply_markup=reply_markup)

    elif query.data.startswith("copy_"):
        num_copied = query.data.replace("copy_", "")
        await query.answer(f"Nomor disalin: +{num_copied}", show_alert=True)

    elif query.data == "change_country":
        await handle_get_number(update, context)

# 4. Runner Bot Panel
def start_bot_panel():
    if not BOT_TOKEN:
        print("PANEL_BOT_TOKEN belum diset di environment variable!")
        return
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("(?i)^(📞 Get Number|Ambil Nomor)$"), handle_get_number))
    app.add_handler(CallbackQueryHandler(button_callback))
    print("Bot Panel is running...")
    app.run_polling(stop_signals=None)

if __name__ == "__main__":
    start_bot_panel()
    
