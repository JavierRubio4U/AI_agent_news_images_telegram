import os
from datetime import datetime
from telegram import Bot
from dotenv import load_dotenv
import re
from pathlib import Path

# Cargar token y chat ID desde .env
load_dotenv(dotenv_path=Path(__file__).resolve().parent / "credenciales_telegram.env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("❌ Faltan las variables TELEGRAM_TOKEN o TELEGRAM_CHAT_ID en el .env")

bot = Bot(token=TELEGRAM_TOKEN)


def publicar_en_telegram(texto):
    try:
        # 🔍 Intentar extraer primer párrafo como titular
        partes = texto.strip().split("\n\n")
        if len(partes) >= 2:
            titular = partes[0].strip()
            cuerpo = "\n\n".join(partes[1:]).strip()
        else:
            # Fallback: usar primeras 15 palabras como titular
            palabras = texto.strip().split()
            titular = " ".join(palabras[:15]) + "..."
            cuerpo = texto.strip()

        # Extraer posible URL al final del cuerpo
        url_match = re.search(r"(https?://[^\s]+)", cuerpo)
        url = url_match.group(1) if url_match else None

        # Limpiar el titular (sin número ni URL final)
        titular = re.sub(r"^\d+\.\s*", "", titular)  # Quitar "5. "
        titular = re.sub(r"\s*\(https?://[^\s]+\)$", "", titular)  # Quitar (url)

        # 🕒 Fecha y hora
        ahora = datetime.now().strftime("%d/%m/%Y %H:%M")

        # 📤 Formatear mensaje final
        mensaje = f"📰 *Titulo: {titular}*\n_Publicado: {ahora}_\n\n{cuerpo}"

        # Añadir fuente si hay URL
        if url:
            mensaje += f"\n\n🔗 *Fuente:* {url}"

        import asyncio
        asyncio.run(bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=mensaje,
            parse_mode="Markdown"
        ))

        print("✅ Mensaje enviado a Telegram.")

    except Exception as e:
        print(f"❌ Error al publicar en Telegram: {e}")