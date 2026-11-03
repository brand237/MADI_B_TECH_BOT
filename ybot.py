import re  # Assurez-vous d'importer re en haut du fichier

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user = update.effective_user
    bot_stats["active_users"].add(user.id)

    # Extraction propre de l'URL via Regex (isole le lien peu importe le texte autour)
    url_match = re.search(r'(https?://[^\s]+)', text)
    if not url_match:
        await update.message.reply_text("❌ Veuillez envoyer un lien YouTube valide.")
        return

    url = url_match.group(1)
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("❌ Ce lien ne provient pas de YouTube.")
        return

    context.user_data["target_url"] = url
    await update.message.reply_text("🔍 Analyse des informations et des formats disponibles...")

    try:
        # Ajout du contournement anti-bot dans les options d'extraction
        ydl_opts = {
            'skip_download': True,
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
        }
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
        # Boutons de secours si les métadonnées échouent mais que le lien est valide
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