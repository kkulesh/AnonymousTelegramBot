from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

BOT_TOKEN = '...'
CHANNEL_ID = ...

# Словник для збереження стану користувача
user_states = {}

# Стани
STATE_NONE = "none"
STATE_MESSAGE = "message"
STATE_COMPLAINT = "complaint"
STATE_IDEA = "idea"

# /start — показує меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📩 Анонімне повідомлення", callback_data='message')],
        [InlineKeyboardButton("✍️ Залишити скаргу", callback_data='complaint')],
        [InlineKeyboardButton("💡 Запропонувати ідею", callback_data='idea')],
        [InlineKeyboardButton("❌ Відміна", callback_data='cancel')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Оберіть тип повідомлення:", reply_markup=reply_markup)

# Обробка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == 'message':
        user_states[user_id] = STATE_MESSAGE
        await query.message.reply_text("📩 Напишіть ваше повідомлення.")
    elif query.data == 'complaint':
        user_states[user_id] = STATE_COMPLAINT
        await query.message.reply_text("✍️ Напишіть вашу скаргу.")
    elif query.data == 'idea':
        user_states[user_id] = STATE_IDEA
        await query.message.reply_text("💡 Напишіть вашу ідею.")
    else:
        user_states[user_id] = STATE_NONE
        await query.message.reply_text("❌ Скасовано.")

# Обробка повідомлень
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message

    # Ігноруємо повідомлення з груп
    if message.chat.type != "private":
        return

    user_id = message.from_user.id
    state = user_states.get(user_id, STATE_NONE)

    if state == STATE_NONE:
        await message.reply_text("ℹ️ Спочатку оберіть тип повідомлення: /start")
        return

    # Префікси для різних типів
    prefix = "📢 Нове повідомлення:"
    if state == STATE_MESSAGE:
        prefix = "📩 Анонімне повідомлення:"
    elif state == STATE_COMPLAINT:
        prefix = "✍️ Анонімна скарга:"
    elif state == STATE_IDEA:
        prefix = "💡 Анонімна ідея:"

    # Відправляємо у канал
    if message.text:
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"{prefix}\n\n{message.text}"
        )
    elif message.photo:
        await context.bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=message.photo[-1].file_id,
            caption=message.caption or prefix
        )
    elif message.document:
        await context.bot.send_document(
            chat_id=CHANNEL_ID,
            document=message.document.file_id,
            caption=message.caption or prefix
        )
    else:
        await message.reply_text("⚠️ Непідтримуваний тип повідомлення.")

    # Після відправки скидаємо стан
    user_states[user_id] = STATE_NONE
    await message.reply_text("✅ Ваше повідомлення надіслано анонімно. Дякуємо!")

# Запуск бота
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))

app.run_polling()
