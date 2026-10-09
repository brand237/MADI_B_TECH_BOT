import os
import requests
from quart import Quart, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

TOKEN = os.environ.get("BOT_TOKEN", "8881509600:AAE1mehCUT2Op7G52iHiDrYBlH_2jLwM5Co")
WEBHOOK_URL = "https://madi-b-tech-bot.onrender.com/webhook"

app = Quart(__name__)

# Initialisation de l'application Telegram
telegram_app = Application.builder().token(TOKEN).build()

async def start(update, context):
    await update.message.reply_text("Bonjour ! Envoyez-moi un lien TikTok et je vous renverrai la vidéo sans filigrane.")

def download_tiktok_video(url: str):
    """Récupère l'URL de la vidéo sans filigrane via l'API TikWM."""
    api_url = "https://www.tikwm.com/api/"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"url": url, "hd": 1}
    
    response = requests.post(api_url, headers=headers, data=data)
    if response.status_code == 200:
        res_json = response.json()
        if res_json.get("code") == 0:
            return res_json["data"]["play"]
    return None

async def handle_tiktok(update, context):
    text = update.message.text
    if "tiktok.com" in text:
        msg = await update.message.reply_text("⏳ Téléchargement de la vidéo sans filigrane en cours...")
        video_url = download_tiktok_video(text)
        
        if video_url:
            await update.message.reply_video(video=video_url, caption="Voici votre vidéo sans filigrane ! 🎬")
            await msg.delete()
        else:
            await msg.edit_text("❌ Impossible de récupérer la vidéo. Vérifiez le lien fourni.")
    else:
        await update.message.reply_text("Veuillez m'envoyer un lien TikTok valide.")

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tiktok))

@app.before_serving
async def startup():
    """Initialise le bot Telegram au démarrage du serveur."""
    await telegram_app.initialize()

@app.route('/')
async def index():
    return "Serveur Quart actif !"

@app.route('/webhook', methods=['POST'])
async def webhook():
    json_data = await request.get_json(force=True)
    update = Update.de_json(json_data, telegram_app.bot)
    
    async with telegram_app:
        await telegram_app.process_update(update)
        
    return "OK", 200

@app.route('/set_webhook', methods=['GET'])
async def set_webhook():
    async with telegram_app.bot:
        success = await telegram_app.bot.set_webhook(WEBHOOK_URL)
        
    if success:
        return "Webhook activé avec succès sur Telegram !", 200
    return "Échec de la configuration du webhook.", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)