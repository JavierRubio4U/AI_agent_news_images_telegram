import os
import re
import time
import torch
import asyncio
import requests
import feedparser
from io import BytesIO
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image
from telegram import Bot
from telegram.constants import ParseMode
from diffusers import StableDiffusionPipeline

# 📁 Cargar credenciales
load_dotenv(dotenv_path=Path(__file__).resolve().parent / "credenciales_telegram.env")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(token=TELEGRAM_TOKEN)

# 🧠 Consulta a tu LLM local
def modelo_llm(prompt: str) -> str:
    url = "http://localhost:11434/v1/completions"
    response = requests.post(url, json={
        "model": "mistralai/mistral-7b-instruct-v0.3",
        "prompt": prompt,
        "max_tokens": 500,
        "temperature": 0.7
    })
    return response.json()["choices"][0]["text"].strip()

# 🔎 Extraer 5 palabras clave y generar prompt visual
def construir_prompt_visual(palabras: list[str]) -> str:
    persona = ""
    marca = ""
    palabras_clave = []

    for palabra in palabras:
        if palabra.startswith("PERSONA::"):
            persona = palabra.replace("PERSONA::", "").strip()
        elif palabra.startswith("MARCA::"):
            marca = palabra.replace("MARCA::", "").strip()
        else:
            palabras_clave.append(palabra)

    temas = ", ".join(palabras_clave)
    partes = [f"A cinematic digital painting featuring themes of {temas}"]
    if persona:
        partes.append(f"with {persona}")
    if marca:
        partes.append(f"and branding of {marca}")
    partes.append("stylized, highly detailed, concept art, without text.")
    return ", ".join(partes)


# 🔑 Extraer 5 palabras clave importantes del resumen
def extraer_keywords_llm(texto: str) -> list[str]:
    # Listas ampliadas de personas y marcas relevantes en IA
    personas_ia = [
        "Sam Altman", "Elon Musk", "Sundar Pichai", "Demis Hassabis", "Mark Zuckerberg",
        "Yann LeCun", "Geoffrey Hinton", "Emad Mostaque", "Ilya Sutskever", "Andrew Ng",
        "Fei-Fei Li", "Dario Amodei", "Richard Socher", "Jim Fan", "Jensen Huang"
    ]

    marcas_ia = [
        "OpenAI", "Google", "DeepMind", "Anthropic", "Meta", "xAI", "Stability AI", "Runway",
        "Mistral", "Cohere", "Hugging Face", "Midjourney", "Inflection AI", "Apple", "Amazon",
        "NVIDIA", "Microsoft", "Gemini", "Claude", "LLaMA", "GPT", "ChatGPT", "Bard", "Copilot"
    ]

    # Consulta al modelo local
    prompt = (
        "A partir del siguiente texto, extrae exactamente 5 palabras clave separadas por comas, "
        "sin explicaciones ni frases adicionales.\n\n"
        f"{texto}"
    )
    respuesta = modelo_llm(prompt)
    print(f"\n🧪 LLM crudo:\n{respuesta!r}")

    # Limpieza robusta del texto antes del split
    respuesta_limpia = respuesta.strip()

    # Eliminar saltos de línea, encabezados, emojis o adornos
    respuesta_limpia = re.sub(r"(?i)(palabras clave|🔑|✏️|[*:_-])+[:]*", "", respuesta_limpia)
    respuesta_limpia = re.sub(r"\s+", " ", respuesta_limpia)  # quita saltos y tabuladores

    print(f"\n🧹 LLM limpio:\n{respuesta_limpia!r}")

    # Separar por comas y limpiar espacios
    palabras = []
    for palabra in respuesta_limpia.split(","):
        palabra_limpia = palabra.strip()
        # Elimina si empieza con solo un número aislado
        palabra_limpia = re.sub(r"^\d+\s*", "", palabra_limpia)
        if palabra_limpia:
            palabras.append(palabra_limpia)

    print(f"\n🔍 Palabras clave extraídas (post-split):\n{palabras}")

    # Extraer nombres conocidos del texto original (por si el modelo los omite)
    texto_lower = texto.lower()
    entidades_extra = []

    for nombre in personas_ia + marcas_ia:
        if nombre.lower() in texto_lower and nombre not in palabras:
            entidades_extra.append(nombre)

    palabras.extend(entidades_extra)

    # Eliminar duplicados manteniendo el orden
    palabras_finales = []
    for p in palabras:
        if p not in palabras_finales:
            palabras_finales.append(p)

    # Completar si hay menos de 5
    while len(palabras_finales) < 5:
        palabras_finales.append("IA")

    return palabras_finales[:5]


