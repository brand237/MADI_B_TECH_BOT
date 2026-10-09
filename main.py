import os
import asyncio
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Configuration Token et Webhook
TOKEN = os.environ.get("BOT_TOKEN", "VOTRE_TOKEN_TELEGRAM_ICI")
WEBHOOK_URL = "https://madi-b-tech-bot.onrender.com/webhook"

app = Flask(__name__)

# Initialisation de la boucle d'événements asyncio
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Initialisation du bot Telegram
telegram_app = Application.builder().token(TOKEN).build()
loop.run_until_complete(telegram_app.initialize())

async def start(update, context):
    await update.message.reply_text("Bonjour ! Envoyez-moi un lien TikTok et je vous renverrai la vidéo sans filigrane.")

async def download_tiktok_video(url: str):
    """Récupère l'URL de la vidéo sans filigrane via l'API TikWM."""
    api_url = "https://www.tikwm.com/api/"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"url": url, "hd": 1}
    
    response = requests.post(api_url, headers=headers, data=data)
    if response.status_code == 200:
        res_json = response.json()
        if res_json.get("code") == 0:
            # Lien direct de la vidéo sans filigrane
            video_url = res_json["data"]["play"]
            return video_url
    return None

async def handle_tiktok(update, context):
    text = update.message.text
    if "tiktok.com" in text:
        msg = await update.message.reply_text("⏳ Téléchargement de la vidéo sans filigrane en cours...")
        
        video_url = await download_tiktok_video(text)
        
        if video_url:
            # Envoie la vidéo directement sur Telegram
            await update.message.reply_video(video=video_url, caption="Voici votre vidéo sans filigrane ! 🎬")
            await msg.delete()
        else:
            await msg.edit_text("❌ Impossible de récupérer la vidéo. Vérifiez le lien fourni.")
    else:
        await update.message.reply_text("Veuillez m'envoyer un lien TikTok valide.")

# Enregistrement des gestionnaires de commandes et messages
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tiktok))

@app.route('/')
def index():
    return "Serveur Flask actif !"

@app.route('/webhook', methods=['POST'])
def webhook():
    json_data = request.get_json(force=True)
    update = Update.de_json(json_data, telegram_app.bot)
    loop.run_until_complete(telegram_app.process_update(update))
    return "OK", 200

@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    async def _set():
        return await telegram_app.bot.set_webhook(WEBHOOK_URL)
    
    success = loop.run_until_complete(_set())
    if success:
        return "Webhook activé avec succès sur Telegram !", 200
    return "Échec de la configuration du webhook.", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)