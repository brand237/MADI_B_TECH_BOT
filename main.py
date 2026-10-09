import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")  # Ou mettez votre token Telegram directement
WEBHOOK_URL = "https://madi-b-tech-bot.onrender.com/webhook"

app = Flask(__name__)

# Initialisation de l'application Telegram
telegram_app = Application.builder().token(TOKEN).build()

async def start(update, context):
    await update.message.reply_text("Bonjour ! Le bot est en ligne.")

telegram_app.add_handler(CommandHandler("start", start))

@app.route('/')
def index():
    return "Bot en ligne !"

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Reçoit les mises à jour de Telegram"""
    json_str = request.get_data().decode('UTF-8')
    update = Update.de_json(eval(json_str), telegram_app.bot)
    await telegram_app.process_update(update)
    return "OK", 200

# Endpoint pour enregistrer le webhook auprès de Telegram
@app.route('/set_webhook', methods=['GET'])
async def set_webhook():
    success = await telegram_app.bot.set_webhook(WEBHOOK_URL)
    if success:
        return "Webhook configuré avec succès !"
    return "Échec de la configuration du webhook", 500