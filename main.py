import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = '8881509600:AAE1mehCUT2Op7G52iHiDrYBlH_2jLwM5Co'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Serviteur HTTP minimaliste pour empêcher Render de couper le bot
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to MBT_Tikfast! 🎥\nSend me any TikTok video link, and I will send you the video without a watermark."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if "tiktok.com" not in url:
        await update.message.reply_text("Please send a valid TikTok URL.")
        return

    status_msg = await update.message.reply_text("Downloading video, please wait...")

    try:
        # Resolve full URL if shortened link is provided
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        response = session.post("https://www.tikwm.com/api/", data={"url": url}).json()

        if response.get("code") == 0:
            video_data = response.get("data", {})
            play_url = video_data.get("play")
            
            if play_url:
                if not play_url.startswith("http"):
                    play_url = "https://www.tikwm.com" + play_url

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
    # Lance la reponse au port de Render en arriere-plan
    threading.Thread(target=run_dummy_server, daemon=True).start()

    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("MBT_Tikfast is running...")
    app.run_polling(drop_pending_updates=True)