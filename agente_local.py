import os
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
import re

# 📁 Cargar credenciales desde .env
load_dotenv(dotenv_path=Path(__file__).resolve().parent / "credenciales_telegram.env")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# 📤 Bot de Telegram
bot = Bot(token=TELEGRAM_TOKEN)

# 🧠 Función que llama a tu modelo LLM local
def modelo_llm(prompt: str) -> str:
    url = "http://localhost:11434/v1/completions"
    response = requests.post(url, json={
        "model": "mistralai/mistral-7b-instruct-v0.3",
        "prompt": prompt,
        "max_tokens": 500,
        "temperature": 0.7
    })

    try:
        respuesta_json = response.json()
        if "choices" not in respuesta_json or len(respuesta_json["choices"]) == 0:
            print("❌ La respuesta del modelo no contiene el contenido esperado:")
            print(respuesta_json)
            raise KeyError("Falta 'choices[0].text' en la respuesta del modelo")
        return respuesta_json["choices"][0]["text"]
    except Exception as e:
        print(f"❌ Error procesando la respuesta del modelo: {e}")
        raise


def extraer_keywords(texto: str) -> str:
    # Extraer nombres propios (palabras con mayúscula no al inicio de frase)
    nombres = re.findall(r'(?<!\.\s)(?<!^)(?<!\n)(?<!\")\b[A-Z][a-zA-Z]{2,}\b', texto)

    # Extraer palabras clave: inteligencia, datos, IA, etc.
    palabras_clave = re.findall(r'\b(inteligencia|artificial|datos|transformación|empresa|optimiza|IA|modelo|código|sistema|automatiza|ciudad|tecnología|neón|cyberpunk|robot|futurista)\b', texto, flags=re.IGNORECASE)

    # Quitar duplicados y limitar a 5
    todas = list(dict.fromkeys(nombres + palabras_clave))[:5]

    # Convertir a una frase separada por comas para usar en el prompt
    return ', '.join(todas)

# 🎨 Generar imagen estilo GTA V sin letras visibles
async def generar_imagen_gtav(texto_resumen: str) -> BytesIO:
    palabras = extraer_keywords(texto_resumen)
    prompt_visual = f"GTA V style, cinematic, {palabras}"
    url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt_visual)}"
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr


# 📰 Formatear la noticia
def formatear_noticia(noticia_completa: str, fecha_publicacion: datetime) -> str:
    prompt = f"""
Analiza la siguiente noticia y responde separando claramente tres secciones:

1. TÍTULO: Un titular corto (máx 15 palabras) que resuma lo más importante.
2. RESUMEN: Qué ha pasado, explicado brevemente (máx 5 líneas).
3. COMENTARIO: Breve análisis del impacto, posibles consecuencias o contexto adicional (máx 8 líneas).

Noticia original:
\"\"\"{noticia_completa}\"\"\"
"""

    respuesta = modelo_llm(prompt).strip()
    fecha_str = fecha_publicacion.strftime("%d/%m/%Y %H:%M")
    mensaje = f"{respuesta}\n\n🗓 *Publicado:* {fecha_str}"
    return mensaje

# 🔎 Obtener noticias desde RSS de VentureBeat
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

# 🧪 Ejecutar el flujo completo
if __name__ == "__main__":
    noticias = obtener_noticias_rss()
    print("🧠 Noticias IA destacadas:\n")
    for i, (titulo, _, fecha, _) in enumerate(noticias, 1):
        print(f"{i}. {titulo} ({fecha.strftime('%d/%m/%Y')})")

    seleccion = int(input("\nElige una noticia (1-3): "))
    _, contenido, fecha, enlace = noticias[seleccion - 1]

    mensaje = formatear_noticia(contenido, fecha)
    print("\n🧠 Resumen generado:\n", mensaje)

    async def main():
        imagen = await generar_imagen_gtav(mensaje)
        await bot.send_photo(chat_id=TELEGRAM_CHAT_ID, photo=imagen, caption=mensaje, parse_mode=ParseMode.MARKDOWN)

    asyncio.run(main())

