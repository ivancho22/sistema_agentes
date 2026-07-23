import os
import requests
from fastapi import FastAPI, Form, Response, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from twilio.http.http_client import TwilioHttpClient
from dotenv import load_dotenv

# Importaciones de tu Grafo
from audio_handler import AudioProcessor
from graph import app_graph
from state import MVPInformation
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="CoreIA Software Factory Webhook")
audio_processor = AudioProcessor()

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
        # Ejecución del grafo completo
        updated_state = app_graph.invoke(current_state)
        session_storage[client_phone] = updated_state
        info = updated_state.get("extracted_info", {})
        
        # 💡 Extraemos la propuesta comercial generada por el Agente Comercial
        proposal = updated_state.get("commercial_proposal", "")
        
        # Formateamos el número para la URL
        clean_phone = client_phone.replace(":", "_").replace("+", "")
        
        # Enlaces únicos dinámicos por cliente
        link_local = f"http://127.0.0.1:8000/prototipo/{clean_phone}"
        
        summary = (
            f"¡🚀 *Tu MVP interactivo está desplegado!* 🚀\n\n"
            f"La factoría técnica de *CoreIA* ha desarrollado tu solución a medida para:\n"
            f"*{info.get('core_feature', 'Módulo Principal')}*.\n\n"
            f"🎨 *Interactúa con tu App en el siguiente enlace exclusivo:*\n"
            f"🔗 {link_local}\n\n"
        )
        
        if ngrok_url and "localhost" not in ngrok_url and "127.0.0.1" not in ngrok_url:
            summary += f"📱 *Desde tu celular (Túnel Ngrok):*\n🔗 {ngrok_url}/prototipo/{clean_phone}\n\n"
            
        summary += (
            f"✨ *Especificaciones compiladas:*\n"
            f"• Lógica matemática y UI responsive funcional.\n"
            f"• Precios y reglas de negocio adaptadas a tu solicitud.\n\n"
            f"Haz clic en el enlace azul para probar las tarjetas, simular los pagos e interactuar con el prototipo.\n"
        )

        # 💡 Si el Agente Comercial generó propuesta, la anexamos al mensaje de WhatsApp
        if proposal:
            summary += f"\n---\n{proposal}\n"
        
        twilio_client.messages.create(
            body=summary,
            from_=os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886"),
            to=client_phone
        )
        print(f"--- MVP Y PROPUESTA COMERCIAL ENTREGADOS CON ÉXITO A {clean_phone} ---")
    except Exception as e:
        print(f"Error en la factoría al notificar a {client_phone}: {e}")

# 🌐 ENDPOINT DINÁMICO POR CLIENTE EN APP.PY
@app.get("/prototipo/{client_phone}", response_class=HTMLResponse)
async def ver_prototipo_cliente(client_phone: str):
    clean_phone = client_phone.replace("whatsapp_", "").replace(":", "_").replace("+", "").strip()
    
    # Posibles rutas donde se pudo guardar la carpeta
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
# Endpoint fallback genérico por compatibilidad
@app.get("/prototipo", response_class=HTMLResponse)
async def ver_prototipo_default():
    return "<h3>Por favor especifica tu enlace único de prototipo entregado por WhatsApp.</h3>"

@app.post("/api/confirmar_interaccion")
async def registrar_interaccion(data: InteractionData, background_tasks: BackgroundTasks):
    print(f"--- NUEVA INTERACCIÓN EN PROTOTIPO DE {data.client_phone} ---")
    print(f"Detalles: {data.service_details} | Total: {data.total_amount}")
    
    # Notificamos por WhatsApp que la simulación en la web funcionó
    mensaje_notificacion = (
        f"⚡ *Simulación de Transacción Exitosa en tu Prototipo:*\n\n"
        f"• *Servicio:* {data.service_details}\n"
        f"• *Valor:* {data.total_amount}\n\n"
        f"✅ *¡Tu software en producción estará conectado directamente a tu pasarela PSE y base de datos!*"
    )
    
    background_tasks.add_task(
        twilio_client.messages.create,
        body=mensaje_notificacion,
        from_=os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886"),
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
    response = MessagingResponse()
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
            "client_phone": client_phone, # 👈 Inyectamos el teléfono en el estado global
            "last_transcription": "",
            "extracted_info": MVPInformation().model_dump(),
            "followup_question": None,
            "chat_history": [],
            "is_ready_for_mvp": False
        }

    current_state = session_storage[client_phone]
    current_state["client_phone"] = client_phone # Aseguramos persistencia del ID
    
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
        response.message("No logré entender el mensaje. ¿Podrías repetirmelo, por favor?")
        return Response(content=str(response), media_type="text/xml; charset=utf-8")

    current_state["last_transcription"] = transcription_text

    from agents.discovery import run_discovery_agent
    discovery_result = run_discovery_agent(current_state)
    
    current_state["extracted_info"] = discovery_result["extracted_info"]
    current_state["is_ready_for_mvp"] = discovery_result["is_ready_for_mvp"]
    current_state["followup_question"] = discovery_result["followup_question"]
    current_state["chat_history"] = discovery_result["chat_history"]
    
    session_storage[client_phone] = current_state

    if current_state["is_ready_for_mvp"]:
        response.message(
            "⚙️ *CoreIA Factory:* ¡Excelente! He recopilado toda la información requerida.\n\n"
            "🧠 *Activando factoría técnica de software...*\n\n"
            "⏳ Compilando prototipo personalizado. En unos segundos te enviaré tu acceso exclusivo por aquí."
        )
        background_tasks.add_task(run_agent_factory_in_background, current_state, client_phone, ngrok_url)
    else:
        response.message(current_state["followup_question"])

    return Response(content=str(response), media_type="text/xml; charset=utf-8")