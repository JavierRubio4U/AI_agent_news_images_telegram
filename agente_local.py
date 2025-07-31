import requests
import json
import feedparser
import os
from dotenv import load_dotenv
from publicar_telegram import publicar_en_telegram

# LM Studio endpoint
url = "http://localhost:1234/v1/chat/completions"
headers = {"Content-Type": "application/json"}
mensajes = []

print("🧠 Agente activo con streaming, logging y publicación. Escribe 'salir' para terminar.\n")

lista = []  # cache de noticias

def obtener_noticias_ia():
    feed_url = "https://feeds.feedburner.com/venturebeat/SZYF"
    feed = feedparser.parse(feed_url)
    noticias = []
    for i, entrada in enumerate(feed.entries[:5], start=1):
        titulo = entrada.title
        enlace = entrada.link
        noticias.append(f"{i}. {titulo} ({enlace})")
    return noticias

while True:
    user_input = input("Tú: ")
    if user_input.lower() in ['salir', 'exit', 'q']:
        break

    if user_input.lower() == "noticias":
        lista = obtener_noticias_ia()
        print("📰 Noticias disponibles:")
        for item in lista:
            print(item)
        print("\nEscribe: un número (1–5) para procesar una.\n")
        continue

    if user_input.isdigit() and 1 <= int(user_input) <= len(lista):
        indice = int(user_input) - 1
        seleccionada = lista[indice]
        user_input = f"Resume esta noticia y coméntala en español:\n{seleccionada}"
        print(f"📰 Procesando noticia {indice + 1}...\n")

    elif user_input.lower() == "publica":
        if mensajes:
            publicar_en_telegram(mensajes[-1]['content'])
        else:
            print("❌ No hay mensaje previo para publicar.")
        continue

    mensajes.append({"role": "user", "content": user_input})
    data = {
        "model": "local-model",
        "messages": mensajes,
        "temperature": 0.7,
        "stream": True
    }

    print("🤖 ", end='', flush=True)
    respuesta = requests.post(url, headers=headers, json=data, stream=True)

    content = ""
    for linea in respuesta.iter_lines():
        if linea:
            linea_str = linea.decode("utf-8")
            if linea_str.startswith("data: "):
                linea_str = linea_str[6:]
            if linea_str.strip() == "[DONE]":
                break
            try:
                dato = json.loads(linea_str)
                delta = dato['choices'][0]['delta']
                texto = delta.get('content', '')
                print(texto, end='', flush=True)
                content += texto
            except Exception as e:
                print(f"\n❌ Error procesando línea: {e}")

    print("\n")
    mensajes.append({"role": "assistant", "content": content})

    # Guardar log
    with open("log_conversacion.txt", "a", encoding="utf-8") as f:
        f.write(f"Tú: {user_input}\n")
        f.write(f"🤖 {content}\n")
        f.write("-" * 40 + "\n")

    if "Resume esta noticia" in user_input:
        publicar_en_telegram(content)


