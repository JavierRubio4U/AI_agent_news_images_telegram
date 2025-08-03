# Usar una imagen base oficial de Python con soporte para pip y CUDA si se quiere usar GPU (opcional)
FROM python:3.10-slim

# Crear y usar un directorio de trabajo
WORKDIR /app

# Copiar archivos necesarios
COPY . /app

# Instalar dependencias
RUN apt-get update && apt-get install -y git libgl1-mesa-glx libglib2.0-0 && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# Puerto por defecto de Cloud Run
EXPOSE 8080

# Ejecutar el script principal
CMD ["python", "crear_noticia_gcp.py"]


