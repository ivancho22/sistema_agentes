import os
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState

def run_designer_agent(state: AgentState) -> dict:
    print("--- INICIANDO AGENTE DISEÑADOR UX/UI INTERACTIVO AVANZADO ---")
    info = state.get("extracted_info", {})
    chat_history = state.get("chat_history", [])
    
    # 💡 1. Obtención robusta del teléfono del cliente
    client_phone = state.get("client_phone") or info.get("client_phone") or "demo_user"
    
    # Formateamos para que la carpeta coincida tanto si tiene prefijo 'whatsapp_' como si no
    clean_phone = client_phone.replace(":", "_").replace("+", "").strip()

    # Carga de plano de ingeniería del analista
    analyst_requirements = "No especificado"
    if os.path.exists("REQUERIMIENTOS_MVP.md"):
        with open("REQUERIMIENTOS_MVP.md", "r", encoding="utf-8") as f:
            analyst_requirements = f.read()

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.4,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    human_context = (
        "Teléfono del Cliente: " + str(client_phone) + "\n"
        "Funcionalidad Core: " + str(info.get('core_feature', 'No especificado')) + "\n"
        "Plataforma: " + str(info.get('platform', 'No especificado')) + "\n"
        "Público Objetivo: " + str(info.get('target_audience', 'No especificado')) + "\n\n"
        "--- PLANO TÉCNICO COMPLETO Y REGLAS DE NEGOCIO ---\n" +
        str(analyst_requirements)
    )
    
    # Escapamos las llaves dobles {{ }} para evitar interferencia con el parser de LangChain
    system_prompt_text = """Eres el Director de Diseño Frontend y UX/UI Senior de CoreIA. Tu objetivo es crear un prototipo SaaS interactivo que parezca una aplicación de producción lista para usar.

### BRANDING Y ESTÉTICA OBLIGATORIA:
1. Identidad del Negocio: Analiza la conversación y extrae el nombre comercial del cliente (ej. "Car Wash VIP", "Barbería Don Pedro", etc.). Si no hay uno explícito, créale un nombre de marca atractivo acorde al nicho.
2. Header con Marca: Muestra un encabezado elegante con el nombre del negocio, un Badge de "Prototipo Activo - CoreIA" y un ícono vectorial SVG acorde.
3. Layout Centrado en Modo Dark: Usa un contenedor flotante con Glassmorphism (bg-slate-900/80 backdrop-blur-xl border border-white/10 rounded-3xl shadow-2xl p-8 max-w-lg w-full).

### INTERACTIVIDAD Y PERSISTENCIA REAL (FETCH AL BACKEND):
1. Mapea exactos los precios en Pesos Colombianos (COP) y la lógica de negocio.
2. Debes incluir una función JavaScript en el HTML que se active al presionar el botón de confirmación o pago. Esta función DEBE hacer un fetch('/api/confirmar_interaccion') por POST enviando un objeto JSON estructurado exactamente así:
   
   fetch('/api/confirmar_interaccion', {{
       method: 'POST',
       headers: {{ 'Content-Type': 'application/json' }},
       body: JSON.stringify({{
           client_phone: 'CLIENT_PHONE_PLACEHOLDER',
           service_details: servicioSeleccionado,
           total_amount: valorTotalCalculado
       }})
   }});

3. Tras hacer el fetch, muestra un modal flotante moderno de confirmación de éxito en la pantalla (sin usar alert() nativo).

### REGLA DE FORMATO:
Devuelve ÚNICAMENTE el código HTML puro desde <!DOCTYPE html> hasta </html>. Nada de comentarios ni etiquetas markdown fuera del HTML."""

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt_text),
        ("human", "{contenido_diseno}")
    ])
    
    prompt = prompt_template.format_messages(contenido_diseno=human_context)
    response = llm.invoke(prompt)
    raw_content = response.content.strip()
    
    # Extracción del bloque HTML con Regex
    html_match = re.search(r'(<!DOCTYPE html>.*?</html>|<html.*?</html>)', raw_content, re.DOTALL | re.IGNORECASE)
    html_code = html_match.group(1).strip() if html_match else raw_content.replace("```html", "").replace("```", "").strip()
    
    # Inyección del teléfono real del cliente en el JavaScript
    html_code = html_code.replace("CLIENT_PHONE_PLACEHOLDER", client_phone)

    # 💡 2. Guardado en la carpeta específica del cliente
    client_dir = os.path.join("prototipos", clean_phone)
    os.makedirs(client_dir, exist_ok=True)
    
    output_filepath = os.path.join(client_dir, "index.html")
    with open(output_filepath, "w", encoding="utf-8") as f:
        f.write(html_code)
        
    print(f"--- PROTOTIPO ÚNICO GUARDADO EN: {output_filepath} ---")
    
    commercial_content = (
        "🎨 **Prototipo Avanzado Detallado:** Se han integrado con precisión todas tus reglas "
        "específicas de negocio en una interfaz interactiva a medida."
    )
    
    return {
        "chat_history": chat_history + [{"role": "designer", "content": commercial_content}]
    }