# 🎨 Generar imagen con modelo local (Stable Diffusion)
def generar_imagen_local(prompt: str) -> BytesIO:
    print(f"🎨 Prompt visual final: \"{prompt}\"")
    start = time.time()
    modelo_id = "sd-legacy/stable-diffusion-v1-5"
    pipe = StableDiffusionPipeline.from_pretrained(modelo_id, torch_dtype=torch.float16)
    pipe = pipe.to("cuda" if torch.cuda.is_available() else "cpu")

    image = pipe(
        prompt=prompt,
        num_inference_steps=25,
        guidance_scale=10.0,
        height=512,
        width=896,
        negative_prompt="text, letters, watermark, signature, subtitles, captions, blurry, distorted, extra limbs, low quality, multiple heads, duplicate faces"
    ).images[0]

    print(f"🕒 Generada en {time.time() - start:.2f} segundos")
    img_byte_arr = BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

# 📰 Formatear resumen de la noticia
def formatear_noticia(texto: str, fecha_publicacion: datetime) -> str:
    prompt = (
        "Analiza la siguiente noticia y responde separando claramente tres secciones:\n"
        "1. TÍTULO: Un titular corto (máx 15 palabras).\n"
        "2. RESUMEN: Qué ha pasado (máx 5 líneas).\n"
        "3. COMENTARIO: Análisis del impacto o contexto (máx 8 líneas).\n\n"
        f"Noticia original:\n\"\"\"\n{texto}\n\"\"\""
    )
    resultado = modelo_llm(prompt)
    fecha_str = fecha_publicacion.strftime("%d/%m/%Y %H:%M")
    return f"{resultado}\n\n🗓 *Publicado:* {fecha_str}"


# 🔎 Obtener noticias desde RSS
def obtener_noticias_rss(feed_url="https://venturebeat.com/feed/"):
    feed = feedparser.parse(feed_url)
    noticias = []
    for entrada in feed.entries[:5]:
        titulo = entrada.title
        enlace = entrada.link
        publicado = datetime(*entrada.published_parsed[:6])
        contenido = entrada.summary
        noticias.append((titulo, contenido, publicado, enlace))
    return noticias


# ▶️ Flujo completo
async def enviar():
    noticias = obtener_noticias_rss()
    print("🧠 Noticias IA destacadas:\n")
    for i, (titulo, _, fecha, _) in enumerate(noticias, 1):
        print(f"{i}. {titulo} ({fecha.strftime('%d/%m/%Y')})")

    seleccion = int(input("\nElige una noticia (1-5): "))
    _, contenido, fecha, enlace = noticias[seleccion - 1]

    resumen = formatear_noticia(contenido, fecha)
    print("\n🧠 Resumen generado:\n", resumen)

    palabras = extraer_keywords_llm(resumen)
    print(f"\n🔑 Palabras clave extraídas: {palabras}")

    prompt = construir_prompt_visual(palabras)
    imagen = generar_imagen_local(prompt)

    await bot.send_photo(
        chat_id=TELEGRAM_CHAT_ID,
        photo=imagen,
        caption=resumen,
        parse_mode=ParseMode.MARKDOWN
    )


import asyncio
import sys

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*NoneType.*")

    try:
        asyncio.run(enviar())
    except KeyboardInterrupt:
        print("⛔ Cancelado por el usuario")


