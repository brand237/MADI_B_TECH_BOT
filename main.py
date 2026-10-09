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

def download_tiktok_local(url: str, output_path: str) -> bool:
    """Télécharge la vidéo TikTok directement sur le disque du serveur."""
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return os.path.exists(output_path)
    except Exception as e:
        print(f"Erreur téléchargement yt-dlp : {e}")
        return False

async def handle_tiktok(update, context):
    text = update.message.text
    tiktok_match = re.search(r'https?://[^\s]*tiktok\.com[^\s]*', text)
    
    if tiktok_match:
        clean_url = tiktok_match.group(0)
        msg = await update.message.reply_text("⏳ Téléchargement de la vidéo en cours sur le serveur...")
        
        # Fichier temporaire
        file_path = f"video_{update.message.message_id}.mp4"
        
        # Exécution du téléchargement dans un thread séparé
        success = await asyncio.to_thread(download_tiktok_local, clean_url, file_path)
        
        if success:
            await msg.edit_text("🚀 Envoi de la vidéo vers Telegram...")
            try:
                with open(file_path, 'rb') as video_file:
                    await update.message.reply_video(video=video_file, caption="Voici votre vidéo sans filigrane ! 🎬")
                await msg.delete()
            except Exception as e:
                await msg.edit_text(f"❌ Erreur lors de l'envoi du fichier : {e}")
            finally:
                # Nettoyage du fichier local
                if os.path.exists(file_path):
                    os.remove(file_path)
        else:
            await msg.edit_text("❌ Impossible de télécharger la vidéo. Le lien est peut-être invalide ou la vidéo est privée.")
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
