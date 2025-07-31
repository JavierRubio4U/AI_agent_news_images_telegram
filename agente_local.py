import os
from datetime import datetime
from pathlib import Path
import requests
import feedparser
from bs4 import BeautifulSoup
from telegram import Bot
from dotenv import load_dotenv

# 📁 Cargar credenciales
load_dotenv(dotenv_path=Path(__file__).resolve().parent / "credenciales_telegram.env")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(token=TELEGRAM_TOKEN)

# 🔍 Noticias IA desde VentureBeat (RSS)
def obtener_noticias_ia():
    feed_url = "https://feeds.feedburner.com/venturebeat/SZYF"
    feed = feedparser.parse(feed_url)
    noticias = []
    for entrada in feed.entries[:3]:  # Solo las 3 primeras
        noticias.append({
            "titulo": entrada.title,
            "link": entrada.link
        })
    return noticias

# 📥 Extraer texto de una noticia
def extraer_contenido_noticia(url: str) -> str:
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(resp.content, "html.parser")
    parrafos = soup.select("p")
    texto = "\n".join(p.get_text(strip=True) for p in parrafos if len(p.get_text(strip=True)) > 50)
    return texto[:3000]  # Máximo 3000 caracteres

# 🧠 Llamada al modelo LLM local
def modelo_llm(prompt: str) -> str:
    url = "http://localhost:11434/v1/completions"
    response = requests.post(url, json={
        "model": "mistralai/mistral-7b-instruct-v0.3",
        "prompt": prompt,
        "max_tokens": 500,
        "temperature": 0.7
    })
    data = response.json()
    if "choices" not in data or len(data["choices"]) == 0:
        raise ValueError("❌ Error: respuesta inesperada del modelo")
    return data["choices"][0]["text"].strip()

# 📄 Formatear resumen LLM
def formatear_noticia(noticia_completa: str, fecha_publicacion: datetime) -> str:
    prompt = f"""
Analiza la siguiente noticia y responde separando claramente tres secciones:

1. TÍTULO: Un titular corto (máx 15 palabras) que resuma lo más importante.
2. RESUMEN: Qué ha pasado, explicado brevemente (máx 5 líneas).
3. COMENTARIO: Breve análisis del impacto, posibles consecuencias o contexto adicional (máx 8 líneas).

Noticia original:
\"\"\"{noticia_completa}\"\"\"
"""
    resumen = modelo_llm(prompt)
    fecha_str = fecha_publicacion.strftime("%d/%m/%Y %H:%M")
    return f"{resumen}\n\n🗓 *Publicado:* {fecha_str}"

import asyncio

# 📤 Enviar a Telegram (modo async)
async def enviar_noticia_a_telegram(texto_resumen: str):
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=texto_resumen, parse_mode="Markdown")

# 🚀 Main interactivo
async def main():
    noticias = obtener_noticias_ia()
    print("\n🧠 Noticias IA destacadas:\n")
    for i, noticia in enumerate(noticias, start=1):
        print(f"{i}. {noticia['titulo']}")

    seleccion = int(input("\nElige una noticia (1-3): ")) - 1
    noticia = noticias[seleccion]
    print(f"\n🔗 Procesando: {noticia['link']}")
    texto = extraer_contenido_noticia(noticia["link"])
    resumen = formatear_noticia(texto, datetime.now())
    await enviar_noticia_a_telegram(resumen)

if __name__ == "__main__":
    asyncio.run(main())
