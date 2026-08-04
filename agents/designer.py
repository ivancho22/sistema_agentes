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
        temperature=0.2,
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
    
    # Construcción segura sin triples comillas f"""
    system_prompt_text = (
        "Eres el Director de Diseño Frontend y UX/UI Senior de CoreIA.\n"
        f"Tu único objetivo es generar un prototipo web HTML/CSS/JS de nivel producción adaptado EXCLUSIVAMENTE a la siguiente idea: '{core_feat}'.\n\n"
        "### 🎨 REGLAS DE DISEÑO Y MAQUETACIÓN:\n"
        "1. INCLUSIONES CDN OBLIGATORIAS:\n"
        "   - Incluye Tailwind CSS CDN: <script src=\"https://cdn.tailwindcss.com\"></script>\n"
        "   - Incluye Lucide Icons CDN: <script src=\"https://unpkg.com/lucide@latest\"></script>\n\n"
        "2. ESTRUCTURA Y TARJETAS DE MÉTRICAS (KPIs):\n"
        f"   - Muestra un Header superior con el título 'CoreIA - {core_feat}' y el estado '🟢 Prototipo Activo'.\n"
        f"   - Genera 3 Tarjetas de Métricas en el grid superior cuyos nombres y valores sean 100% RELACIONADOS con '{core_feat}'.\n"
        "     * SI ES UN CRM / INMOBILIARIA: Muestra tarjetas como 'Inmuebles Activos', 'Clientes Potenciales', 'Ventas Estimadas'.\n"
        "     * SI ES PELUQUERÍA / AUTOLAVADO: Muestra tarjetas como 'Citas del Día', 'Servicios Prestados', 'Ingresos Estimados'.\n"
        "     * REGLA PROHIBITIVA ESTRICTA: Queda ESTRICTAMENTE PROHIBIDO usar palabras como 'Eficiencia Energética', 'Ahorro' o métricas solares si la idea no es de energía solar.\n\n"
        "3. ESTILO VISUAL PREMIUM:\n"
        "   - Usa modo oscuro elegante sobre Slate-900 con tarjetas en Glassmorphism (bg-slate-800/80, border border-slate-700, rounded-2xl, shadow-2xl).\n"
        f"   - Muestra un formulario, catálogo o panel interactivo adecuado para la lógica de '{core_feat}'.\n\n"
        "4. INTERACTIVIDAD REAL (JS):\n"
        "   - Incluye una función JavaScript que procese las interacciones del formulario/pantalla y envíe la petición POST al backend usando fetch a '/api/confirmar_interaccion' enviando JSON con 'client_phone', 'service_details' y 'total_amount'.\n"
        "   - Al hacer clic en el botón principal, muestra un modal flotante moderno de confirmación de éxito.\n\n"
        "### REGLA DE FORMATO:\n"
        "Devuelve ÚNICAMENTE el código HTML puro desde <!DOCTYPE html> hasta </html>. Nada de texto explicativo fuera del código."
    )

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt_text),
        ("human", "{contenido_diseno}")
    ])
    
    prompt = prompt_template.format_messages(contenido_diseno=human_context)
    response = llm.invoke(prompt)
    raw_content = response.content.strip()
    
    # Extracción del bloque HTML
    html_match = re.search(r'(<!DOCTYPE html>.*?</html>|<html.*?</html>)', raw_content, re.DOTALL | re.IGNORECASE)
    html_code = html_match.group(1).strip() if html_match else raw_content.replace("```html", "").replace("```", "").strip()
    
    # Inyección del teléfono real del cliente
    html_code = html_code.replace("CLIENT_PHONE_PLACEHOLDER", str(client_phone))

    # Guardado en la carpeta específica del cliente
    client_dir = os.path.join("prototipos", clean_phone)
    os.makedirs(client_dir, exist_ok=True)
    
    output_filepath = os.path.join(client_dir, "index.html")

    if os.path.exists(output_filepath):
        try:
            os.remove(output_filepath)
        except Exception as e:
            print(f"⚠️ No se pudo eliminar el prototipo anterior: {e}")

    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write(html_code)
        
    print(f"--- PROTOTIPO ÚNICO GUARDADO EN: {output_filepath} ---")
    
    commercial_content = (
        f"🎨 **Prototipo Personalizado:** Se ha diseñado la interfaz interactiva para el módulo de *{core_feat}*."
    )
    
    return {
        "prototype_path": f"/prototipo/{clean_phone}",
        "chat_history": chat_history + [{"role": "designer", "content": commercial_content}]
    }