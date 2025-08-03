from transformers import pipeline
import json
import datetime

# 🔹 Carga del generador de texto desde Hugging Face
print("⏳ Cargando modelo...")
pipe = pipeline("text-generation", model="mistralai/Mistral-7B-Instruct-v0.2", device=-1)  # CPU
print("✅ Modelo cargado.")

# 🔹 Prompt fijo o dinámico
prompt = "Resume brevemente qué es la inteligencia artificial y sus usos actuales."

print("🧠 Enviando prompt al modelo...")
respuestas = pipe(prompt, max_new_tokens=300, do_sample=True, temperature=0.7)

texto_generado = respuestas[0]['generated_text']
print("\n📰 Resultado generado:\n")
print(texto_generado.strip())

# 🔹 Guarda publicación con fecha
fecha = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
nueva = {fecha: prompt}

try:
    with open("publicadas.json", "r", encoding="utf-8") as f:
        historico = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    historico = {}

historico.update(nueva)

with open("publicadas.json", "w", encoding="utf-8") as f:
    json.dump(historico, f, indent=2, ensure_ascii=False)

print("\n✅ Guardado en publicadas.json")

