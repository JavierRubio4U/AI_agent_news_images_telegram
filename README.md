# 🤖 Agente de Noticias IA para Telegram

Este proyecto automatiza el proceso de selección, análisis y publicación de noticias tecnológicas (especialmente sobre inteligencia artificial) en un canal de Telegram, combinando un resumen generado por un LLM local y una imagen estilo GTA V.

---

## 🔧 ¿Qué hace este proyecto?

1. **Lee el feed RSS de VentureBeat**.
2. **Selecciona una de las 3 primeras noticias** (puede ser al azar o con selección manual).
3. **Envía la noticia a un modelo LLM local** (por ejemplo, Mistral vía Ollama) para generar:
   - Un título.
   - Un resumen breve.
   - Un comentario de impacto o contexto.
4. **Genera una imagen tipo póster estilo GTA V** con un prompt fijo.
5. **Publica todo en un canal de Telegram** automáticamente.

---

## 📁 Estructura de archivos

| Archivo                    | Descripción                                                                 |
|---------------------------|-----------------------------------------------------------------------------|
| `agente_local.py`         | Script manual. Permite elegir la noticia y ver el resultado antes de enviar.|
| `agente_local_automatico.py` | Script automático. Se ejecuta sin intervención, elige una noticia aleatoria y la publica. Ideal para uso diario con cron. |
| `publicar_telegram.py`    | Versión experimental o de pruebas para publicación en Telegram.            |
| `.gitignore`              | Evita subir archivos sensibles como `.env` con tus credenciales.           |

---

## 📦 Requisitos

- Python 3.10+
- Tener un modelo LLM corriendo localmente (como Ollama con Mistral).
- Cuenta de Telegram + un canal + un bot configurado con token.
- Archivo `.env` en la misma carpeta con este contenido:

```env
TELEGRAM_TOKEN=TuTokenTelegram
TELEGRAM_CHAT_ID=@TuCanalPublico
