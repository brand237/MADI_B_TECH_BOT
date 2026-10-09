import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler

# Token de votre bot Telegram (récupéré depuis @BotFather)
TOKEN = os.environ.get("BOT_TOKEN", "VOTRE_TOKEN_TELEGRAM_ICI")
WEBHOOK_URL = "https://madi-b-tech-bot.onrender.com/webhook"

app = Flask(__name__)

# Initialisation de la boucle d'événements asyncio globale
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Initialisation de l'application python-telegram-bot
telegram_app = Application.builder().token(TOKEN).build()

# Initialiser l'application Telegram une seule fois au démarrage
loop.run_until_complete(telegram_app.initialize())

# Commande /start
async def start(update, context):
    await update.message.reply_text("Bonjour ! Le bot fonctionne parfaitement en Webhook.")

telegram_app.add_handler(CommandHandler("start", start))

@app.route('/')
def index():
    return "Serveur Flask actif !"

@app.route('/webhook', methods=['POST'])
def webhook():
    """Point d'entrée où Telegram envoie les messages reçus."""
    json_data = request.get_json(force=True)
    update = Update.de_json(json_data, telegram_app.bot)
    
    # Traitement de la mise à jour sur la boucle principale
    loop.run_until_complete(telegram_app.process_update(update))
    return "OK", 200

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Route pour lier automatiquement votre URL Render à Telegram."""
    async def _set():
        return await telegram_app.bot.set_webhook(WEBHOOK_URL)
    
    success = loop.run_until_complete(_set())
    if success:
        return "Webhook activé avec succès sur Telegram !", 200
    return "Échec de la configuration du webhook.", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)