import os
import re
import asyncio
from quart import Quart, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import yt_dlp

TOKEN = os.environ.get("BOT_TOKEN", "8881509600:AAE1mehCUT2Op7G52iHiDrYBlH_2jLwM5Co")
WEBHOOK_URL = "https://madi-b-tech-bot.onrender.com/webhook"

app = Quart(__name__)

telegram_app = Application.builder().token(TOKEN).build()

async def start(update, context):
    await update.message.reply_text("Bonjour ! Envoyez-moi un lien TikTok et je vous renverrai la vidéo sans filigrane.")

def extract_with_ytdlp(url: str) -> str:
    """Extrait l'URL directe du fichier vidéo MP4 via yt-dlp."""
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get('url')

async def download_tiktok_video(url: str):
    try:
        # Exécution de yt-dlp dans un thread séparé pour ne pas bloquer Quart
        video_url = await asyncio.to_thread(extract_with_ytdlp, url)
        return video_url
    except Exception as e:
        print(f"Erreur yt-dlp : {e}")
        return None

async def handle_tiktok(update, context):
    text = update.message.text
    tiktok_match = re.search(r'https?://[^\s]*tiktok\.com[^\s]*', text)
    
    if tiktok_match:
        clean_url = tiktok_match.group(0)
        msg = await update.message.reply_text("⏳ Extraction de la vidéo avec yt-dlp...")
        
        video_url = await download_tiktok_video(clean_url)
        
        if video_url:
            await msg.edit_text("🚀 Envoi de la vidéo en cours...")
            await update.message.reply_video(video=video_url, caption="Voici votre vidéo sans filigrane ! 🎬")
            await msg.delete()
        else:
            await msg.edit_text("❌ Impossible de récupérer la vidéo. Assurez-vous que le lien est valide.")
    else:
        await update.message.reply_text("Veuillez envoyer un lien TikTok valide.")

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_tiktok))

@app.before_serving
async def startup():
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
