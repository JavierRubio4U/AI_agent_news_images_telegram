# 🤖 Proyecto de Agentes de IA para Telegram

Este proyecto unificado consta de dos bots de Telegram que interactúan con modelos de lenguaje y generación de imágenes locales para automatizar y facilitar tareas relacionadas con la inteligencia artificial.

## 🔧 ¿Qué hace este proyecto?

El proyecto tiene dos componentes principales:

### 1. Bot de Noticias (Automatizado)

* **Busca noticias relevantes:** Utiliza la API de Búsqueda Personalizada de Google para encontrar las 5 noticias más importantes sobre "agentes de IA" de las últimas 24 horas.

* **Evita duplicados:** El script comprueba si la noticia ya ha sido publicada en los últimos 7 días.

* **Procesa la noticia:** Envía el titular y el contenido de la noticia a un LLM local (`mistral-small`) para traducirlo al español, generar un resumen y un comentario.

* **Genera una imagen conceptual:** Crea una imagen artística de alta calidad con Stable Diffusion XL basándose en los conceptos clave de la noticia.

* **Publica de forma autónoma:** Publica el resultado en un canal de Telegram, incluyendo la fuente de la noticia.

### 2. Bot de Chat (Interactivo)

* **Responde en tiempo real:** Un segundo bot te permite interactuar en un chat privado de Telegram con tu LLM local (`mistral-small`).

* **Gestión de peticiones:** Utiliza un semáforo de concurrencia para gestionar las peticiones, asegurando que el modelo no se sature.

* **Herramienta de desarrollo:** Ideal para probar y depurar el LLM, o simplemente para tener un asistente personal de IA en tu chat.

## 📁 Estructura de archivos

| **Archivo** | **Descripción** |
|---|---|
| `crear_noticia.py` | Script principal para el bot de noticias autónomo. |
| `telegram_message_bot.py` | Script para el bot de chat interactivo. |
| `publicadas.json` | Archivo JSON que el bot de noticias usa para evitar duplicados. |
| `.gitignore` | Configuración para que Git ignore archivos sensibles como `.env` y el cache de `diffusers`. |
| `credenciales_telegram.env` | Archivo donde se guardan las credenciales para ambas funcionalidades. |

## 📦 Requisitos

* **Python 3.10+** y las bibliotecas necesarias (`requests`, `python-dotenv`, `diffusers`, `torch`, `Pillow`, `python-telegram-bot`).

* **Un LLM corriendo localmente** (se recomienda `mistral-small-3.2-24b-instruct-256k` o similar) con LM Studio u Ollama en `http://localhost:11434`.

* **Modelo Stable Diffusion XL Base 1.0** descargado en tu sistema.

* **API Key y CX ID de Google Custom Search**.

* **Un bot de Telegram** con su token y un canal para el bot de noticias.

## ⚙️ Configuración

1.  Crea un archivo llamado `credenciales_telegram.env` en la misma carpeta.

2.  Añade tus credenciales en el archivo:
    ```
    TELEGRAM_TOKEN=tu_token_de_telegram
    TELEGRAM_CHAT_ID=tu_chat_id_o_nombre_de_canal
    GOOGLE_API_KEY=tu_api_key_de_google
    GOOGLE_CX_ID=tu_cx_id_de_google
    ```

## 🚀 Pruébalo

Puedes ver el resultado del bot de noticias en acción en el canal de Telegram: [https://t.me/agente_libre](https://t.me/agente_libre)