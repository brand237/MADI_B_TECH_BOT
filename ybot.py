import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp
from flask import Flask
import threading

# Configuration des logs
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "9075133731:AAHLJOXA0RVopiAgqz-_9rUkvY_7dsn03sg"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 Mo (Limite Bot API Telegram standard)

# --- MINI SERVEUR FLASK POUR LE MAINTIEN EN VEILLE (KEEP-ALIVE) ---
app = Flask('')

@app.route('/')
def home():
    return "Le bot Telegram de Brandon Tech est bien en ligne et actif !"

def run_web():
    # Render attribue dynamiquement un port via la variable d'environnement PORT, sinon on utilise le port 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()
# -----------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_message = (
        "🔥 **Salut et bienvenue !**\n\n"
        "Vous êtes ici sur le canal officiel des solutions automatisées propulsées par **Brandon Tech** (CEO de **MBT**). "
        "Notre mission : vous simplifier le digital au quotidien.\n\n"
        "Prêt à récupérer vos médias ? Envoyez-moi un lien YouTube et découvrez toutes les infos avant de télécharger ! 🎧📹"
    )
    await update.message.reply_text(welcome_message, parse_mode="Markdown")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("❌ Veuillez envoyer un lien YouTube valide.")
        return

    context.user_data["target_url"] = url

    await update.message.reply_text("🔍 Analyse des informations de la vidéo...")

    try:
        ydl_opts = {'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'Titre inconnu')
            author = info.get('uploader', 'Auteur inconnu')
            description = info.get('description', 'Aucune description disponible.')
            
            if len(description) > 350:
                description = description[:350] + "..."

        safe_title = title.replace('*', '').replace('_', '').replace('`', '')
        safe_author = author.replace('*', '').replace('_', '').replace('`', '')

        text_info = (
            f"🎬 **Titre :** {safe_title}\n"
            f"👤 **Auteur :** {safe_author}\n\n"
            f"📝 **Description :**\n{description}\n\n"
            f"🎯 **Choisissez votre format :**"
        )

        keyboard = [
            [
                InlineKeyboardButton("📹 Vidéo (MP4)", callback_data="format_video"),
                InlineKeyboardButton("🎵 Audio (MP3)", callback_data="format_audio")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(text_info, reply_markup=reply_markup, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Erreur d'extraction des métadonnées : {e}")
        keyboard = [
            [
                InlineKeyboardButton("📹 Vidéo (MP4)", callback_data="format_video"),
                InlineKeyboardButton("🎵 Audio (MP3)", callback_data="format_audio")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🎯 Vidéo détectée !\nChoisissez le format de téléchargement :", reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = context.user_data.get("target_url")
    if not url:
        await query.edit_message_text("❌ Session expirée. Veuillez renvoyer le lien YouTube.")
        return

    choice = query.data
    await query.edit_message_text("⏳ Téléchargement en cours, veuillez patienter...")

    output_dir = os.path.join(os.path.expanduser("~"), "yt_bot_downloads")
    os.makedirs(output_dir, exist_ok=True)

    try:
        if choice == "format_video":
            ydl_opts = {
                'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best',
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'noplaylist': False,
                'socket_timeout': 30,
                'retries': 10,
                'fragment_retries': 10,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                entries = info.get('entries', [info]) if 'entries' in info else [info]

                for entry in entries:
                    if not entry:
                        continue
                    filename = ydl.prepare_filename(entry)
                    if not filename.endswith('.mp4'):
                        filename = os.path.splitext(filename)[0] + '.mp4'

                    if os.path.exists(filename):
                        file_size = os.path.getsize(filename)
                        if file_size > MAX_FILE_SIZE:
                            await query.message.reply_text(
                                f"⚠️ Le fichier dépasse 50 Mo ({file_size // (1024*1024)} Mo). "
                                "Impossible de l'envoyer directement via Telegram."
                            )
                        else:
                            with open(filename, 'rb') as f:
                                await query.message.reply_video(video=f)
                        os.remove(filename)

        elif choice == "format_audio":
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'noplaylist': False,
                'socket_timeout': 30,
                'retries': 10,
                'fragment_retries': 10,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                entries = info.get('entries', [info]) if 'entries' in info else [info]

                for entry in