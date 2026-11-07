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

# መጽሐፎች እና ፋይሎቻቸው (የሰነድ ሊንክ፣ የቴሌግራም ፋይል 🆔 ወይም ዩአርኤል ማስገባት ይቻላል)
COURSES = {
    "basic": ("Basic Computer Skills Full Course", 350, "https://t.me/your_channel/file_or_link_1"),
    "video": ("Video Editing Full Course", 450, "https://t.me/your_channel/file_or_link_2"),
    "mobile": ("Mobile Software Full Course", 350, "https://t.me/your_channel/file_or_link_3"),
    "graphics": ("Graphics Design Full Course", 500, "https://t.me/your_channel/file_or_link_4"),
}

logging.basicConfig(level=logging.INFO)


# 1. START
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


# 2. COURSE SELECTION
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


# 3. PAYMENT INFORMATION
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


# 4. RECEIVE PAYMENT SCREENSHOT & NOTIFY ADMIN
async def receive_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    course = context.user_data.get("course")

    if not course:
        await update.message.reply_text("Please select a book first. Use /start")
        return

    user = update.effective_user
    name, price, _ = COURSES[course]

    # ለአድሚኑ ማረጋገጫ የሚሆን አዝራር (Approve Button) መፍጠር
    # ዩዘር ਆਈዲ (user.id) እና ኮርሱን (course) በ callback_data ውስጥ እናያይዛለን
    keyboard = [
        [InlineKeyboardButton("✅ Approve & Send Book", callback_data=f"approve_{user.id}_{course}")]
    ]

    # ስክሪንሾቱን እና መረጃውን ወደ አድሚን መላክ
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


# 5. ADMIN APPROVAL & SENDING BOOK
async def admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # አድሚኑ መሆኑን ማረጋገጥ
    if update.effective_user.id != ADMIN_ID:
        await query.answer("You are not authorized!", show_alert=True)
        return

    # ዳታውን ከ callback_data መውሰድ (ምሳሌ: approve_12345678_basic)
    data_parts = query.data.split("_")
    customer_id = int(data_parts[1])
    course_key = data_parts[2]

    name, price, book_link = COURSES[course_key]

    # መጽሐፉን ለተጠቃሚው መላክ
    try:
        await context.bot.send_message(
            chat_id=customer_id,
            text=(
                "🎉 Your payment has been verified by Admin!\n\n"
                f"Here is your book: {name}\n"
                f"Download Link: {book_link}"
            )
        )
        
        # ለአድሚኑ የተረጋገጠ መሆኑን ማሳየት
        await query.edit_message_caption(
            caption=query.message.caption + "\n\nSTATUS: ✅ APPROVED & BOOK SENT"
        ) if query.message.caption else await query.edit_message_text(
            text=query.message.text + "\n\nSTATUS: ✅ APPROVED & BOOK SENT"
        )
        
    except Exception as e:
        await query.message.reply_text(f"Failed to send book to user: {e}")


# MAIN
def main():
    if BOT_TOKEN == "PASTE_YOUR_NEW_TOKEN_HERE":
        raise ValueError("Please add your new BotFather token first.")

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