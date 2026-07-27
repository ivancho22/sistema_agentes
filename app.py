import os
import requests
from xml.sax.saxutils import escape
from fastapi import FastAPI, Form, Response, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from twilio.http.http_client import TwilioHttpClient
from dotenv import load_dotenv

# Importaciones de tu Grafo y Módulos
from audio_handler import AudioProcessor
from graph import app_graph
from state import MVPInformation
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="CoreIA Software Factory Webhook")
audio_processor = AudioProcessor()

# Priorizar el número en las variables de entorno de Render
TWILIO_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+573160513218")

custom_http_client = TwilioHttpClient(timeout=5.0)
twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"), 
    os.getenv("TWILIO_AUTH_TOKEN"),
    http_client=custom_http_client
)

class InteractionData(BaseModel):
    client_phone: str
    service_details: str
    total_amount: str
    
session_storage = {}

def run_agent_factory_in_background(current_state, client_phone: str, ngrok_url: str):
    try:
        print(f"--- INICIANDO GRAFO DE FACTORÍA PARA {client_phone} ---")
        updated_state = app_graph.invoke(current_state)
        session_storage[client_phone] = updated_state
        info = updated_state.get("extracted_info", {})
        proposal = updated_state.get("commercial_proposal", "")
        
        clean_phone = client_phone.replace(":", "_").replace("+", "")
        
        # Construir la URL del prototipo alojado en Render
        host_url = os.getenv("RENDER_EXTERNAL_URL", "https://coreia-factory.onrender.com")
        link_prototipo = f"{host_url}/prototipo/{clean_phone}"
        
        # 1. MENSAJE 1: Enlace al Prototipo Interactivo
        summary = (
            f"🚀 *¡Tu prototipo interactivo está listo!* 🚀\n\n"
            f"🎨 *Prueba la aplicación aquí:*\n"
            f"🔗 {link_prototipo}\n"
        )

        twilio_client.messages.create(
            body=summary,
            from_=TWILIO_NUMBER,
            to=client_phone
        )
        print(f"--- PROTOTIPO ENTREGADO A {client_phone} ---")

        # 2. MENSAJE 2: Propuesta Comercial (se envía en mensaje separado para evitar Error 21617)
        if proposal:
            proposal_msg = f"📋 *Propuesta Comercial:*\n\n{proposal}"
            
            # Recorte de seguridad a 1500 caracteres
            if len(proposal_msg) > 1500:
                proposal_msg = proposal_msg[:1450] + "\n\n...(Propuesta resumida para WhatsApp. Revisa el prototipo para más detalles)."

            twilio_client.messages.create(
                body=proposal_msg,
                from_=TWILIO_NUMBER,
                to=client_phone
            )
            print(f"--- PROPUESTA COMERCIAL ENTREGADA A {client_phone} ---")
            
    except Exception as e:
        print(f"❌ ERROR EN FACTORÍA: {e}")
        try:
            twilio_client.messages.create(
                body=f"⚠️ Ocurrió un inconveniente al generar tu prototipo: {str(e)[:100]}. Por favor, intenta enviando un nuevo mensaje.",
                from_=TWILIO_NUMBER,
                to=client_phone
            )
        except Exception as tw_err:
            print(f"Error al notificar excepción: {tw_err}")

@app.get("/prototipo/{client_phone}", response_class=HTMLResponse)
async def ver_prototipo_cliente(client_phone: str):
    clean_phone = client_phone.replace("whatsapp_", "").replace(":", "_").replace("+", "").strip()
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
        twilio_client.messages.create,
        body=mensaje_notificacion,
        from_=TWILIO_NUMBER,
        to=data.client_phone
    )
    return {"status": "ok", "message": "Interacción registrada con éxito"}

@app.post("/whatsapp")
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    From: str = Form(...),       
    NumMedia: int = Form(0),    
    MediaUrl0: str = Form(None), 
    MediaContentType0: str = Form(None), 
    Body: str = Form("")        
):
    client_phone = From

    host_header = request.headers.get("host", "")
    x_forwarded_host = request.headers.get("x-forwarded-host", "") or ""
    
    if "ngrok-free.app" in host_header and "tu-subdominio" not in host_header:
        ngrok_url = f"https://{host_header}"
    elif "ngrok-free.app" in x_forwarded_host and "tu-subdominio" not in x_forwarded_host:
        ngrok_url = f"https://{x_forwarded_host}"
    else:
        env_url = os.getenv("NGROK_URL", "")
        ngrok_url = env_url if "tu-subdominio" not in env_url else f"http://{host_header}"

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
    
    # Procesamiento de audio o texto
    if NumMedia > 0 and MediaUrl0 and "audio" in MediaContentType0:
        local_filename = f"audio_{client_phone.replace(':', '_')}.ogg"
        try:
            auth = (os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
            audio_data = requests.get(MediaUrl0, auth=auth)
            with open(local_filename, "wb") as f:
                f.write(audio_data.content)
            transcription_text = audio_processor.transcribe_audio_file(local_filename)
        except Exception as e:
            transcription_text = Body
        finally:
            if os.path.exists(local_filename):
                os.remove(local_filename)
    else:
        transcription_text = Body

    if not transcription_text.strip():
        safe_msg = escape("No logré entender el mensaje. ¿Podrías repetírmelo, por favor?")
        xml_err = f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{safe_msg}</Message></Response>'
        return Response(content=xml_err, media_type="application/xml")

    current_state["last_transcription"] = transcription_text

    # Ejecución del agente de descubrimiento
    from agents.discovery import run_discovery_agent
    discovery_result = run_discovery_agent(current_state)
    
    current_state["extracted_info"] = discovery_result["extracted_info"]
    current_state["is_ready_for_mvp"] = discovery_result["is_ready_for_mvp"]
    current_state["followup_question"] = discovery_result["followup_question"]
    current_state["chat_history"] = discovery_result["chat_history"]
    
    session_storage[client_phone] = current_state

# 1. Definir el texto a enviar según el estado del MVP
    if current_state["is_ready_for_mvp"]:
        text_to_send = (
            "⚙️ *CoreIA Factory:* ¡Excelente! He recopilado toda la información requerida.\n\n"
            "🧠 *Activando factoría técnica de software...*\n\n"
            "⏳ Compilando prototipo personalizado. En unos segundos te enviaré tu acceso exclusivo por aquí."
        )
        background_tasks.add_task(run_agent_factory_in_background, current_state, client_phone, ngrok_url)
    else:
        text_to_send = current_state["followup_question"] or "Cuéntame más detalles sobre tu idea."

    # 2. Enviar el mensaje explícitamente usando la API REST de Twilio (garantiza entrega en producción)
    try:
        twilio_client.messages.create(
            body=text_to_send,
            from_=TWILIO_NUMBER,
            to=client_phone
        )
        print(f"--- MENSAJE ENVIADO EXITOSAMENTE VÍA API A {client_phone} ---")
    except Exception as err_msg:
        print(f"❌ Error al enviar mensaje vía API: {err_msg}")

    # 3. Retornar TwiML vacío a Twilio para confirmar la recepción HTTP 200 OK
    empty_twiml = '<?xml version="1.0" encoding="UTF-8"?><Response></Response>'
    return Response(content=empty_twiml, media_type="application/xml")