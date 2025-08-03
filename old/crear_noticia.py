# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import time
import torch
import asyncio
import requests
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from PIL import Image, ImageDraw
from telegram import Bot
from diffusers import StableDiffusionXLPipeline
from typing import List, Tuple
from io import BytesIO

# 📁 Cargar credenciales desde el archivo .env (para uso local)
load_dotenv(dotenv_path=Path(__file__).resolve().parent / "credenciales_telegram.env")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
# Para la API de Google Custom Search
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX_ID = os.getenv("GOOGLE_CX_ID")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    raise ValueError("El TOKEN de Telegram o el CHAT_ID no están configurados en el archivo .env")

# Inicialización del bot de Telegram
bot = Bot(token=TELEGRAM_TOKEN)

# 🧠 Consulta a tu LLM local (Ollama)
def modelo_llm(prompt: str, model_name: str = "mistral") -> str:
    """
    Consulta a un modelo de lenguaje local a través de la API de Ollama.
    """
    url = "http://localhost:11434/api/chat"
    
    payload = {
        "model": model_name,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False
    }
    
    start_time = time.time()
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        end_time = time.time()
        print(f"🕒 LLM (modelo_llm) tardó {end_time - start_time:.2f} segundos.")
        return response.json()["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con el LLM local: {e}")
        return ""

# 🔎 Generar los conceptos clave para el prompt visual con el LLM
def generar_conceptos_visual_llm(texto_noticia: str) -> List[str]:
    """
    Pide al LLM que extraiga de 2 a 3 conceptos clave y los devuelva en inglés.
    """
    start_time = time.time()
    prompt_base = (
        "Based on the following news text, extract 3 key concepts for an image. "
        "Return them in a simple comma-separated list, in English, without explanations or extra phrases. "
        "Example format: 'futuristic office, data visualization, AI branding'.\n\n"
        "News text:\n\"\"\"\n{texto_noticia}\n\"\"\""
    )

    respuesta = modelo_llm(prompt_base)
    
    if not respuesta:
        print("❌ The LLM did not return any concepts. Using default concepts.")
        return ["technology", "artificial intelligence", "innovation"]

    conceptos_limpios = [c.strip() for c in respuesta.split(',') if c.strip()]
    end_time = time.time()
    print(f"🕒 Extracción de conceptos tardó {end_time - start_time:.2f} segundos.")
    return conceptos_limpios[:3]

# 🖼️ Construir el prompt visual final
def construir_prompt_final(conceptos: List[str], texto_original: str) -> str:
    """
    Combina los conceptos clave, el estilo y las entidades para un prompt final conciso.
    """
    prompt_base = f"A cinematic digital painting of {', '.join(conceptos)}"

    personas_ia = {
        "Sam Altman": "a visionary leader on a stage",
        "Elon Musk": "a tech mogul in a futuristic setting",
        "Sundar Pichai": "a CEO in a corporate environment",
        "Jensen Huang": "a leader with a leather jacket, surrounded by AI hardware",
        "Mark Zuckerberg": "a tech CEO discussing major deals"
    }
    marcas_ia = {
        "OpenAI": "the OpenAI logo and branding",
        "Google": "the Google logo and branding",
        "NVIDIA": "NVIDIA branding and graphics",
        "Cohere": "the Cohere logo and branding",
        "Microsoft": "the Microsoft logo and branding"
    }

    texto_lower = texto_original.lower()
    
    # Añadir persona
    for nombre, descripcion in personas_ia.items():
        if nombre.lower() in texto_lower:
            prompt_base = f"{prompt_base}, with a portrait of {descripcion}"
            break
    
    # Añadir marca
    for nombre, descripcion in marcas_ia.items():
        if nombre.lower() in texto_lower:
            prompt_base = f"{prompt_base}, featuring {nombre} branding"
            break

    # Añadir el estilo final
    return f"{prompt_base}, highly detailed, cinematic digital painting, without text, beautiful lighting."


# 🎨 Generar imagen con modelo local (Stable Diffusion)
def generar_imagen_local(prompt: str) -> BytesIO:
    """
    Genera una imagen usando el modelo Stable Diffusion XL en local.
    """
    print(f"\n🎨 Prompt visual final: \n\n{prompt}\n")
    start_time = time.time()
    try:
        modelo_id = "stabilityai/stable-diffusion-xl-base-1.0"
        pipe = StableDiffusionXLPipeline.from_pretrained(
            modelo_id, 
            torch_dtype=torch.float16,
        )
        pipe.to("cuda" if torch.cuda.is_available() else "cpu")

        print(f"✅ Se ha cargado el modelo: {modelo_id}")
        print("💡 Empezando la generación de la imagen...")

        image = pipe(
            prompt=prompt,
            num_inference_steps=25,
            guidance_scale=7.5,
            height=512,
            width=896,
            negative_prompt="text, letters, watermark, signature, subtitles, captions, blurry, distorted, extra limbs, bad hands, deformed faces, low quality, multiple heads, duplicate faces, poorly drawn, poorly rendered, ugly, anatomical malformation, person"
        ).images[0]
        
        end_time = time.time()
        print(f"🕒 Generada en {end_time - start_time:.2f} segundos")
        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr

    except Exception as e:
        print(f"Error al generar la imagen con Stable Diffusion: {e}")
        img = Image.new('RGB', (896, 512), color='gray')
        d = ImageDraw.Draw(img)
        d.text((10, 10), "Error al generar la imagen", fill=(255, 255, 255))
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr

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

