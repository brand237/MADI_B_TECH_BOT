import os
import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
import yt_dlp
from flask import Flask
import threading

# Configuration des logs
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "9075133731:AAHVYpj8kOyB3HLr-MdEsYymp7-UoUAqM8M"
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 Mo (Limite Bot API Telegram standard)

# Statistiques globales du bot (en mémoire)
bot_stats = {
    "start_time": time.time(),
    "total_downloads": 0,
    "active_users": set()
}

# --- MINI SERVEUR FLASK POUR LE MAINTIEN EN VEILLE (KEEP-ALIVE) ---
app = Flask('')

@app.route('/')
def home():
    return "Le bot Telegram de Brandon Tech est bien en ligne et actif !"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = threading.Thread(target=run_web)
    t.daemon = True
    t.start()
# -----------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    bot_stats["active_users"].add(user.id)
    
    welcome_message = (
        "🔥 **Salut et bienvenue !**\n\n"
        "Vous êtes ici sur le canal officiel des solutions automatisées propulsées par **Brandon Tech** (CEO de **MBT**). "
        "Notre mission : vous simplifier le digital au quotidien.\n\n"
        "Envoyez-moi un lien YouTube pour accéder aux options avancées (choix de résolution, miniature, audio HD) ! 🎧📹"
    )
    await update.message.reply_text(welcome_message, parse_mode="Markdown")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Commande /stats pour l'administration
    uptime_seconds = int(time.time() - bot_stats["start_time"])
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    
    stats_text = (
        "📊 **Statistiques du Bot (Brandon Tech)**\n\n"
        f"👥 **Utilisateurs uniques :** {len(bot_stats['active_users'])}\n"
        f"📥 **Téléchargements totaux :** {bot_stats['total_downloads']}\n"
        f"⏱️ **Temps de fonctionnement :** {hours}h {minutes}m\n"
        f"🟢 **Statut Render / UptimeRobot :** Actif (24h/24)"
    )
    await update.message.reply_text(stats_text, parse_mode="Markdown")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    user = update.effective_user
    bot_stats["active_users"].add(user.id)

    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("❌ Veuillez envoyer un lien YouTube valide.")
        return

    context.user_data["target_url"] = url
    await update.message.reply_text("🔍 Analyse des informations et des formats disponibles...")

    try:
        ydl_opts = {'skip_download': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'Titre inconnu')
            author = info.get('uploader', 'Auteur inconnu')
            description = info.get('description', 'Aucune description disponible.')
            
            if len(description) > 300:
                description = description[:300] + "..."

        safe_title = title.replace('*', '').replace('_', '').replace('`', '')
        safe_author = author.replace('*', '').replace('_', '').replace('`', '')

        text_info = (
            f"🎬 **Titre :** {safe_title}\n"
            f"👤 **Auteur :** {safe_author}\n\n"
            f"📝 **Description :**\n{description}\n\n"
            f"🎯 **Choisissez votre format :**"
        )

        # Menu interactif enrichi (Options 1, 2, 5)
        keyboard = [
            [
                InlineKeyboardButton("📹 Vidéo 720p", callback_data="vid_720"),
                InlineKeyboardButton("📹 Vidéo 360p", callback_data="vid_360")
            ],
            [
                InlineKeyboardButton("🎵 Audio MP3 (192 kbps)", callback_data="aud_192"),
                InlineKeyboardButton("🎵 Audio MP3 (320 kbps)", callback_data="aud_320")
            ],
            [
                InlineKeyboardButton("🖼️ Télécharger la miniature", callback_data="get_thumb")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(text_info, reply_markup=reply_markup, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Erreur d'extraction : {e}")
        keyboard = [
            [
                InlineKeyboardButton("📹 Vidéo 720p", callback_data="vid_720"),
                InlineKeyboardButton("🎵 Audio MP3", callback_data="aud_192")
            ],
            [
                InlineKeyboardButton("🖼️ Miniature", callback_data="get_thumb")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("🎯 Média détecté !\nChoisissez une option :", reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = context.user_data.get("target_url")
    if not url:
        await query.edit_message_text("❌ Session expirée. Veuillez renvoyer le lien YouTube.")
        return

    choice = query.data
    output_dir = os.path.join(os.path.expanduser("~"), "yt_bot_downloads")
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Option 2 : Téléchargement de la miniature seule
        if choice == "get_thumb":
            await query.edit_message_text("⏳ Récupération de la miniature...")
            ydl_opts = {'skip_download': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                thumbnail_url = info.get('thumbnail')
                
                if thumbnail_url:
                    await query.message.reply_photo(photo=thumbnail_url, caption="🖼️ Miniature officielle de la vidéo.")
                    await query.message.reply_text("✅ Miniature envoyée avec succès !")
                else:
                    await query.message.reply_text("❌ Aucune miniature trouvée pour cette vidéo.")
            return

        # Options Vidéo (1) et Audio (5)
        await query.edit_message_text("⏳ Téléchargement et traitement en cours, veuillez patienter...")

        if choice.startswith("vid_"):
            quality = "720" if "720" in choice else "360"
            ydl_opts = {
                'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]/best',
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'noplaylist': True,
                'socket_timeout': 30,
                'retries': 10,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
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

        elif choice.startswith("aud_"):
            bitrate = "320" if "320" in choice else "192"
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': bitrate,
                }],
                'noplaylist': True,
                'socket_timeout': 30,
                'retries': 10,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                filename = os.path.splitext(filename)[0] + ".mp3"

                if os.path.exists(filename):
                    file_size = os.path.getsize(filename)
                    if file_size > MAX_FILE_SIZE:
                        await query.message.reply_text(
                            f"⚠️ L'audio dépasse 50 Mo. "
                            "Impossible de l'envoyer directement."
                        )
                    else:
                        with open(filename, 'rb') as f:
                            await query.message.reply_audio(audio=f)
                    os.remove(filename)

        # Incrémenter les statistiques de téléchargement
        bot_stats["total_downloads"] += 1
        await query.message.reply_text("✅ Traitement terminé avec succès !")

    except Exception as e:
        logger.error(f"Erreur de traitement : {e}")
        await query.message.reply_text(f"❌ Une erreur est survenue : {str(e)}")

def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_handler(CallbackQueryHandler(button_callback))

    application.run_polling()

if __name__ == "__main__":
    keep_alive()
    main()