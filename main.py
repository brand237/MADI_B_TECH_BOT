import os
import logging
import threading
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

TOKEN = os.environ.get("BOT_TOKEN", "8881509600:AAE1mehCUT2Op7G52iHiDrYBlH_2jLwM5Co")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Serveur HTTP factice pour empêcher le shutdown de Render
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

def download_tiktok_file(url: str, output_path: str) -> bool:
    """Télécharge physiquement le MP4 sur le serveur en imitant un smartphone."""
    ydl_opts = {
        'format': 'b/best',
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return os.path.exists(output_path) and os.path.getsize(output_path) > 0
    except Exception as e:
        logging.error(f"Erreur yt-dlp download : {e}")
        return False

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
    file_path = f"video_{update.message.message_id}.mp4"

    try:
        # Téléchargement local asynchrone
        success = await asyncio.to_thread(download_tiktok_file, url, file_path)

        if success:
            await status_msg.edit_text("Uploading to Telegram...")
            with open(file_path, 'rb') as video_file:
                await update.message.reply_video(
                    video=video_file,
                    caption="Downloaded via MBT_Tikfast 🚀"
                )
            await status_msg.delete()
        else:
            await status_msg.edit_text("Could not fetch the video. Please check the link or try another video.")

    except Exception as e:
        logging.error(f"Error processing TikTok URL: {e}", exc_info=True)
        await status_msg.edit_text("An error occurred while processing your request.")
        
    finally:
        # Suppression du fichier temporaire après l'envoi
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == '__main__':
    # Démarre le serveur dummy pour le port 10000 sur Render
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("MBT_Tikfast is running...")
    app.run_polling(drop_pending_updates=True)