import os
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState

def run_designer_agent(state: AgentState) -> dict:
    print("--- INICIANDO AGENTE DISEÑADOR UX/UI INTERACTIVO AVANZADO ---")
    info = state.get("extracted_info", {})
    chat_history = state.get("chat_history", [])
    
    # 💡 1. Obtención robusta del teléfono/ID del cliente
    client_phone = state.get("client_phone") or info.get("client_phone") or "demo_user"
    clean_phone = client_phone.replace("whatsapp_", "").replace(":", "_").replace("+", "").replace("@c.us", "").strip()

    # Carga del plano de ingeniería del analista
    analyst_requirements = "No especificado"
    if os.path.exists("REQUERIMIENTOS_MVP.md"):
        try:
            with open("REQUERIMIENTOS_MVP.md", "r", encoding="utf-8") as f:
                analyst_requirements = f.read()
        except Exception as e:
            print(f"⚠️ No se pudo leer REQUERIMIENTOS_MVP.md: {e}")

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    core_feat = info.get('core_feature', 'No especificado')
    plat = info.get('platform', 'No especificado')
    target = info.get('target_audience', 'No especificado')

    human_context = (
        f"Teléfono del Cliente: {client_phone}\n"
        f"Funcionalidad Core: {core_feat}\n"
        f"Plataforma: {plat}\n"
        f"Público Objetivo: {target}\n\n"
        f"--- PLANO TÉCNICO COMPLETO Y REGLAS DE NEGOCIO ---\n{analyst_requirements}"
    )
    
    # Prompt con llaves dobles {{ }} en bloques de JS/CSS para prevenir errores de parsing en LangChain
    system_prompt_text = f"""Eres el Director de Diseño Frontend y UX/UI Senior de CoreIA.
Tu único objetivo es generar un prototipo web HTML/CSS/JS de nivel producción (estilo SaaS Premium / Dashboard Moderno).

### 🎨 BRANDING Y ESTÉTICA OBLIGATORIA:
1. INCLUSIONES CDN:
   - Incluye Tailwind CSS CDN: <script src="https://cdn.tailwindcss.com"></script>
   - Incluye Lucide Icons CDN: <script src="https://unpkg.com/lucide@latest"></script>
   - Incluye Chart.js CDN si aplica para gráficos: <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

2. LAYOUT Y UI/UX (SaaS Dashboard Moderno):
   - Muestra un Header superior elegante con el logo/marca del proyecto, estado "🟢 Prototipo Activo - CoreIA" e íconos.
   - Crea un grid de Tarjetas de Métricas/KPIs en la parte superior adaptadas 100% A LA IDEA DEL USUARIO (ej. Si es Peluquería: 'Citas Hoy', 'Estilistas Activos', 'Ingresos Estimados'; Si es Autolavado: 'Vehículos Agendados', 'Servicios VIP', 'Total Cotizado'). Queda ESTRICTAMENTE PROHIBIDO usar temas de energía solar si el proyecto no es de energía.
   - Usa un contenedor amplio con Glassmorphism (`bg-slate-800/80`, `border border-slate-700`, `rounded-2xl`, `shadow-2xl`, `backdrop-blur-md`) sobre fondo oscuro Slate-900.
   - Incluye formularios estilizados e insumos interactivos propios de la idea de negocio.

3. DIVERSIDAD Y ACABADO VISUAL:
   - Agrega pestañas (Tabs), tablas de resultados, catálogos o calendarios de agendamiento según corresponda.
   - Usa botones con degradados atractivos (`bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500`), efectos hover y micro-interacciones fluidas.

4. INTERACTIVIDAD Y PERSISTENCIA REAL (FETCH AL BACKEND):
   - Implementa lógica JavaScript para seleccionar opciones o simular flujos reales.
   - Incluye una función JavaScript al presionar el botón de confirmación o simulación principal:

```javascript
fetch('/api/confirmar_interaccion', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{
        client_phone: 'CLIENT_PHONE_PLACEHOLDER',
        service_details: servicioSeleccionado,
        total_amount: valorTotalCalculado
    }})
}});