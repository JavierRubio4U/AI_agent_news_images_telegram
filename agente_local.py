import requests
import json
import feedparser

def obtener_noticias_ia():
    feed_url = "https://feeds.feedburner.com/venturebeat/SZYF"  # VentureBeat AI
    feed = feedparser.parse(feed_url)
    noticias = []
    for entrada in feed.entries[:3]:  # Solo 3 titulares
        titulo = entrada.title
        enlace = entrada.link
        noticias.append(f"{titulo} ({enlace})")
    return "\n".join(noticias)

url = "http://localhost:1234/v1/chat/completions"
headers = {"Content-Type": "application/json"}

mensajes = []

print("🧠 Agente local activo con streaming. Escribe 'salir' para terminar.\n")

while True:
    user_input = input("Tú: ")
    if user_input.lower() in ['salir', 'exit', 'q']:
        break
    
    # 📌 Si escribe "noticias", se cargan y se reescribe el prompt
    if user_input.lower() == "noticias":
        resumen = obtener_noticias_ia()
        user_input = f"Resume estas noticias y coméntalas en español:\n{resumen}"
        print("📰 Noticias obtenidas y enviadas al modelo...\n")

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
            # Quitar prefijo "data: " si lo tiene
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


    # Guardar conversación en un archivo de log
    with open("log_conversacion.txt", "a", encoding="utf-8") as f:
        f.write(f"Tú: {user_input}\n")
        f.write(f"🤖 {content}\n")
        f.write("-" * 40 + "\n")

