import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# SETTINGS
BOT_TOKEN = "9216931047:AAGYhm4ycsktMXmh6JEODB-A9_LSQmIHBdg"
ADMIN_ID = 8892893806

CBE_ACCOUNT = "1000303969547"
CBE_NAME = "Mesfin"

TELEBIRR_NUMBER = "0931335199"
TELEBIRR_NAME = "Mesfin"

COURSES = {
    "basic": ("Basic Computer Skills Full Course", 350, "[https://t.me/your_channel/file_or_link_1](https://t.me/your_channel/file_or_link_1)"),
    "video": ("Video Editing Full Course", 450, "[https://t.me/your_channel/file_or_link_2](https://t.me/your_channel/file_or_link_2)"),
    "mobile": ("Mobile Software Full Course", 350, "[https://t.me/your_channel/file_or_link_3](https://t.me/your_channel/file_or_link_3)"),
    "graphics": ("Graphics Design Full Course", 500, "[https://t.me/your_channel/file_or_link_4](https://t.me/your_channel/file_or_link_4)"),
}

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Basic Computer Skills - 350 Birr", callback_data="basic")],
        [InlineKeyboardButton("Video Editing - 450 Birr", callback_data="video")],
        [InlineKeyboardButton("Mobile Software - 350 Birr", callback_data="mobile")],
        [InlineKeyboardButton("Graphics Design - 500 Birr", callback_data="graphics")],
    ]
    await update.message.reply_text(
        "Welcome to Mesola Technology! 📚\n\nChoose the book you want to purchase:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

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
        f"📚 {name}\n💰 Price: {price} Birr\n\nChoose your payment method:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if "course" not in context.user_data:
        await query.message.reply_text("Please select a book first. Use /start")
        return
    if query.data == "cbe":
        info = f"🏦 CBE PAYMENT\n\nAccount Name: {CBE_NAME}\nAccount Number: {CBE_ACCOUNT}"
    else:
        info = f"📱 TELEBIRR PAYMENT\n\nAccount Name: {TELEBIRR_NAME}\nPhone Number: {TELEBIRR_NUMBER}"
    await query.message.reply_text(info + "\n\nAfter payment, send your payment screenshot here.")

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

async def admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if update.effective_user.id != ADMIN_ID:
        await query.answer("You are not authorized!", show_alert=True)
        return
    data_parts = query.data.split("_")
    customer_id = int(data_parts[1])
    course_key = data_parts[2]
    name, _, book_link = COURSES[course_key]
    try:
        await context.bot.send_message(
            chat_id=customer_id,
            text=(
                "🎉 Your payment has been verified by Admin!\n\n"
                f"Here is your book: {name}\n"
                f"Download Link: {book_link}"
            )
        )
        if query.message.caption:
            await query.edit_message_caption(caption=query.message.caption + "\n\nSTATUS: ✅ APPROVED & BOOK SENT")
        else:
            await query.edit_message_text(text=query.message.text + "\n\nSTATUS: ✅ APPROVED & BOOK SENT")
    except Exception as e:
        await query.message.reply_text(f"Failed to send book to user: {e}")

def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        raise ValueError("Please add your BotFather token first.")
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