# 🧠 NoticiasBot - Generador de Noticias con Imagen AI

Este proyecto genera y publica automáticamente noticias sobre IA con una imagen ilustrativa generada por modelos open source. Puede ejecutarse en local con Ollama o desplegarse en una VM con GPU en Google Cloud Platform (GCP).

---
## 📲 Canal de Telegram (usuario)

Puedes ver las publicaciones generadas por este bot en tiempo real en el canal de Telegram:

👉 [t.me/agente_libre](https://t.me/agente_libre) *(reemplaza con el canal real si es otro)*


## 🚀 Cómo probarlo rápidamente

### ▶️ En GCP (modo nube con GPU)

```bat
REM Ejecutar desde tu PC
start.bat

REM Dentro de la VM
python3 crear_noticia_gcp.py
```

### 💻 En local (modo Ollama)

```bash
python crear_noticia_ollama.py
```

> Requiere Ollama y tener un modelo como `mistral` funcionando localmente.

---

## 📁 Estructura del proyecto

```plaintext
noticiasbot/
├── cloud/
│   ├── crear_noticia_gcp.py          # Bot completo con FastAPI para ejecutar en GCP
│   ├── requirements.txt              # Dependencias sin torch (instalar con CUDA manual)
│   ├── start.bat                     # Script para conectar vía SSH y lanzar bot
│   └── crear_vm_noticiasbot.bat      # Crea la VM con GPU en GCP
│
├── local/
│   ├── crear_noticia_ollama.py       # Versión para ejecución en local con Ollama
│   └── requirements.txt              # Dependencias locales (incluye torch)
│
├── telegram/
│   └── telegram_message_bot.py       # (Próximamente) Bot Telegram interactivo
│
└── README.md                         # Este documento
```

---

## ☁️ Despliegue en Google Cloud Platform (GCP)

### 1. Preparar el entorno

* Instala el [Google Cloud SDK](https://cloud.google.com/sdk)
* Activa tu proyecto:

```bash
gcloud config set project TU_PROYECTO_ID
```

### 2. Crear la VM con GPU

```bat
crear_vm_noticiasbot.bat
```

Este script lanza una instancia con:

* GPU NVIDIA T4
* Ubuntu 22.04
* 100 GB de disco SSD
* Puertos HTTP/HTTPS abiertos (con etiquetas)

> Recuerda solicitar la cuota de GPU previamente desde la consola de GCP.

### 3. Conectarse a la VM

```bat
start.bat
```

Esto abre una sesión SSH y permite lanzar el bot manualmente.

### 4. Instalar dependencias dentro de la VM

```bash
sudo apt update && sudo apt install -y python3-pip python3-venv git
python3 -m venv venv && source venv/bin/activate
git clone https://github.com/TU_USUARIO/noticiasbot.git
cd noticiasbot/cloud
pip install -r requirements.txt
pip install torch==2.2.2+cu118 --index-url https://download.pytorch.org/whl/cu118
```

### 5. Ejecutar el bot

```bash
python crear_noticia_gcp.py
```

---

## 🔐 Variables necesarias en Secret Manager (GCP)

* `TELEGRAM_BOT_TOKEN` → Token del bot de Telegram
* `TELEGRAM_CHAT_ID` → ID del canal o chat donde publicar
* `GOOGLE_API_KEY` → Clave de API de Google Programmable Search
* `GOOGLE_CX_ID` → ID del motor de búsqueda personalizado

---

## 📬 Próximos pasos

* [ ] Mejorar `telegram_message_bot.py` para responder a comandos
* [ ] Agendado automático (cron local o Cloud Scheduler)
* [ ] Soporte para varios idiomas

---

Cualquier contribución o duda, ¡bienvenida!

💬 Contacto: [carthagonova@gmail.com](mailto:carthagonova@gmail.com)
