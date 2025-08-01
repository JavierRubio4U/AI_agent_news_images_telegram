import asyncio
import os
import threading
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Cargar token desde .env
load_dotenv("credenciales_telegram.env")
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Semáforo para controlar acceso concurrente al modelo
semaforo_llm = asyncio.Semaphore(1)

def responder_con_modelo_local(prompt: str) -> str:
    url = "http://localhost:11434/v1/chat/completions"
    payload = {
        "model": "mistral-7b-instruct-v0.3",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=90)
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"❌ Error al consultar el modelo: {e}"

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message

    print(f"📥 Mensaje desde: {chat.username or chat.title} (ID: {chat.id}, tipo: {chat.type})")

    if chat.type != "private":
        print("🔕 Ignorado por no ser mensaje privado.")
        return

    if message and message.text:
        print(f"📩 Mensaje privado de @{update.effective_user.username}: {message.text}")
        await message.chat.send_action(ChatAction.TYPING)

        aviso = None
        if semaforo_llm.locked():
            aviso = await message.reply_text("⌛ Estoy generando tu respuesta, un momento...")

        async with semaforo_llm:
            loop = asyncio.get_event_loop()
            respuesta = await loop.run_in_executor(None, responder_con_modelo_local, message.text)
            await message.reply_text(respuesta)

            if aviso:
                await aviso.delete()
    else:
        print("⚠️ Mensaje sin texto. Ignorado.")



def arrancar_bot(app: Application, stop_event: threading.Event):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def run():
        await app.initialize()
        await app.start()
        await app.updater.start_polling()

        print("🤖 Bot activo, esperando mensajes... (Pulsa 'q' + Enter para apagar)")

        while not stop_event.is_set():
            await asyncio.sleep(0.5)

        print("🛑 Apagando bot...")

        await app.updater.stop()
        await app.stop()
        await app.shutdown()

    loop.run_until_complete(run())
    loop.close()

def iniciar_bot():
    stop_event = threading.Event()
    app = Application.builder().token(TOKEN).read_timeout(30).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))

    hilo = threading.Thread(target=arrancar_bot, args=(app, stop_event), daemon=True)
    hilo.start()

    try:
        while True:
            entrada = input()
            if entrada.strip().lower() == 'q':
                stop_event.set()
                hilo.join()
                break
    except KeyboardInterrupt:
        stop_event.set()
        hilo.join()

if __name__ == "__main__":
    iniciar_bot()
