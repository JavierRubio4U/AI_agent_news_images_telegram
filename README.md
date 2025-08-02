# 🤖 Agente de Noticias IA para Telegram

Este proyecto automatiza el proceso de selección, análisis y publicación de noticias de última hora sobre agentes de inteligencia artificial en un canal de Telegram. Combina un resumen generado por un modelo de lenguaje local (LLM) con una imagen conceptual creada por Stable Diffusion XL.

## 🔧 ¿Qué hace este proyecto?

1.  **Busca noticias relevantes:** Utiliza la API de Búsqueda Personalizada de Google para encontrar las 5 noticias más importantes sobre "agentes de IA" de las últimas 24 horas.

2.  **Evita duplicados:** El script comprueba si la noticia ya ha sido publicada en los últimos 7 días. Si es así, busca la siguiente noticia no publicada en la lista.

3.  **Procesa la noticia:** Envía el titular y el contenido de la noticia a un LLM local (como el modelo `mistral-small`) para:
    * Traducir el texto al español.
    * Generar un resumen breve, un comentario y el título en español.

4.  **Genera una imagen conceptual:** Extrae conceptos clave de la noticia y los utiliza para crear un *prompt* visual detallado para el modelo Stable Diffusion XL. Esto genera una imagen artística y de alta calidad.

5.  **Publica de forma autónoma:** Una vez que la imagen y el resumen están listos, el script publica automáticamente el resultado completo en un canal de Telegram, incluyendo la fuente de la noticia.

## 📁 Estructura de archivos

| Archivo | Descripción |
|---|---|
| `crear_noticia.py` | El script principal que realiza todo el flujo de trabajo de forma automática. |
| `publicadas.json` | Un archivo JSON que el script utiliza para guardar un registro de las noticias ya publicadas en los últimos 7 días. |
| `.gitignore` | Configuración para que Git ignore archivos como `.env` y el cache de `diffusers`. |
| `credenciales_telegram.env` | Archivo donde se guardan las credenciales para las APIs y el bot de Telegram. |

## 📦 Requisitos

* **Python 3.10+** y las bibliotecas necesarias (`requests`, `python-dotenv`, `diffusers`, `torch`, `Pillow`, `python-telegram-bot`).

* **Un LLM corriendo localmente** (se recomienda `mistral-small-3.2-24b-instruct-256k` o similar) con LM Studio o Ollama en `http://localhost:11434`.

* **Modelo Stable Diffusion XL Base 1.0** descargado en tu sistema. La biblioteca `diffusers` lo descargará la primera vez que se ejecute el script.

* **API Key y CX ID de Google Custom Search**.

* **Un bot de Telegram** con su token y un canal configurado.

## ⚙️ Configuración

1.  Crea un archivo llamado `credenciales_telegram.env` en la misma carpeta que el script.

2.  Añade tus credenciales en el archivo:
    ```
    TELEGRAM_TOKEN=tu_token_de_telegram
    TELEGRAM_CHAT_ID=tu_chat_id_o_nombre_de_canal
    GOOGLE_API_KEY=tu_api_key_de_google
    GOOGLE_CX_ID=tu_cx_id_de_google
    ```