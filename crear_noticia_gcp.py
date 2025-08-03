# -*- coding: utf-8 -*-
import os
import json
import time
import torch
import asyncio
import requests
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw
from telegram import Bot
from typing import List, Tuple
from io import BytesIO
from contextlib import contextmanager
from diffusers import StableDiffusionXLPipeline
from fastapi import FastAPI
import asyncio

# Variables desde entorno (ya vienen desde Secret Manager)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_CX_ID = os.environ.get("GOOGLE_CX_ID")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("Faltan TELEGRAM_TOKEN o TELEGRAM_CHAT_ID en las variables de entorno")

bot = Bot(token=TELEGRAM_TOKEN)
ARCHIVO_NOTICIAS = "noticias_publicadas.json"
PIPE = None

MARCAS_PRIORITARIAS = {
    "OpenAI": "a futuristic lab inspired by OpenAI",
    "Google": "a digital workspace inspired by Google",
    "NVIDIA": "an AI chip lab inspired by NVIDIA",
    "Cohere": "a research studio inspired by Cohere",
    "Microsoft": "a sleek corporate building inspired by Microsoft",
    "Apple": "a minimalistic space inspired by Apple",
    "Meta": "a metaverse environment inspired by Meta",
    "Facebook": "a virtual interaction hub inspired by Facebook",
    "Vogue": "a fashion magazine cover inspired by Vogue",
    "Anthropic": "a research-focused lab inspired by Anthropic",
    "Claude": "an AI assistant interface by Anthropic",
    "Gemini": "Google Gemini interface with glowing data streams",
    "GPT-4": "OpenAI neural model core",
    "GPT-4o": "GPT-4 Omni assistant in a tech interface",
    "ChatGPT": "a chat terminal inspired by ChatGPT",
    "Copilot": "an AI assistant UI inspired by Microsoft Copilot",
    "Suno": "a musical waveform studio inspired by Suno AI",
    "Perplexity": "an AI search UI inspired by Perplexity",
    "Mistral": "an open-source AI research space inspired by Mistral",
    "LLaMA": "a Meta AI research interface inspired by LLaMA"
}

app = FastAPI()

@app.get("/")
async def run_news_bot():
    from crear_noticia_core import enviar_noticia  # o directamente importar tu función actual
    await enviar_noticia()
    return {"status": "OK"}

@contextmanager
def medir_duracion(etiqueta):
    inicio = time.time()
    yield
    fin = time.time()
    print(f"⏱ Tiempo en {etiqueta}: {fin - inicio:.2f} segundos")

def contar_tokens_estimada(prompt: str) -> int:
    return len(prompt.replace(",", "").split())

def modelo_llm(prompt: str, model_name: str = "mistral") -> str:
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error al conectar con Ollama: {e}")
        return ""

def obtener_noticias_reales_google(query="latest AI agent news") -> List[Tuple[str, str, datetime, str]]:
    if not GOOGLE_API_KEY or not GOOGLE_CX_ID:
        print("❌ Faltan claves de API.")
        return []

    print(f"Buscando noticias reales en Google con el término: '{query}'")
    url = f"https://www.googleapis.com/customsearch/v1?key={GOOGLE_API_KEY}&cx={GOOGLE_CX_ID}&q={query}&num=5&dateRestrict=d1&lr=lang_en"

    try:
        response = requests.get(url)
        response.raise_for_status()
        search_results = response.json()
        noticias = []
        for item in search_results.get('items', []):
            titulo = item.get('title', '')
            contenido = item.get('snippet', '')
            enlace = item.get('link', '')
            publicado = datetime.now()
            noticias.append((titulo, contenido, publicado, enlace))
        return noticias
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con la API de Google: {e}")
        return []

def url_ya_publicada(url: str) -> bool:
    if not Path(ARCHIVO_NOTICIAS).exists():
        return False
    with open(ARCHIVO_NOTICIAS, "r", encoding="utf-8") as f:
        try:
            urls = json.load(f)
        except json.JSONDecodeError:
            urls = []
    return url in urls

