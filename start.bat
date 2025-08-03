@echo off
set VM_NAME=noticiasbot-vm
set ZONE=europe-west1-b
set USER=tu-usuario
set PROJECT=api-project-1047655645154

REM Conectarse por SSH y ejecutar todo dentro de la VM
gcloud compute ssh %USER%@%VM_NAME% --zone=%ZONE% --project=%PROJECT% --command="

cd /home/%USER%/noticiasbot || mkdir /home/%USER%/noticiasbot && cd /home/%USER%/noticiasbot

# Crear entorno virtual si no existe
if [ ! -d venv ]; then
  python3 -m venv venv
fi

source venv/bin/activate

# Instalar Torch con CUDA 11.8 solo si no está
pip show torch || pip install torch==2.2.2+cu118 --index-url https://download.pytorch.org/whl/cu118

# Instalar resto de requirements
pip install -r requirements.txt

# Exportar variables de entorno (puedes comentar si usas Secret Manager en futuro)
export TELEGRAM_TOKEN=TU_TOKEN
export TELEGRAM_CHAT_ID=TU_CHAT_ID
export GOOGLE_API_KEY=TU_GOOGLE_API_KEY
export GOOGLE_CX_ID=TU_CX_ID

# Lanzar el servidor FastAPI
python crear_noticia_gcp.py
"
