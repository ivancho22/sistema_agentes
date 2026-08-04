import os
import requests
import time
from fastapi import FastAPI, BackgroundTasks, Request
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv
from pydantic import BaseModel

from lead_manager import save_lead
from audio_handler import AudioProcessor
from graph import app_graph
from state import MVPInformation

load_dotenv()

app = FastAPI(title="CoreIA Software Factory Webhook")
audio_processor = AudioProcessor()

# --- CREDENCIALES GREEN API ---
GREEN_ID_INSTANCE = os.getenv("GREEN_ID_INSTANCE", "7105438396")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN", "")
GREEN_API_URL = f"https://api.green-api.com/waInstance{GREEN_ID_INSTANCE}"

class InteractionData(BaseModel):
    client_phone: str
    service_details: str
    total_amount: str
    
session_storage = {}

def clean_phone_number(raw_phone: str) -> str:
    """Helper único para estandarizar el teléfono en todo el sistema."""
    return str(raw_phone).replace("whatsapp_", "").replace(":", "_").replace("+", "").replace("@c.us", "").strip()

# --- FUNCIÓN HELPER PARA ENVIAR MENSAJES VÍA GREEN API ---
def send_green_api_message(chat_id: str, text: str):
    try:
        time.sleep(2.0)
        url = f"{GREEN_API_URL}/sendMessage/{GREEN_API_TOKEN}"
        
        # Asegurar formato correcto de chatId para Green API
        if not chat_id.endswith("@c.us"):
            clean_num = clean_phone_number(chat_id)
            chat_id = f"{clean_num}@c.us"

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
        
        # 1. Ejecutar el grafo con los 5 agentes
        updated_state = app_graph.invoke(current_state)
        session_storage[client_phone] = updated_state
        
        proposal = updated_state.get("commercial_proposal", "")
        clean_phone = clean_phone_number(client_phone)
        
        # 2. Construir la URL del prototipo
        host_url = os.getenv("RENDER_EXTERNAL_URL", "https://coreia-factory.onrender.com")
        link_prototipo = f"{host_url}/prototipo/{clean_phone}"
        
        # 3. Guardar el Lead con la información del prototipo recién generado
        updated_state["lead_status"] = "PROTOTIPO_Y_OFERTA_ENTREGADOS"
        save_lead(client_phone, updated_state, custom_status="PROTOTIPO_ENTREGADO")

        # 4. MENSAJE 1: Notificación del Prototipo + Pregunta de Cierre
        summary = (
            f"🚀 *¡Tu prototipo interactivo está listo!*\n\n"
            f"🎨 *Prueba la aplicación aquí:*\n🔗 {link_prototipo}\n\n"
            f"💬 *¿Qué opinas del diseño?* ¿Te gustaría agregarle alguna funcionalidad extra o deseas que comencemos con el desarrollo oficial de tu software?"
        )
        send_green_api_message(client_phone, summary)
        print(f"--- PROTOTIPO ENTREGADO A {client_phone} ---")

        # 5. MENSAJE 2: Propuesta Comercial Resumida
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


# --- UNIFICACIÓN ÚNICA DEL ENDPOINT DE PROTOTIPOS ---
@app.get("/prototipo/{client_phone}", response_class=HTMLResponse)
async def serve_prototype(client_phone: str):
    clean_phone = clean_phone_number(client_phone)
    file_path = os.path.join("prototipos", clean_phone, "index.html")
    
    print(f"🔍 Buscando prototipo en: {file_path}")
    
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        response = HTMLResponse(content=content)
        # Encabezados anti-caché estrictos
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    else:
        print(f"❌ No se encontró el archivo en: {file_path}")
        return HTMLResponse(
            content=f"<h3>El prototipo para {clean_phone} aún se está compilando o no existe. Por favor, recarga en unos segundos.</h3>",
            status_code=404
        )


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

    host_header = request.headers.get("host", "")
    x_forwarded_host = request.headers.get("x-forwarded-host", "") or ""
    
    if "ngrok-free.app" in host_header and "tu-subdominio" not in host_header:
        ngrok_url = f"https://{host_header}"
    elif "ngrok-free.app" in x_forwarded_host and "tu-subdominio" not in x_forwarded_host:
        ngrok_url = f"https://{x_forwarded_host}"
    else:
        env_url = os.getenv("NGROK_URL", "")
        ngrok_url = env_url if "tu-subdominio" not in env_url else f"http://{host_header}"

    # Inicialización limpia del estado en session_storage
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

    # Extraer tipo de mensaje
    message_data = data.get("messageData", {})
    type_message = message_data.get("typeMessage")
    transcription_text = ""

    # 1. Si es AUDIO
    if type_message in ["audioMessage", "voiceMessage"]:
        file_url = message_data.get("fileMessageData", {}).get("downloadUrl")
        if file_url:
            local_filename = f"audio_{clean_phone_number(client_phone)}.ogg"
            try:
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

    # 2. Si es TEXTO
    elif type_message in ["textMessage", "extendedTextMessage"]:
        text_data = message_data.get("textMessageData", {}) or message_data.get("extendedTextMessageData", {})
        transcription_text = text_data.get("textMessage", "") or text_data.get("text", "")
        
    if not transcription_text.strip():
        safe_msg = "No logré entender el mensaje. ¿Podrías repetírmelo, por favor?"
        send_green_api_message(client_phone, safe_msg)
        return JSONResponse(content={"status": "ok"}, status_code=200)

    current_state["last_transcription"] = transcription_text

    # Ejecución del agente de descubrimiento
    from agents.discovery import run_discovery_agent
    discovery_result = run_discovery_agent(current_state)
    
    # 💡 RESET SI CAMBIA DE IDEA: Si discovery detecta una NUEVA_CONSULTA, limpiamos la info vieja
    if discovery_result.get("lead_status") == "NUEVA_CONSULTA":
        print("🔄 DETECTADO NUEVO PROYECTO: Limpiando memoria de la sesión...")
        current_state["extracted_info"] = discovery_result["extracted_info"]
        current_state["chat_history"] = [] # Reiniciar historial para el nuevo proyecto
    else:
        current_state["extracted_info"] = discovery_result["extracted_info"]
        current_state["chat_history"] = discovery_result["chat_history"]

    current_state["is_ready_for_mvp"] = discovery_result["is_ready_for_mvp"]
    current_state["followup_question"] = discovery_result["followup_question"]
    current_state["is_interested"] = discovery_result["is_interested"]
    current_state["lead_status"] = discovery_result["lead_status"]
    
    session_storage[client_phone] = current_state

    # Definir la respuesta según el estado
    if current_state["is_ready_for_mvp"]:
        text_to_send = (
            "⚙️ *CoreIA Factory:* ¡Excelente! He recopilado toda la información requerida.\n\n"
            "🧠 *Activando factoría técnica de software...*\n\n"
            "⏳ Compilando prototipo personalizado. En unos segundos te enviaré tu acceso exclusivo por aquí."
        )
        background_tasks.add_task(run_agent_factory_in_background, current_state, client_phone, ngrok_url)
    else:
        text_to_send = current_state["followup_question"] or "Cuéntame más detalles sobre tu idea."

    send_green_api_message(client_phone, text_to_send)

    return JSONResponse(content={"status": "ok"}, status_code=200)