# 💾 Persistencia de noticias publicadas
def cargar_noticias_publicadas() -> List[dict]:
    """
    Carga las noticias publicadas del archivo JSON. Si no existe, devuelve una lista vacía.
    También limpia las noticias de más de 7 días.
    """
    archivo = Path("publicadas.json")
    if not archivo.exists():
        return []

    try:
        with open(archivo, 'r') as f:
            noticias = json.load(f)
        
        hace_7_dias = datetime.now() - timedelta(days=7)
        noticias_filtradas = [
            n for n in noticias 
            if datetime.fromisoformat(n['fecha']) > hace_7_dias
        ]
        
        return noticias_filtradas
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error al cargar el archivo de noticias publicadas: {e}")
        return []

def guardar_noticia_publicada(noticia: dict):
    """
    Guarda una noticia en el archivo JSON.
    """
    archivo = Path("publicadas.json")
    noticias = cargar_noticias_publicadas()
    noticias.append(noticia)
    
    try:
        with open(archivo, 'w') as f:
            json.dump(noticias, f, indent=4)
    except IOError as e:
        print(f"Error al guardar el archivo de noticias publicadas: {e}")
        
# 📰 Formatear resumen de la noticia
def formatear_noticia(titulo_en: str, contenido_en: str, fecha_publicacion: datetime) -> str:
    """
    Usa el LLM local para resumir, comentar y traducir una noticia en un formato específico.
    """
    start_time = time.time()
    prompt = (
        "Analiza el siguiente texto en inglés y responde separando claramente tres secciones, en español:\n"
        "1. TÍTULO: Un titular corto y llamativo (máx 15 palabras).\n"
        "2. RESUMEN: Qué ha pasado (máx 5 líneas).\n"
        "3. COMENTARIO: Análisis del impacto o contexto (máx 8 líneas).\n\n"
        f"Texto original:\n\"\"\"\n{titulo_en}\n{contenido_en}\n\"\"\""
    )
    resultado = modelo_llm(prompt)
    if not resultado:
        return "❌ No se pudo generar el resumen de la noticia."
    
    fecha_str = fecha_publicacion.strftime("%d/%m/%Y %H:%M")
    end_time = time.time()
    print(f"🕒 Formateo de noticia tardó {end_time - start_time:.2f} segundos.")
    return f"{resultado}\n\n🗓 *Publicado:* {fecha_str}"


# ▶️ Flujo completo del bot de noticias
async def enviar_noticia():
    """
    Función principal que ejecuta todo el flujo: obtiene noticias,
    procesa la primera no publicada, genera resumen e imagen y publica en Telegram.
    """
    noticias_publicadas = cargar_noticias_publicadas()
    enlaces_publicados = {n['enlace'] for n in noticias_publicadas}

    noticias = obtener_noticias_reales_google()
    if not noticias:
        print("No se encontraron noticias. El script finalizará.")
        return

    noticia_para_publicar = None
    for titulo, contenido, fecha, enlace in noticias:
        if enlace not in enlaces_publicados:
            noticia_para_publicar = {
                "titulo": titulo,
                "contenido": contenido,
                "fecha": fecha,
                "enlace": enlace
            }
            print(f"\n✅ Se ha encontrado una noticia nueva para publicar: '{titulo}'")
            break
    
    if not noticia_para_publicar:
        print("\nℹ️ No se encontraron noticias nuevas en la búsqueda. El script finalizará.")
        return

    titulo_en = noticia_para_publicar['titulo']
    contenido_en = noticia_para_publicar['contenido']
    fecha = noticia_para_publicar['fecha']
    enlace = noticia_para_publicar['enlace']

    print("\n⏳ Generando resumen...")
    resumen = formatear_noticia(titulo_en, contenido_en, fecha)
    print("\n🧠 Resumen generado:\n", resumen)
    
    print("\n⏳ Creando prompt visual a partir de la noticia completa...")
    conceptos = generar_conceptos_visual_llm(contenido_en)
    print(f"\n🔑 Conceptos clave extraídos: {', '.join(conceptos)}\n")
    
    print("\n⏳ Construyendo prompt final para Stable Diffusion...")
    prompt_final = construir_prompt_final(conceptos, contenido_en)

    imagen = generar_imagen_local(prompt_final)

    try:
        print("\n🚀 Enviando mensaje a Telegram...")
        caption = f"{resumen}\n\nFuente: {enlace}"
        await bot.send_photo(
            chat_id=TELEGRAM_CHAT_ID,
            photo=imagen,
            caption=caption,
            parse_mode='Markdown'
        )
        print("✅ Mensaje enviado con éxito.")
        
        noticia_guardar = {
            'titulo': noticia_para_publicar['titulo'],
            'enlace': enlace,
            'fecha': datetime.now().isoformat()
        }
        guardar_noticia_publicada(noticia_guardar)
        
    except Exception as e:
        print(f"❌ Error al enviar el mensaje a Telegram: {e}")


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*NoneType.*")

    try:
        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        asyncio.run(enviar_noticia())
    except KeyboardInterrupt:
        print("⛔ Cancelado por el usuario")
