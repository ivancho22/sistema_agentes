import os
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState

def run_designer_agent(state: AgentState) -> dict:
    print("--- INICIANDO AGENTE DISEÑADOR UX/UI INTERACTIVO AVANZADO ---")
    info = state.get("extracted_info", {})
    chat_history = state.get("chat_history", [])
    
    # 💡 1. Obtención del teléfono/ID del cliente
    client_phone = state.get("client_phone") or info.get("client_phone") or "demo_user"
    clean_phone = str(client_phone).replace("whatsapp_", "").replace(":", "_").replace("+", "").replace("@c.us", "").strip()

    # Requerimientos provenientes del estado del grafo
    analyst_requirements = state.get("analyst_doc", "No especificado")

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2, # Reducimos a 0.2 para apegarse estrictamente al tema solicitado
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    core_feat = info.get('core_feature', 'Aplicación de Software')
    plat = info.get('platform', 'Web')
    target = info.get('target_audience', 'Usuarios Generales')

    human_context = (
        f"Teléfono del Cliente: {client_phone}\n"
        f"PROYECTO EXCLUSIVO A DIBUJAR: {core_feat}\n"
        f"Plataforma: {plat}\n"
        f"Público Objetivo: {target}\n\n"
        f"--- ESPECIFICACIÓN TÉCNICA Y REGLAS DE NEGOCIO DEL PROYECTO ---\n{analyst_requirements}"
    )
    
    # Prompt sin palabras clave heredadas ni ejemplos estáticos
    system_prompt_text = f"""Eres el Director de Diseño Frontend y UX/UI Senior de CoreIA.
Tu único objetivo es generar un prototipo web HTML/CSS/JS de nivel producción adaptado EXCLUSIVAMENTE a la siguiente idea: "{core_feat}".

### 🎨 REGLAS DE DISEÑO Y MAQUETACIÓN:
1. INCLUSIONES CDN OBLIGATORIAS:
   - Incluye Tailwind CSS CDN: <script src="https://cdn.tailwindcss.com"></script>
   - Incluye Lucide Icons CDN: <script src="https://unpkg.com/lucide@latest"></script>

2. ESTRUCTURA Y TARJETAS DE MÉTRICAS (KPIs):
   - Muestra un Header superior con el título "CoreIA - {core_feat}" y el estado "🟢 Prototipo Activo".
   - Genera 3 Tarjetas de Métricas en el grid superior cuyos nombres y valores sean 100% RELACIONADOS con "{core_feat}".
     * SI ES UN CRM / INMOBILIARIA: Muestra tarjetas como 'Inmuebles Activos', 'Clientes Potenciales', 'Ventas Estimadas'.
     * SI ES PELUQUERÍA / AUTOLAVADO: Muestra tarjetas como 'Citas del Día', 'Servicios Prestados', 'Ingresos Estimados'.
     * REGLA PROHIBITIVA ESTRICTA: Queda ESTRICTAMENTE PROHIBIDO usar palabras como 'Eficiencia Energética', 'Ahorro' o métricas solares si la idea no es de energía solar.

3. ESTILO VISUAL PREMIUM:
   - Usa modo oscuro elegante sobre Slate-900 con tarjetas en Glassmorphism (`bg-slate-800/80`, `border border-slate-700`, `rounded-2xl`, `shadow-2xl`).
   - Muestra un formulario, catálogo o panel interactivo adecuado para la lógica de "{core_feat}".

4. INTERACTIVIDAD REAL (JS):
   - Incluye una función JavaScript que procese las interacciones del formulario/pantalla y envíe la petición POST al backend:

```javascript
fetch('/api/confirmar_interaccion', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{
        client_phone: 'CLIENT_PHONE_PLACEHOLDER',
        service_details: detalleAccion,
        total_amount: valorCalculado
    }})
}});