import os
import re
import httpx
from quart import Quart, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

TOKEN = os.environ.get("BOT_TOKEN", "8881509600:AAE1mehCUT2Op7G52iHiDrYBlH_2jLwM5Co")
WEBHOOK_URL = "https://madi-b-tech-bot.onrender.com/webhook"

app = Quart(__name__)
telegram_app = Application.builder().token(TOKEN).build()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.tikwm.com/",
}

async def start(update, context):
    await update.message.reply_text("Bonjour ! Envoyez-moi un lien TikTok et je vous renverrai la vidéo sans filigrane.")

async def resolve_tiktok_url(url: str) -> str:
    """Résout les liens courts (vt.tiktok.com) vers l'URL canonique."""
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            res = await client.get(url, headers={"User-Agent": HEADERS["User-Agent"]})
            return str(res.url)
    except Exception as e:
        print(f"Erreur résolution : {e}")
        return url

async def fetch_tikwm(url: str):
    """Méthode 1 : API TikWM"""
    api_url = "https://www.tikwm.com/api/"
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            res = await client.post(api_url, headers=HEADERS, data={"url": url, "hd": 1})
            if res.status_code == 200:
                data = res.json()
                if data.get("code") == 0 and "data" in data:
                    return data["data"].get("play") or data["data"].get("hdplay")
        except Exception as e:
            print(f"Erreur TikWM: {e}")
    return None

async def fetch_ssstik(url: str):
    """Méthode 2 : API SSSTik"""
    api_url = "https://ssstik.io/abc?url=dl"
    headers = {
        "User-Agent": HEADERS["User-Agent"],
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "hx-request": "true",
        "hx-target": "target",
        "hx-current-url": "https://ssstik.io/en"
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            res = await client.post(api_url, headers=headers, data={"id": url, "locale": "en", "tt": "0"})
            if res.status_code == 200:
                # Extraction du lien mp4 dans le HTML retourné par ssstik
                match = re.search(r'href="(https?://[^"]+\.mp4[^"]*)"', res.text)
                if match:
                    return match.group(1)
        except Exception as e:
            print(f"Erreur SSSTik: {e}")
    return None

async def download_tiktok_video(url: str):
    final_url = await resolve_tiktok_url(url)
    
    # Tentative 1: TikWM
    video_url = await fetch_tikwm(final_url)
    if video_url:
        return video_url
        
    # Tentative 2: SSSTik
    video_url = await fetch_ssstik(final_url)
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
