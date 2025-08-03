# Imagen base oficial con soporte CUDA 11.8 y Python 3.10
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Evitar prompts de apt
ENV DEBIAN_FRONTEND=noninteractive

# Actualizamos el sistema e instalamos dependencias básicas
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    git \
    curl \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos del bot al contenedor
COPY . .

# Instalar torch con CUDA 11.8 primero (no desde PyPI)
RUN pip install torch==2.2.2+cu118 --index-url https://download.pytorch.org/whl/cu118

# Instalar el resto de dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto para FastAPI (Cloud Run usa el 8080)
EXPOSE 8080

# Ejecutar la app con Uvicorn
CMD ["uvicorn", "crear_noticia_gcp:app", "--host", "0.0.0.0", "--port", "8080"]





