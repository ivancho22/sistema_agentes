import os
from datetime import datetime
from supabase import create_client, Client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"⚠️ Error conectando con Supabase: {e}")

def save_lead(client_phone: str, state_data: dict, custom_status: str = None):
    """
    Guarda o actualiza el registro del lead en Supabase en CADA interacción.
    """
    if not supabase:
        print("⚠️ Supabase no está configurado correctamente.")
        return False

    clean_phone = str(client_phone).replace("whatsapp_", "").replace(":", "_").replace("+", "").replace("@c.us", "").strip()
    
    extracted = state_data.get("extracted_info", {})
    lead_status = custom_status or state_data.get("lead_status", "EN_CONSULTA")
    is_interested = state_data.get("is_interested", False)
    
    # Campo booleano si la persona decidió contratar o avanzar
    es_cliente_contratado = is_interested or (lead_status in ["LISTO_PARA_CONTRATAR", "CONTRATADO"])

    payload = {
        "client_id": clean_phone,
        "fecha_ultima_actividad": datetime.utcnow().isoformat(),
        "estado_lead": lead_status,
        "idea_proyecto": extracted.get("core_feature", "No especificado"),
        "plataforma": extracted.get("platform", "Web"),
        "publico_objetivo": extracted.get("target_audience", "General"),
        "es_cliente_contratado": es_cliente_contratado,
        "historial_chat": state_data.get("chat_history", []),
        "propuesta_comercial": state_data.get("commercial_proposal", "")
    }

    try:
        # Usamos upsert para actualizar por 'client_id' o crear la fila si no existe
        response = supabase.table("leads_coreia").upsert(payload, on_conflict="client_id").execute()
        print(f"✅ [SUPABASE] LEAD REGISTRADO/ACTUALIZADO PARA {clean_phone} CON ESTADO: {lead_status}")
        return True
    except Exception as e:
        print(f"❌ Error guardando lead en Supabase: {e}")
        return False