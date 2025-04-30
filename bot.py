import os
from dotenv import load_dotenv
from datetime import date
from telegram import (
    Update,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InputFile
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
    CallbackQueryHandler
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# Завантаження токена
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Етапи розмови
GET_PASSPORT_PHOTO, GET_CAR_PHOTO, CONFIRM_DATA, QUOTE_PRICE = range(4)

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привіт! 👋\nЯ бот для оформлення автострахування.\n\n"
        "Щоб почати, надішли фото свого паспорта 📸",
        reply_markup=ReplyKeyboardRemove()
    )
    return GET_PASSPORT_PHOTO

# Отримуємо фото паспорта
async def get_passport_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❗ Будь ласка, надішли саме *фото* паспорта, а не текст чи документ.", parse_mode="Markdown")
        return GET_PASSPORT_PHOTO

    photo_file = await update.message.photo[-1].get_file()
    user_id = update.message.from_user.id
    file_path = f"storage/{user_id}_passport.jpg"
    os.makedirs("storage", exist_ok=True)
    await photo_file.download_to_drive(file_path)
    context.user_data["passport_photo"] = file_path

    await update.message.reply_text("Дякую! ✅ Тепер надішли, будь ласка, фото техпаспорта 🚗")
    return GET_CAR_PHOTO

async def invalid_passport_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❗ Це не фото. Будь ласка, надішли саме *фото* паспорта.", parse_mode="Markdown")
    return GET_PASSPORT_PHOTO


# Отримуємо фото техпаспорта
async def get_car_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.photo:
        await update.message.reply_text("❗ Це не фото. Будь ласка, надішли фото техпаспорта 📷", parse_mode="Markdown")
        return GET_CAR_PHOTO

    photo_file = await update.message.photo[-1].get_file()
    user_id = update.message.from_user.id
    file_path = f"storage/{user_id}_car_doc.jpg"
    await photo_file.download_to_drive(file_path)
    context.user_data["car_photo"] = file_path

    await mock_recognize_documents(update, context)
    return CONFIRM_DATA

async def invalid_car_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❗ Це не фото. Будь ласка, надішли саме *фото* техпаспорта.", parse_mode="Markdown")
    return GET_CAR_PHOTO


# Мок-розпізнавання документів
async def mock_recognize_documents(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    mock_data = {
        "full_name": "Іваненко Іван Іванович",
        "passport_number": "АА123456",
        "car_model": "Toyota Corolla",
        "vin": "JTDBR32E820051234",
        "reg_number": "АА1234ВС"
    }

    context.user_data["recognized_data"] = mock_data

    text = (
        f"🔍 Ось що мені вдалося 'розпізнати':\n\n"
        f"👤 ПІБ: {mock_data['full_name']}\n"
        f"📄 Паспорт: {mock_data['passport_number']}\n"
        f"🚘 Авто: {mock_data['car_model']}\n"
        f"🔑 VIN: {mock_data['vin']}\n"
        f"📋 Номер авто: {mock_data['reg_number']}\n\n"
        "Все правильно?"
    )

    buttons = [
        [
            InlineKeyboardButton("✅ Так", callback_data="confirm_data"),
            InlineKeyboardButton("❌ Ні", callback_data="reject_data")
        ]
    ]

    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Обробка підтвердження даних
async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "confirm_data":
        await query.edit_message_text("Дякую за підтвердження ✅")

        # Пропонуємо ціну
        buttons = [
            [
                InlineKeyboardButton("💲 Так, погоджуюсь", callback_data="agree_price"),
                InlineKeyboardButton("❌ Ні, дорого", callback_data="decline_price")
            ]
        ]
        await query.message.reply_text(
            "💵 Вартість автострахування становить *100 USD*.\n"
            "Вас влаштовує така ціна?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return QUOTE_PRICE

    else:
        await query.edit_message_text("Будь ласка, надішліть фото ще раз.")
        return GET_PASSPORT_PHOTO

# Обробка відповіді на ціну
async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "agree_price":
        await query.edit_message_text("Чудово! ✨ Формуємо страховий поліс...")

        user_id = query.from_user.id
        data = context.user_data.get("recognized_data")

        policy_text = (
            "📄 *Страховий поліс*\n\n"
            f"👤 Страхувальник: {data['full_name']}\n"
            f"📄 Паспорт: {data['passport_number']}\n"
            f"🚘 Автомобіль: {data['car_model']}\n"
            f"🔑 VIN: {data['vin']}\n"
            f"📋 Номер авто: {data['reg_number']}\n"
            f"📆 Дата оформлення: {date.today()}\n"
            "✅ Поліс дійсний протягом 1 року"
        )

        await query.message.reply_text(policy_text, parse_mode="Markdown")

        pdf_path = generate_pdf_policy(user_id, data)

        with open(pdf_path, 'rb') as pdf_file:
            document = InputFile(pdf_file, filename=f"policy_{user_id}.pdf")
            await query.message.reply_document(document)

        return ConversationHandler.END

    else:
        await query.edit_message_text("Вибач, наразі можлива лише фіксована ціна 100 USD 💰.")
        return ConversationHandler.END

# Генерація PDF

font_path = os.path.join("fonts", "DejaVuSans.ttf")
pdfmetrics.registerFont(TTFont("DejaVuSans", font_path))

def generate_pdf_policy(user_id, data):
    path = f"storage/policy_{user_id}.pdf"
    c = canvas.Canvas(path, pagesize=A4)
    text = c.beginText(50, 800)
    text.setFont("DejaVuSans", 12)
    text.textLine("СТРАХОВИЙ ПОЛІС")
    text.textLine("")
    text.textLine(f"ПІБ: {data['full_name']}")
    text.textLine(f"Паспорт: {data['passport_number']}")
    text.textLine(f"Автомобіль: {data['car_model']}")
    text.textLine(f"VIN: {data['vin']}")
    text.textLine(f"Номер авто: {data['reg_number']}")
    text.textLine(f"Дата оформлення: {date.today()}")
    text.textLine("Поліс дійсний протягом 1 року")
    c.drawText(text)
    c.showPage()
    c.save()
    return path

# Запуск бота
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_PASSPORT_PHOTO: [
                MessageHandler(filters.PHOTO, get_passport_photo),
                MessageHandler(~filters.PHOTO, invalid_passport_input)  # якщо НЕ фото
            ],
            GET_CAR_PHOTO: [
                MessageHandler(filters.PHOTO, get_car_photo),
                MessageHandler(~filters.PHOTO, invalid_car_input)  # якщо НЕ фото
            ],
            CONFIRM_DATA: [
                CallbackQueryHandler(handle_confirmation, pattern="^(confirm_data|reject_data)$")
            ],
            QUOTE_PRICE: [
                CallbackQueryHandler(handle_price, pattern="^(agree_price|decline_price)$")
            ],
        },
        fallbacks=[]
    )
    app.add_handler(conv_handler)
    print("Бот запущено..")
    app.run_polling()

if __name__ == "__main__":
    main()
