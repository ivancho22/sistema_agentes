import os
import json
from datetime import datetime
from supabase import create_client, Client

LEADS_FILE = "leads_capturados.json"

# Configuración de Supabase desde variables de entorno
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"⚠️ No se pudo conectar a Supabase: {e}")

def save_lead(client_id: str, state: dict, custom_status: str = None):
    """Guarda o actualiza la información del lead tanto en JSON local como en Supabase."""
    status = custom_status or state.get("lead_status", "CONSULTA_INCOMPLETA")
    
    lead_data = {
        "client_id": client_id,
        "fecha_ultima_actividad": datetime.now().isoformat(),
        "estado_lead": status,
        "es_cliente_interesado": state.get("is_interested", False),
        "informacion_extraida": state.get("extracted_info", {}),
        "propuesta_comercial": state.get("commercial_proposal", "Pendiente"),
        "ruta_prototipo": state.get("prototype_path", "Pendiente"),
        "historial_mensajes_count": len(state.get("chat_history", []))
    }

    # 1. Guardar de respaldo en JSON Local
    try:
        leads = {}
        if os.path.exists(LEADS_FILE):
            with open(LEADS_FILE, "r", encoding="utf-8") as f:
                leads = json.load(f)
        leads[client_id] = lead_data
        with open(LEADS_FILE, "w", encoding="utf-8") as f:
            json.dump(leads, f, ensure_ascii=False, indent=4)
    except Exception as err:
        print(f"❌ Error al guardar en JSON local: {err}")

    # 2. Persistir en Supabase (si está configurado)
    if supabase:
        try:
            # Usamos upsert para insertar o actualizar según el client_id
            response = supabase.table("leads_coreia").upsert(
                lead_data, 
                on_conflict="client_id"
            ).execute()
            print(f"☁️ [SUPABASE] Lead '{client_id}' sincronizado con éxito.")
        except Exception as e:
            print(f"❌ [SUPABASE ERROR] No se pudo guardar el lead: {e}")