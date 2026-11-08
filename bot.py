import os
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ==================== SETTINGS ====================
BOT_TOKEN = "9076447381:AAFQjWAVfpcuno18AJF5jXwY2feGl99V8w0"
ADMIN_ID = 8892893806

CBE_ACCOUNT = "1000303969547"
CBE_NAME = "Mesfin"

TELEBIRR_NUMBER = "0931335199"
TELEBIRR_NAME = "Mesfin"

# Courses and their corresponding GitHub PDF filenames
COURSES = {
    "basic": ("Basic Computer Skills Full Course", 350, "BASIC COMPUTER SKIILLS FULL COURSE.pdf"),
    "video": ("Video Editing Full Course", 450, "CAPCUT FULL COARSE.pdf"),
    "mobile": ("Mobile Software Full Course", 350, "MOBILE SOFTWARE FULL COURSE.pdf"),
    "graphics": ("Graphics Design Full Course", 500, "GRAPHICS DESIGN FULL COURSE.pdf"),
}

logging.basicConfig(level=logging.INFO)


# ==================== DUMMY HTTP SERVER FOR RENDER ====================
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Mesola Technology Bot is alive and running!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()


# ==================== 1. START COMMAND ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Basic Computer Skills - 350 Birr", callback_data="basic")],
        [InlineKeyboardButton("Video Editing - 450 Birr", callback_data="video")],
        [InlineKeyboardButton("Mobile Software - 350 Birr", callback_data="mobile")],
        [InlineKeyboardButton("Graphics Design - 500 Birr", callback_data="graphics")],
    ]

    await update.message.reply_text(
        "Welcome to Mesola Technology! 📚\n\n"
        "Choose the book you want to purchase:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==================== 2. COURSE SELECTION ====================
async def select_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    course = query.data
    context.user_data["course"] = course

    name, price, _ = COURSES[course]

    keyboard = [
        [InlineKeyboardButton("CBE", callback_data="cbe")],
        [InlineKeyboardButton("Telebirr", callback_data="tele")],
    ]

    await query.message.reply_text(
        f"📚 {name}\n"
        f"💰 Price: {price} Birr\n\n"
        "Choose your payment method:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==================== 3. PAYMENT INFORMATION ====================
async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if "course" not in context.user_data:
        await query.message.reply_text("Please select a book first. Use /start")
        return

    if query.data == "cbe":
        info = (
            f"🏦 CBE PAYMENT\n\n"
            f"Account Name: {CBE_NAME}\n"
            f"Account Number: {CBE_ACCOUNT}"
        )
    else:
        info = (
            f"📱 TELEBIRR PAYMENT\n\n"
            f"Account Name: {TELEBIRR_NAME}\n"
            f"Phone Number: {TELEBIRR_NUMBER}"
        )

    await query.message.reply_text(
        info + "\n\n"
        "After payment, send your payment screenshot here."
    )


# ==================== 4. RECEIVE RECEIPT & NOTIFY ADMIN ====================
async def receive_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    course = context.user_data.get("course")

    if not course:
        await update.message.reply_text("Please select a book first. Use /start")
        return

    user = update.effective_user
    name, price, _ = COURSES[course]

    keyboard = [
        [InlineKeyboardButton("✅ Approve & Send Book", callback_data=f"approve_{user.id}_{course}")]
    ]

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "🔔 NEW PAYMENT SUBMISSION\n\n"
            f"Customer: {user.full_name}\n"
            f"Username: @{user.username or 'N/A'}\n"
            f"Telegram ID: {user.id}\n"
            f"Book: {name}\n"
            f"Price: {price} Birr\n\n"
            "Please verify the payment."
        )
    )

    await context.bot.copy_message(
        chat_id=ADMIN_ID,
        from_chat_id=update.effective_chat.id,
        message_id=update.message.message_id,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text(
        "✅ Your payment screenshot has been sent to Admin.\n\n"
        "Please wait while your payment is verified.\n"
        "Admin will send your book after confirmation."
    )


# ==================== 5. ADMIN APPROVAL & SENDING BOOK ====================
async def admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        await query.answer("You are not authorized!", show_alert=True)
        return

    data_parts = query.data.split("_")
    customer_id = int(data_parts[1])
    course_key = data_parts[2]

    name, _, book_filename = COURSES[course_key]

    try:
        # Send confirmation message
        await context.bot.send_message(
            chat_id=customer_id,
            text=f"🎉 Your payment has been verified by Admin!\n\nHere is your book: {name}"
        )

        # Send the actual PDF document from the server files
        with open(book_filename, 'rb') as book_file:
            await context.bot.send_document(
                chat_id=customer_id,
                document=book_file,
                caption=f"📖 {name} - Enjoy reading!"
            )
        
        # Safely update admin message to prevent NoneType errors
        old_caption = query.message.caption or ""
        old_text = query.message.text or ""
        
        if query.message.caption:
            await query.edit_message_caption(
                caption=old_caption + "\n\nSTATUS: ✅ APPROVED & BOOK SENT"
            )
        else:
            await query.edit_message_text(
                text=old_text + "\n\nSTATUS: ✅ APPROVED & BOOK SENT"
            )
        
    except Exception as e:
        await query.message.reply_text(f"Failed to send book to user: {e}")


# ==================== MAIN FUNCTION ====================
def main():
    if BOT_TOKEN == "PASTE_YOUR_NEW_TOKEN_HERE":
        raise ValueError("Please add your new BotFather token first.")

    # Start the dummy HTTP server in a background thread for Render
    server_thread = threading.Thread(target=run_dummy_server, daemon=True)
    server_thread.start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(select_course, pattern="^(basic|video|mobile|graphics)$"))
    app.add_handler(CallbackQueryHandler(payment, pattern="^(cbe|tele)$"))
    app.add_handler(CallbackQueryHandler(admin_approve, pattern="^approve_"))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, receive_receipt))

    print("Mesola Technology Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()