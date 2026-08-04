import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState

def run_sales_agent(state: AgentState) -> dict:
    print("--- INICIANDO AGENTE COMERCIAL / COTIZADOR ---")
    info = state.get("extracted_info", {})
    chat_history = state.get("chat_history", [])
    
    # 💡 1. Obtención y normalización del teléfono/ID del cliente para la URL
    client_phone = state.get("client_phone") or info.get("client_phone") or "demo_user"
    clean_phone = str(client_phone).replace("whatsapp_", "").replace(":", "_").replace("+", "").replace("@c.us", "").strip()

    # Requerimientos provenientes del estado del grafo
    analyst_requirements = state.get("analyst_doc", "No especificado")

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    core_feat = info.get('core_feature', 'No especificado')
    plat = info.get('platform', 'No especificado')

    human_context = (
        f"Funcionalidad Core: {core_feat}\n"
        f"Plataforma: {plat}\n"
        f"Requerimientos y reglas de negocio:\n{analyst_requirements}"
    )

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """Eres el Director Comercial Senior de CoreIA. Tu objetivo es transformar el interés del cliente en una oportunidad de venta formal para el desarrollo del software en producción.

Debes generar una propuesta comercial muy breve, clara, persuasiva y profesional estructurada de la siguiente manera:

1. **Estimación Económica en Pesos Colombianos (COP)**: Evalúa la complejidad del proyecto (básica, intermedia, avanzada) y asigna un rango estimado de inversión en COP (ej. $2.500.000 COP - $4.000.000 COP).
2. **Tiempo Estimado de Entrega**: Propón un tiempo de implementación realista (ej. 2 a 3 semanas).
3. **Inclusiones Principales**: Menciona brevemente que incluye base de datos, backend seguro, integraciones reales (ej. PSE / WhatsApp) y despliegue en la nube.
4. **Llamado a la Acción (Call to Action)**: Invita cordialmente al cliente a agendar una breve llamada de 15 minutos o responder si desea recibir la propuesta formal en PDF.

Mantén un tono ejecutivo, consultivo y altamente profesional."""),
        ("human", "{contexto_comercial}")
    ])

    prompt = prompt_template.format_messages(contexto_comercial=human_context)
    response = llm.invoke(prompt)

    proposal_text = response.content.strip()

    # 💡 2. Construcción del enlace dinámico al prototipo en Render
    prototype_url = f"https://coreia-factory.onrender.com/prototipo/{clean_phone}"

    # 💡 3. Mensaje Comercial Completo enviado al Usuario
    commercial_entry = (
        f"🎨 **¡Tu Prototipo Interactivo para '{core_feat}' está listo!**\n"
        f"Puedes probar la primera maqueta en vivo aquí:\n"
        f"👉 {prototype_url}\n\n"
        f"💼 **Propuesta Comercial Estimada:**\n\n{proposal_text}"
    )

    print("--- PROPUESTA COMERCIAL Y ENLACE DE PROTOTIPO GENERADOS CON ÉXITO ---")

    return {
        "chat_history": chat_history + [{"role": "sales", "content": commercial_entry}],
        "commercial_proposal": proposal_text,
        "prototype_path": f"/prototipo/{clean_phone}"
    }