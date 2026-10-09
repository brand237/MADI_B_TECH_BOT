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

async def start(update, context):
    await update.message.reply_text("Bonjour ! Envoyez-moi un lien TikTok et je vous renverrai la vidéo sans filigrane.")

async def resolve_tiktok_url(url: str) -> str:
    """Résout les liens courts (vt.tiktok.com, vm.tiktok.com) vers l'URL canonique complète."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            return str(response.url)
    except Exception as e:
        print(f"Erreur de résolution d'URL : {e}")
        return url

async def download_tiktok_video(url: str):
    """Obtient le lien direct vidéo sans filigrane via l'API TikWM."""
    # 1. Résolution préalable de l'URL finale
    final_url = await resolve_tiktok_url(url)
    
    api_url = "https://www.tikwm.com/api/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
    }
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(api_url, headers=headers, data={"url": final_url, "hd": 1})
            if response.status_code == 200:
                res_json = response.json()
                if res_json.get("code") == 0 and "data" in res_json:
                    data = res_json["data"]
                    # Privilégie le lien vidéo standard sans watermark ou HD
                    return data.get("play") or data.get("hdplay")
                else:
                    print(f"Réponse TikWM : {res_json.get('msg')}")
        except Exception as e:
            print(f"Erreur requête TikWM : {e}")
            
    return None

async def handle_tiktok(update, context):
    text = update.message.text
    tiktok_match = re.search(r'https?://[^\s]*tiktok\.com[^\s]*', text)
    
    if tiktok_match:
        clean_url = tiktok_match.group(0)
        msg = await update.message.reply_text("⏳ Traitement du lien et extraction de la vidéo...")
        
        video_url = await download_tiktok_video(clean_url)
        
        if video_url:
            await msg.edit_text("🚀 Envoi de la vidéo en cours...")
            await update.message.reply_video(video=video_url, caption="Voici votre vidéo sans filigrane ! 🎬")
            await msg.delete()
        else:
            await msg.edit_text("❌ Impossible de récupérer la vidéo. Assurez-vous que le lien est valide et que la vidéo n'est pas privée.")
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)