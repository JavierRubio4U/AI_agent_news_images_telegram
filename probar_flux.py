from pathlib import Path
from datetime import datetime
from diffusers import StableDiffusionPipeline
import torch
import time

# Verificar estado de PyTorch y CUDA
def verificar_entorno():
    print("🚀 Estado de PyTorch:")
    print(f" - CUDA disponible: {torch.cuda.is_available()}")
    print(f" - Versión PyTorch: {torch.__version__}")
    if torch.cuda.is_available():
        print(f" - Versión CUDA: {torch.version.cuda}")
        print(f" - GPU activa: {torch.cuda.get_device_name(0)}")

# Listas ampliadas de personas y empresas del mundo IA
PERSONAS_IA = [
    "Elon Musk", "Sam Altman", "Demis Hassabis", "Geoffrey Hinton", "Yann LeCun",
    "Fei-Fei Li", "Andrew Ng", "Dario Amodei", "Ilya Sutskever", "Mark Zuckerberg",
    "Emad Mostaque", "Jensen Huang", "Sundar Pichai", "Satya Nadella"
]

EMPRESAS_IA = [
    "OpenAI", "DeepMind", "Anthropic", "Stability AI", "Meta", "Google", "Microsoft",
    "Tesla", "NVIDIA", "Amazon", "Apple", "IBM", "Hugging Face", "Mistral AI", "Runway"
]

# Crear prompt simple a partir de keywords
def generar_prompt_simple(keywords: list[str]) -> str:
    personas = [k for k in keywords if any(p.lower() in k.lower() for p in PERSONAS_IA)]
    empresas = [k for k in keywords if any(e.lower() in k.lower() for e in EMPRESAS_IA)]
    acciones = [k for k in keywords if k not in personas + empresas]

    prompt = "A cinematic poster showing "
    if personas:
        prompt += f"{', '.join(personas)} in a dramatic pose, "
    if empresas:
        prompt += f"surrounded by logos of {' and '.join(empresas)}, "
    if acciones:
        prompt += f"with themes of {' and '.join(acciones)}, "
    prompt += "in the art style of GTA VI"
    return prompt

# Generar imagen con parámetros ajustados
def generar_imagen_sd15(prompt: str):
    start = time.time()
    modelo_id = "sd-legacy/stable-diffusion-v1-5"
    pipe = StableDiffusionPipeline.from_pretrained(modelo_id, torch_dtype=torch.float16)
    pipe = pipe.to("cuda" if torch.cuda.is_available() else "cpu")

    print("🎨 Generando imagen con 25 pasos, guidance_scale=11 y formato teléfono (512x896)...")
    image = pipe(prompt, num_inference_steps=25, guidance_scale=11, height=512, width=896).images[0]

    nombre_archivo = f"imagen_prueba_sd15_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    image.save(nombre_archivo)
    print(f"✅ Imagen generada en {time.time() - start:.2f} segundos")
    print(f"🖼️ Imagen guardada como '{nombre_archivo}'")

# Ejecutar prueba
if __name__ == "__main__":
    verificar_entorno()
    keywords = ["Elon Musk", "Tesla", "release", "breakthrough", "AI agent"]
    prompt = generar_prompt_simple(keywords)
    print(f"\n🧠 Prompt generado:\n\"{prompt}\"\n")
    generar_imagen_sd15(prompt)
