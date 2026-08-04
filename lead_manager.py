import os
import json
from datetime import datetime
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ [SUPABASE] Cliente inicializado correctamente.")
    except Exception as e:
        print(f"❌ [SUPABASE] Error de conexión inicial: {e}")
else:
    print("⚠️ [SUPABASE] Faltan las variables NGROK_URL, SUPABASE_URL o SUPABASE_KEY en Render.")

def save_lead(client_phone: str, state_data: dict, custom_status: str = None):
    """
    Guarda o actualiza el registro del lead en Supabase en CADA interacción.
    """
    if not supabase:
        print("❌ [SUPABASE] Operación cancelada: El cliente de Supabase no está configurado.")
        return False

    clean_phone = str(client_phone).replace("whatsapp_", "").replace(":", "_").replace("+", "").replace("@c.us", "").replace("@s.whatsapp.net", "").strip()
    
    extracted = state_data.get("extracted_info", {})
    lead_status = custom_status or state_data.get("lead_status", "EN_CONSULTA")
    is_interested = state_data.get("is_interested", False)
    
    # Campo booleano de contratación
    es_cliente_contratado = is_interested or (lead_status in ["LISTO_PARA_CONTRATAR", "CONTRATADO", "PROTOTIPO_ENTREGADO"])

    # Serializar historial de chat a String JSON seguro
    raw_history = state_data.get("chat_history", [])
    try:
        history_json = json.dumps(raw_history, ensure_ascii=False)
    except Exception:
        history_json = str(raw_history)

    payload = {
        "client_id": clean_phone,
        "fecha_ultima_actividad": datetime.utcnow().isoformat(),
        "estado_lead": str(lead_status),
        "idea_proyecto": str(extracted.get("core_feature", "No especificado")),
        "plataforma": str(extracted.get("platform", "Web")),
        "publico_objetivo": str(extracted.get("target_audience", "General")),
        "es_cliente_contratado": bool(es_cliente_contratado),
        "historial_chat": history_json,
        "propuesta_comercial": str(state_data.get("commercial_proposal", ""))
    }

    try:
        # Intenta hacer un upsert basado en client_id
        response = supabase.table("leads_coreia").upsert(payload, on_conflict="client_id").execute()
        print(f"✅ [SUPABASE SUCCESS] LEAD REGISTRADO/ACTUALIZADO PARA {clean_phone} | Estado: {lead_status}")
        return True
    except Exception as e:
        print(f"❌ [SUPABASE ERROR DETALLADO]: {e}")
        return False