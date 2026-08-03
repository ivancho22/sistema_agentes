import os
import requests
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv

# Importaciones de tu Grafo y Módulos
from audio_handler import AudioProcessor
from graph import app_graph
from state import MVPInformation
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="CoreIA Software Factory Webhook")
audio_processor = AudioProcessor()

# --- CREDENCIALES GREEN API ---
GREEN_ID_INSTANCE = os.getenv("GREEN_ID_INSTANCE", "7105438396")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN", "TU_TOKEN_AQUI")
GREEN_API_URL = f"https://7105.api.greenapi.com/waInstance{GREEN_ID_INSTANCE}"

class InteractionData(BaseModel):
    client_phone: str
    service_details: str
    total_amount: str
    
session_storage = {}

# --- FUNCIÓN HELPER PARA ENVIAR MENSAJES VÍA GREEN API ---
def send_green_api_message(chat_id: str, text: str):
    """
    Envía un mensaje de texto por WhatsApp usando Green API.
    `chat_id` debe venir en formato internacional, ej: '573102476744@c.us'
    """
    try:
        url = f"{GREEN_API_URL}/sendMessage/{GREEN_API_TOKEN}"
        
        # Asegurar formato correcto de chatId
        if not chat_id.endswith("@c.us"):
            clean_number = chat_id.replace("whatsapp:", "").replace("+", "").replace(":", "").strip()
            chat_id = f"{clean_number}@c.us"

        payload = {
            "chatId": chat_id,
            "message": text
        }
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"--- MENSAJE ENVIADO VÍA GREEN API A {chat_id} ---")
        return True
    except Exception as e:
        print(f"❌ ERROR ENVIANDO MENSAJE VÍA GREEN API: {e}")
        return False


def run_agent_factory_in_background(current_state, client_phone: str, ngrok_url: str):
    try:
        print(f"--- INICIANDO GRAFO DE FACTORÍA PARA {client_phone} ---")
        updated_state = app_graph.invoke(current_state)
        session_storage[client_phone] = updated_state
        info = updated_state.get("extracted_info", {})
        proposal = updated_state.get("commercial_proposal", "")
        
        clean_phone = client_phone.replace("whatsapp_", "").replace(":", "_").replace("+", "").replace("@c.us", "")
        
        # Construir la URL del prototipo alojado en Render
        host_url = os.getenv("RENDER_EXTERNAL_URL", "https://coreia-factory.onrender.com")
        link_prototipo = f"{host_url}/prototipo/{clean_phone}"
        
        # 1. MENSAJE 1: Enlace al Prototipo Interactivo
        summary = (
            f"🚀 *¡Tu prototipo interactivo está listo!* 🚀\n\n"
            f"🎨 *Prueba la aplicación aquí:*\n"
            f"🔗 {link_prototipo}\n"
        )

        send_green_api_message(client_phone, summary)
        print(f"--- PROTOTIPO ENTREGADO A {client_phone} ---")

        # 2. MENSAJE 2: Propuesta Comercial
        if proposal:
            proposal_msg = f"📋 *Propuesta Comercial:*\n\n{proposal}"
            
            if len(proposal_msg) > 1500:
                proposal_msg = proposal_msg[:1450] + "\n\n...(Propuesta resumida para WhatsApp. Revisa el prototipo para más detalles)."

            send_green_api_message(client_phone, proposal_msg)
            print(f"--- PROPUESTA COMERCIAL ENTREGADA A {client_phone} ---")
            
    except Exception as e:
        print(f"❌ ERROR EN FACTORÍA: {e}")
        err_msg = f"⚠️ Ocurrió un inconveniente al generar tu prototipo: {str(e)[:100]}. Por favor, intenta enviando un nuevo mensaje."
        send_green_api_message(client_phone, err_msg)


@app.get("/prototipo/{client_phone}", response_class=HTMLResponse)
async def ver_prototipo_cliente(client_phone: str):
    clean_phone = client_phone.replace("whatsapp_", "").replace(":", "_").replace("+", "").replace("@c.us", "").strip()
    possible_paths = [
        os.path.join("prototipos", client_phone, "index.html"),
        os.path.join("prototipos", f"whatsapp_{clean_phone}", "index.html"),
        os.path.join("prototipos", clean_phone, "index.html"),
        os.path.join("prototipos", "demo_user", "index.html")
    ]
    for path in possible_paths:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
    return f"<h3>El prototipo para {client_phone} aún se está compilando en la factoría CoreIA. Por favor, recarga en unos segundos.</h3>"


@app.get("/prototipo", response_class=HTMLResponse)
async def ver_prototipo_default():
    return "<h3>Por favor especifica tu enlace único de prototipo entregado por WhatsApp.</h3>"


