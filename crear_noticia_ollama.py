# -*- coding: utf-8 -*-
import os
import json
import time
import torch
import asyncio
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image, ImageDraw
from telegram import Bot
from typing import List, Tuple
from io import BytesIO
from contextlib import contextmanager
from diffusers import StableDiffusionXLPipeline
import re

# Cargar credenciales
load_dotenv(dotenv_path=Path(__file__).resolve().parent / "credenciales_telegram.env")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX_ID = os.getenv("GOOGLE_CX_ID")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("Faltan TELEGRAM_TOKEN o TELEGRAM_CHAT_ID en el .env")

bot = Bot(token=TELEGRAM_TOKEN)
ARCHIVO_NOTICIAS = "noticias_publicadas.json"

MARCAS_PRIORITARIAS = {
    "OpenAI": "a futuristic street scene with a glowing OpenAI billboard",
    "Google": "a cyberpunk plaza with a luminous Google sign",
    "NVIDIA": "a digital cityscape featuring an NVIDIA holographic ad",
    "Microsoft": "a tech-themed avenue with a Microsoft neon billboard",
    "Apple": "a sleek street with a floating Apple logo in the sky",
    "Meta": "a metaverse city intersection with Meta brand holograms",
    "Facebook": "an urban scene with Facebook posts on digital screens",
    "Anthropic": "a night city view with a glowing Anthropic lab sign",
    "Claude": "a futuristic city terminal showing Claude's interface",
    "Gemini": "a skyline with Gemini glowing letters above buildings",
    "GPT-4": "a digital future alley with GPT-4 visual core above",
    "GPT-4o": "an open tech square with GPT-4 Omni AI screen",
    "ChatGPT": "a modern AI helpdesk in a public urban plaza",
    "Copilot": "a cyber city with a drone projecting Copilot logo",
    "Suno": "a music-themed neon district with Suno AI waves visible",
    "Perplexity": "a futuristic alleyway with a Perplexity search UI",
    "Mistral": "an open-source AI conference outside with Mistral posters",
    "LLaMA": "a digital jungle plaza featuring LLaMA virtual ads",
    "Vogue": "a fashion-forward avenue with a massive Vogue screen",
}

PIPE = None

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

# 🔎 Obtener noticias desde una búsqueda de Google (implementación real)
def obtener_noticias_reales_google(query="latest AI agent news") -> List[Tuple[str, str, datetime, str]]:
    """
    Realiza una búsqueda de Google para obtener noticias relevantes sobre IA y extrae la información.
    """
    if not GOOGLE_API_KEY or not GOOGLE_CX_ID:
        print("❌ No se encontraron GOOGLE_API_KEY o GOOGLE_CX_ID en el archivo .env.")
        print("Usando resultados simulados para la demostración.")
        simulated_results = [
            {"title": "AI in the workplace: what employees need to excel with intelligent agents", "snippet": "A new report from Microsoft details the future of AI in business, emphasizing the need for skilled employees to work alongside intelligent agents and Copilot...", "link": "https://www.example-news.com/microsoft-ai-agent", "date": "2025-08-02"},
            {"title": "OpenAI's latest breakthrough: a reasoning agent that learns from its mistakes", "snippet": "OpenAI's new agent can now self-correct its actions, a significant step forward in autonomous AI and self-improving systems...", "link": "https://www.another-news-site.com/openai-web-agent", "date": "2025-08-01"},
            {"title": "DeepMind researcher on the future of multi-modal AI", "snippet": "A key researcher from DeepMind shares insights into the development of multi-modal AI and its potential impact on various industries...", "link": "https://www.ai-finance-news.com/deep-mind-research", "date": "2025-07-31"},
            {"title": "Google's new agent-based model for climate science", "snippet": "Google Research introduces a novel AI agent that simulates climate change scenarios to predict future ecological trends...", "link": "https://www.google-research.com/ai-agents-paper", "date": "2025-07-30"},
            {"title": "The new AI arms race: tech giants compete for top talent with massive salaries", "snippet": "Tech companies like Meta and Google are offering unprecedented salaries and benefits to attract the best AI talent, with offers reaching into the millions...", "link": "https://www.infobae.com/america/the-new-york-times/2025/08/01/los-investigadores-en-ia-estan-negociando-paquetes-salariales-de-250-millones-de-dolares-justo-como-las-estrellas-de-la-nba/", "date": "2025-07-29"}
        ]
        
        noticias_simuladas = []
        for resultado in simulated_results:
            titulo = resultado['title']
            contenido = resultado['snippet']
            publicado = datetime.strptime(resultado['date'], "%Y-%m-%d")
            enlace = resultado['link']
            noticias_simuladas.append((titulo, contenido, publicado, enlace))
        return noticias_simuladas

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
    conceptos_limpios = [c.strip() for c in respuesta.split(',') if c.strip()]

    correcciones = {
        "Gemini": "Google's AI model represented with holographic data",
        "Claude": "Anthropic's AI assistant in a digital interface",
        "ChatGPT": "OpenAI's chatbot interface",
        "GPT-4": "OpenAI neural network engine",
        "GPT-4o": "GPT-4 Omni visual assistant",
        "Perplexity": "AI search engine with abstract graphs",
        "Mistral": "open-source AI model with algorithmic patterns"
    }

    conceptos_corregidos = []
    for c in conceptos_limpios:
        limpio = c.strip().strip('"')
        corregido = correcciones.get(limpio, limpio)
        if corregido.lower() not in [k.lower() for k in MARCAS_PRIORITARIAS.keys()]:
            conceptos_corregidos.append(corregido)
    
    conceptos_limpios = [re.sub(r'^\d+[\.\)]\s*', '', c.strip()) for c in respuesta.split(',') if c.strip()]

    return conceptos_corregidos[:4]

def construir_prompt_final(conceptos: List[str], texto_original: str) -> str:
    base = f"A cinematic digital painting of {', '.join(conceptos)}"

    personas = {
        "Sam Altman": "Sam Altman",
        "Elon Musk": "Elon Musk",
        "Sundar Pichai": "Sundar Pichai",
        "Jensen Huang": "Jensen Huang",
        "Mark Zuckerberg": "Mark Zuckerberg",
        "Tim Cook": "Tim Cook"
    }

    texto_lower = texto_original.lower()
    for nombre, desc in personas.items():
        if nombre.lower() in texto_lower and all(nombre.lower() not in c.lower() for c in conceptos):
            base += f", with a portrait of {desc}"
            print(f"🧑‍🎨 Persona añadida al prompt: {desc}")
            break

    for nombre, decorado in MARCAS_PRIORITARIAS.items():
        if nombre.lower() in texto_lower:
            base += f", featuring {decorado}"
            print(f"🏢 Decorado añadido al prompt: {decorado}")
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
    # Filtrar noticias ya publicadas
    noticias = [n for n in noticias if not url_ya_publicada(n[3])]


    if not noticias:
        print("❌ No se encontró ninguna noticia.")
        return

    # Elegimos la primera noticia (puedes implementar lógica para evitar repetidas)
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
            parse_mode="Markdown")

    guardar_url_publicada(url_noticia)

if __name__ == "__main__":
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(enviar_noticia())