def guardar_url_publicada(url: str):
    if Path(ARCHIVO_NOTICIAS).exists():
        with open(ARCHIVO_NOTICIAS, "r", encoding="utf-8") as f:
            try:
                urls = json.load(f)
            except json.JSONDecodeError:
                urls = []
    else:
        urls = []
    urls.append(url)
    with open(ARCHIVO_NOTICIAS, "w", encoding="utf-8") as f:
        json.dump(urls, f, ensure_ascii=False, indent=2)

def generar_conceptos_visual_llm(texto: str) -> List[str]:
    prompt = (
        "Based on the following news text, extract 4 key visual concepts for an image. "
        "Return them in English, as a comma-separated list, without explanation.\n\n"
        f"News text:\n\"\"\"\n{texto}\n\"\"\""
    )
    respuesta = modelo_llm(prompt)
    conceptos = [c.strip() for c in respuesta.split(',') if c.strip()]
    return conceptos[:4]

def construir_prompt_final(conceptos: List[str], texto_original: str) -> str:
    base = f"A cinematic digital painting of {', '.join(conceptos)}"
    for nombre, decorado in MARCAS_PRIORITARIAS.items():
        if nombre.lower() in texto_original.lower():
            base += f", featuring {decorado}"
            break
    return f"{base}, in the art style of a stylized, highly detailed, digital painting, no text, cinematic lighting"

def generar_imagen_local(prompt: str) -> BytesIO:
    global PIPE
    try:
        if PIPE is None:
            modelo_id = "stabilityai/stable-diffusion-xl-base-1.0"
            PIPE = StableDiffusionXLPipeline.from_pretrained(modelo_id, torch_dtype=torch.float16, variant="fp16")
            PIPE.to("cuda" if torch.cuda.is_available() else "cpu")
        image = PIPE(prompt=prompt, num_inference_steps=25, guidance_scale=6.0, height=512, width=896,
            negative_prompt="text, watermark, blurry, deformed, duplicate, low quality").images[0]
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr
    except Exception as e:
        print(f"❌ Error generando imagen: {e}")
        img = Image.new('RGB', (896, 512), color='gray')
        d = ImageDraw.Draw(img)
        d.text((10, 10), "Error generando imagen", fill=(255, 255, 255))
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr

async def enviar_noticia():
    print("🔍 Buscando noticia relevante en Google News...")
    noticias = obtener_noticias_reales_google()
    noticias = [n for n in noticias if not url_ya_publicada(n[3])]
    if not noticias:
        print("❌ No se encontró ninguna noticia.")
        return
    titulo_noticia, snippet, _, url_noticia = noticias[0]
    texto = f"{titulo_noticia}. {snippet}"

    with medir_duracion("generar resumen"):
        resumen = modelo_llm(
            "Resume esta noticia en tres partes separadas por nueva línea:\n"
            "1. TÍTULO: (máximo 15 palabras)\n"
            "2. RESUMEN: (1–2 frases claras)\n"
            "3. COMENTARIO: (análisis de impacto o contexto)\n\n"
            f"{texto}"
        )
    print("🧠 Resumen generado:\n", resumen)

    with medir_duracion("extraer conceptos"):
        conceptos = generar_conceptos_visual_llm(texto)
    print("🔑 Conceptos visuales extraídos:", conceptos)

    with medir_duracion("generar imagen"):
        prompt = construir_prompt_final(conceptos, texto)
        print("🎨 Prompt visual final:\n", prompt)
        print("🧮 Tokens estimados para CLIP:", contar_tokens_estimada(prompt), "/ 77")
        imagen = generar_imagen_local(prompt)

    texto_telegram = (
        f"{resumen}\n\n"
        f"🗓 *Publicado:* {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        f"🔗 Fuente: {url_noticia}"
    )

    with medir_duracion("enviar a Telegram"):
        await bot.send_photo(
            chat_id=TELEGRAM_CHAT_ID,
            photo=imagen,
            caption=texto_telegram,
            parse_mode="Markdown"
        )

    guardar_url_publicada(url_noticia)

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("crear_noticia_gcp:app", host="0.0.0.0", port=port)


