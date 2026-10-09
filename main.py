import threading
from flask import Flask
# Importez votre bot Telegram ici (ex: de telegram.ext import Application...)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_telegram_bot():
    # Placez le code d'initialisation et d'exécution de votre bot ici
    # Exemple: application.run_polling()
    pass

# Démarre le bot sur un thread séparé pour ne pas bloquer Gunicorn
bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
bot_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)