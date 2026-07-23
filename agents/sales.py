import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState

def run_sales_agent(state: AgentState) -> dict:
    print("--- INICIANDO AGENTE COMERCIAL / COTIZADOR ---")
    info = state.get("extracted_info", {})
    chat_history = state.get("chat_history", [])
    
    analyst_requirements = "No especificado"
    if os.path.exists("REQUERIMIENTOS_MVP.md"):
        with open("REQUERIMIENTOS_MVP.md", "r", encoding="utf-8") as f:
            analyst_requirements = f.read()

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    human_context = (
        f"Funcionalidad Core: {info.get('core_feature', 'No especificado')}\n"
        f"Plataforma: {info.get('platform', 'No especificado')}\n"
        f"Requerimientos y reglas de negocio:\n{analyst_requirements}"
    )

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """Eres el Director Comercial Senior de CoreIA. Tu objetivo es transformar el interés del cliente en una oportunidad de venta formal para el desarrollo del software en producción.

Debes generar una propuesta comercial muy breve, clara, persuasiva y profesional estructurada de la siguiente manera:

1. **Estimación Económica en Pesos Colombianos (COP)**: Evalúa la complejidad del proyecto (básica, intermedia, avanzada) y asigna un rango estimado de inversión en COP (ej. $2.500.000 COP - $4.000.000 COP).
2. **Tiempo Estimado de Entrega**: Propon un tiempo de implementación realista (ej. 2 a 3 semanas).
3. **Inclusiones Principales**: Menciona brevemente que incluye base de datos, backend seguro, integraciones reales (ej. PSE / WhatsApp) y despliegue en la nube.
4. **Llamado a la Acción (Call to Action)**: Invita cordialmente al cliente a agendar una breve llamada de 15 minutos o responder si desea recibir la propuesta formal en PDF.

Mantén un tono ejecutivo, consultivo y altamente profesional."""),
        ("human", "{contexto_comercial}")
    ])

    prompt = prompt_template.format_messages(contexto_comercial=human_context)
    response = llm.invoke(prompt)

    proposal_text = response.content.strip()

    commercial_entry = f"💼 **Propuesta Comercial de CoreIA:**\n\n{proposal_text}"

    print("--- PROPUESTA COMERCIAL GENERADA CON ÉXITO ---")

    return {
        "chat_history": chat_history + [{"role": "sales", "content": commercial_entry}],
        "commercial_proposal": proposal_text
    }