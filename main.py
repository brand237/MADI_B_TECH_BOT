import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN", "8881509600:AAE1mehCUT2Op7G52iHiDrYBlH_2jLwM5Co")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def resolve_url(url: str) -> str:
    """Suit les redirections pour obtenir l'URL finale (utile pour vt.tiktok.com)."""
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
        })
        res = session.get(url, allow_redirects=True, timeout=10)
        return res.url
    except Exception as e:
        logging.error(f"Erreur resolution URL: {e}")
        return url

def get_video_url_tikwm(url: str):
    """Méthode 1 : TikWM API avec headers navigateur."""
    try:
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://www.tikwm.com/'
        }
        res = session.post("https://www.tikwm.com/api/", data={"url": url, "hd": 1}, headers=headers, timeout=10)
        
        # Vérifie si la réponse est du JSON valide
        if res.status_code == 200 and res.text.startswith('{'):
            data = res.json()
            if data.get("code") == 0:
                play_url = data.get("data", {}).get("play")
                if play_url and not play_url.startswith("http"):
                    play_url = "https://www.tikwm.com" + play_url
                return play_url
    except Exception as e:
        logging.error(f"Erreur TikWM: {e}")
    return None

def get_video_url_cobalt(url: str):
    """Méthode 2 de secours : Cobalt API (contourne les blocages d'IP Cloud)."""
    try:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        payload = {"url": url, "noWatermark": True}
        res = requests.post("https://api.cobalt.tools/api/json", json=payload, headers=headers, timeout=10)
        if res.status_code == 200 and res.text.startswith('{'):
            data = res.json()
            if data.get("status") in ["stream", "redirect"]:
                return data.get("url")
    except Exception as e:
        logging.error(f"Erreur Cobalt: {e}")
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to MBT_Tikfast! 🎥\nSend me any TikTok video link, and I will send you the video without a watermark."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_url = update.message.text.strip()
    
    if "tiktok.com" not in raw_url:
        await update.message.reply_text("Please send a valid TikTok URL.")
        return

    status_msg = await update.message.reply_text("Downloading video, please wait...")

    try:
        # 1. Résolution de l'URL finale (liens courts vt.tiktok.com)
        full_url = resolve_url(raw_url)

        # 2. Essai via TikWM
        play_url = get_video_url_tikwm(full_url)
        
        # 3. Secours via Cobalt si TikWM est bloqué sur Render
        if not play_url:
            play_url = get_video_url_cobalt(full_url)

        if play_url:
            await update.message.reply_video(
                video=play_url,
                caption="Downloaded via MBT_Tikfast 🚀"
            )
            await status_msg.delete()
            return

        await status_msg.edit_text("Could not fetch the video. Please check the link or try another video.")

    except Exception as e:
        logging.error(f"Error processing TikTok URL: {e}", exc_info=True)
        await status_msg.edit_text("An error occurred while processing your request.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("MBT_Tikfast is running...")
    app.run_polling(drop_pending_updates=True)