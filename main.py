import os
import re
import httpx
from quart import Quart, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

TOKEN = os.environ.get("BOT_TOKEN", "VOTRE_TOKEN_TELEGRAM_ICI")
WEBHOOK_URL = "https://madi-b-tech-bot.onrender.com/webhook"

app = Quart(__name__)
telegram_app = Application.builder().token(TOKEN).build()

async def start(update, context):
    await update.message.reply_text("Bonjour ! Envoyez-moi un lien TikTok et je vous renverrai la vidéo sans filigrane.")

async def fetch_cobalt(url: str):
    """Méthode 1 : API Cobalt.tools (Extrêmement fiable sur les IPs cloud)"""
    api_url = "https://api.cobalt.tools/api/json"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    payload = {
        "url": url,
        "vCodec": "h264",
        "noWatermark": True
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            res = await client.post(api_url, headers=headers, json=payload)
            if res.status_code == 200:
                data = res.json()
                if data.get("status") in ["stream", "redirect"]:
                    return data.get("url")
        except Exception as e:
            print(f"Erreur Cobalt: {e}")
    return None

async def fetch_tikwm(url: str):
    """Méthode 2 : TikWM API avec en-têtes modifiés"""
    api_url = "https://www.tikwm.com/api/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
        "Accept": "*/*"
    }
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        try:
            res = await client.post(api_url, headers=headers, data={"url": url, "hd": 1})
            if res.status_code == 200:
                data = res.json()
                if data.get("code") == 0 and "data" in data:
                    return data["data"].get("play") or data["data"].get("hdplay")
        except Exception as e:
            print(f"Erreur TikWM: {e}")
    return None

async def download_tiktok_video(url: str):
    # 1. Tentative avec Cobalt API
    video_url = await fetch_cobalt(url)
    if video_url:
        return video_url
        
    # 2. Secours avec TikWM
    video_url = await fetch_tikwm(url)
    if video_url:
        return video_url

    return None

async def handle_tiktok(update, context):
    text = update.message.text
    tiktok_match = re.search(r'https?://[^\s]*tiktok\.com[^\s]*', text)
    
    if tiktok_match:
        clean_url = tiktok_match.group(0)
        msg = await update.message.reply_text("⏳ Extraction de la vidéo sans filigrane...")
        
        video_url = await download_tiktok_video(clean_url)
        
        if video_url:
            await msg.edit_text("🚀 Envoi de la vidéo en cours...")
            try:
                await update.message.reply_video(video=video_url, caption="Voici votre vidéo sans filigrane ! 🎬")
                await msg.delete()
            except Exception as e:
                await msg.edit_text(f"❌ Impossible d'envoyer le fichier vidéo : {e}")
        else:
            await msg.edit_text("❌ Impossible de récupérer la vidéo. Assurez-vous que la vidéo est publique.")
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
