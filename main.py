import os
import threading
import requests
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# 1. Configuration du serveur Web Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "MBT_Tikfast Bot is running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# 2. Logic du Bot Telegram
TOKEN = os.environ.get("TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bienvenue sur MBT_Tikfast ! Envoyez-moi un lien TikTok.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip() if update.message and update.message.text else ""
    if "tiktok.com" not in url:
        await update.message.reply_text("Veuillez envoyer un lien TikTok valide.")
        return

    status_msg = await update.message.reply_text("Téléchargement en cours...")

    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
        })
        res = session.post("https://www.tikwm.com/api/", data={"url": url, "hd": 1}).json()

        if res.get("code") == 0:
            play_url = res.get("data", {}).get("play")
            if play_url:
                if not play_url.startswith("http"):
                    play_url = "https://www.tikwm.com" + play_url
                await update.message.reply_video(video=play_url, caption="Téléchargé via MBT_Tikfast 🚀")
                await status_msg.delete()
                return

        await status_msg.edit_text("Impossible de récupérer la vidéo. Vérifiez le lien.")
    except Exception as e:
        await status_msg.edit_text("Une erreur est survenue lors du traitement.")

if __name__ == "__main__":
    # Lancement du serveur Flask dans un thread secondaire
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Lancement du bot Telegram sur le thread principal
    tg_app = ApplicationBuilder().token(TOKEN).build()
    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    tg_app.run_polling()