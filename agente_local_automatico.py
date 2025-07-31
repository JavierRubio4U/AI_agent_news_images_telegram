import os
import random
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
import requests
import feedparser
from io import BytesIO
from PIL import Image
from telegram import Bot
from telegram.constants import ParseMode

# 📁 Cargar credenciales desde .env
load_dotenv(dotenv_path=Path(__file__).resolve().parent / "credenciales_telegram.env")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(token=TELEGRAM_TOKEN)

# 🔍 Obtener noticias
def obtener_noticias_rss(feed_url="https://venturebeat.com/feed/"):
    feed = feedparser.parse(feed_url)
    noticias = []
    for entrada in feed.entries[:3]:
        titulo = entrada.title
        enlace = entrada.link
        publicado = datetime(*entrada.published_parsed[:6])
        contenido = entrada.summary
        noticias.append((titulo, contenido, publicado, enlace))
    return noticias

# 🧠 LLM local
def modelo_llm(prompt: str) -> str:
    url = "http://localhost:11434/v1/completions"
    response = requests.post(url, json={
        "model": "mistralai/mistral-7b-instruct-v0.3",
        "prompt": prompt,
        "max_tokens": 500,
        "temperature": 0.7
    })
    respuesta_json = response.json()
    return respuesta_json["choices"][0]["text"]

# 🖼️ Imagen estilo GTA V sin letras
async def generar_imagen_gtav() -> BytesIO:
    prompt = "futuristic city, neon lights, cyberpunk woman, gta v style"
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

# 📰 Resumir noticia
def formatear_noticia(noticia_completa: str, fecha: datetime) -> str:
    prompt = f"""
Analiza la siguiente noticia y responde separando claramente tres secciones:

1. TÍTULO: Un titular corto (máx 15 palabras) que resuma lo más importante.
2. RESUMEN: Qué ha pasado, explicado brevemente (máx 5 líneas).
3. COMENTARIO: Breve análisis del impacto, posibles consecuencias o contexto adicional (máx 8 líneas).

Noticia original:
\"\"\"{noticia_completa}\"\"\"
"""
    respuesta = modelo_llm(prompt).strip()
    fecha_str = fecha.strftime("%d/%m/%Y %H:%M")
    return f"{respuesta}\n\n🗓 *Publicado:* {fecha_str}"

# 🚀 Proceso principal automático
async def main():
    noticias = obtener_noticias_rss()
    titulo, contenido, fecha, _ = random.choice(noticias)
    resumen = formatear_noticia(contenido, fecha)
    imagen = await generar_imagen_gtav()
    await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=imagen, caption=resumen, parse_mode=ParseMode.MARKDOWN)

if __name__ == "__main__":
    asyncio.run(main())
