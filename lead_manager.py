import os
import json
import traceback
from datetime import datetime, timezone
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
    print("⚠️ [SUPABASE] Faltan SUPABASE_URL o SUPABASE_KEY en Render.")

def save_lead(client_phone: str, state_data: dict, custom_status: str = None):
    if not supabase:
        print("❌ [SUPABASE] Operación cancelada: Cliente no inicializado.")
        return False

    clean_phone = str(client_phone).replace("whatsapp_", "").replace(":", "_").replace("+", "").replace("@c.us", "").replace("@s.whatsapp.net", "").strip()
    
    extracted = state_data.get("extracted_info", {})
    if not isinstance(extracted, dict):
        extracted = {}

    lead_status = custom_status or state_data.get("lead_status", "EN_CONSULTA")
    is_interested = state_data.get("is_interested", False)
    es_cliente_interesado = is_interested or (lead_status in ["LISTO_PARA_CONTRATAR", "CONTRATADO", "PROTOTIPO_ENTREGADO"])

    raw_history = state_data.get("chat_history", [])
    try:
        history_str = json.dumps(raw_history, ensure_ascii=False)
    except Exception:
        history_str = str(raw_history)

    # Payload adaptado 100% a las columnas de la tabla public.leads_coreia
    payload = {
        "client_id": clean_phone,
        "fecha_ultima_act": datetime.now(timezone.utc).isoformat(),
        "estado_lead": str(lead_status),
        "es_cliente_intere": bool(es_cliente_interesado),
        "informacion_extr": extracted, # Guarda en JSONB la fecha de cita, hora, módulos y detalles del MVP
        "propuesta_come": str(state_data.get("commercial_proposal", "")),
        "ruta_prototipo": f"/prototipo/{clean_phone}",
        "historial_mensaje": history_str
    }

    try:
        res = supabase.table("leads_coreia").upsert(payload, on_conflict="client_id").execute()
        print(f"✅ [SUPABASE SUCCESS] LEAD GUARDADO/ACTUALIZADO: {clean_phone} | Estado: {lead_status}")
        return True
    except Exception as e:
        print(f"❌ [SUPABASE ERROR GRAVE]: {e}")
        print(traceback.format_exc())
        return False