@app.post("/api/confirmar_interaccion")
async def registrar_interaccion(data: InteractionData, background_tasks: BackgroundTasks):
    mensaje_notificacion = (
        f"⚡ *Simulación de Transacción Exitosa en tu Prototipo:*\n\n"
        f"• *Servicio:* {data.service_details}\n"
        f"• *Valor:* {data.total_amount}\n\n"
        f"✅ *¡Tu software en producción estará conectado directamente a tu pasarela PSE y base de datos!*"
    )
    background_tasks.add_task(
        send_green_api_message,
        data.client_phone,
        mensaje_notificacion
    )
    return {"status": "ok", "message": "Interacción registrada con éxito"}


@app.post("/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(content={"status": "invalid json"}, status_code=400)

    # Filtrar únicamente notificaciones de mensajes de texto u audio ENTRANTES
    type_webhook = data.get("typeWebhook")
    if type_webhook != "incomingMessageReceived":
        return JSONResponse(content={"status": "ignored_webhook_type"}, status_code=200)

    sender_data = data.get("senderData", {})
    client_phone = sender_data.get("chatId") # Viene en formato: '573102476744@c.us'
    
    if not client_phone:
        return JSONResponse(content={"status": "no_sender_id"}, status_code=200)

    # Reconstrucción de la URL de Ngrok/Render si aplica
    host_header = request.headers.get("host", "")
    x_forwarded_host = request.headers.get("x-forwarded-host", "") or ""
    
    if "ngrok-free.app" in host_header and "tu-subdominio" not in host_header:
        ngrok_url = f"https://{host_header}"
    elif "ngrok-free.app" in x_forwarded_host and "tu-subdominio" not in x_forwarded_host:
        ngrok_url = f"https://{x_forwarded_host}"
    else:
        env_url = os.getenv("NGROK_URL", "")
        ngrok_url = env_url if "tu-subdominio" not in env_url else f"http://{host_header}"

    # Inicialización del estado en session_storage
    if client_phone not in session_storage:
        session_storage[client_phone] = {
            "client_phone": client_phone,
            "last_transcription": "",
            "extracted_info": MVPInformation().model_dump(),
            "followup_question": None,
            "chat_history": [],
            "is_ready_for_mvp": False
        }

    current_state = session_storage[client_phone]
    current_state["client_phone"] = client_phone

    # Extraer tipo de mensaje (Texto o Nota de Voz)
    message_data = data.get("messageData", {})
    type_message = message_data.get("typeMessage")
    transcription_text = ""

    # 1. Si es AUDIO / NOTA DE VOZ
    if type_message in ["audioMessage", "voiceMessage"]:
        file_url = message_data.get("fileMessageData", {}).get("downloadUrl")
        if file_url:
            local_filename = f"audio_{client_phone.replace('@c.us', '')}.ogg"
            try:
                # Green API entrega la URL de descarga directa sin credenciales
                audio_res = requests.get(file_url, timeout=10)
                with open(local_filename, "wb") as f:
                    f.write(audio_res.content)
                transcription_text = audio_processor.transcribe_audio_file(local_filename)
            except Exception as e:
                print(f"Error procesando audio: {e}")
                transcription_text = ""
            finally:
                if os.path.exists(local_filename):
                    os.remove(local_filename)

    # 2. Si es TEXTO CONVENCIONAL
    elif type_message in ["textMessage", "extendedTextMessage"]:
        transcription_text = message_data.get("textMessageData", {}).get("textMessage", "")

    # Validar si el texto está vacío
    if not transcription_text.strip():
        safe_msg = "No logré entender el mensaje. ¿Podrías repetírmelo, por favor?"
        send_green_api_message(client_phone, safe_msg)
        return JSONResponse(content={"status": "ok"}, status_code=200)

    current_state["last_transcription"] = transcription_text

    # Ejecución del agente de descubrimiento
    from agents.discovery import run_discovery_agent
    discovery_result = run_discovery_agent(current_state)
    
    current_state["extracted_info"] = discovery_result["extracted_info"]
    current_state["is_ready_for_mvp"] = discovery_result["is_ready_for_mvp"]
    current_state["followup_question"] = discovery_result["followup_question"]
    current_state["chat_history"] = discovery_result["chat_history"]
    
    session_storage[client_phone] = current_state

    # Definir la respuesta según el estado del MVP
    if current_state["is_ready_for_mvp"]:
        text_to_send = (
            "⚙️ *CoreIA Factory:* ¡Excelente! He recopilado toda la información requerida.\n\n"
            "🧠 *Activando factoría técnica de software...*\n\n"
            "⏳ Compilando prototipo personalizado. En unos segundos te enviaré tu acceso exclusivo por aquí."
        )
        background_tasks.add_task(run_agent_factory_in_background, current_state, client_phone, ngrok_url)
    else:
        text_to_send = current_state["followup_question"] or "Cuéntame más detalles sobre tu idea."

    # Enviar mensaje de respuesta vía Green API
    send_green_api_message(client_phone, text_to_send)

    return JSONResponse(content={"status": "ok"}, status_code=200)