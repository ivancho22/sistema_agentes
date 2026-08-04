import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState

def run_analyst_agent(state: AgentState) -> dict:
    print("--- INICIANDO AGENTE ANALISTA COREIA ---")
    info = state.get("extracted_info", {})
    last_message = state.get("last_transcription", "No especificado")
    chat_history = state.get("chat_history", [])
    
    core_feat = info.get('core_feature', 'No especificado')

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    human_context = (
        f"Ficha técnica básica recopilada:\n"
        f"- Público objetivo: {info.get('target_audience', 'No especificado')}\n"
        f"- Funcionalidad core: {core_feat}\n"
        f"- Requiere Base de Datos: {'Sí' if info.get('database_needed') else 'No'}\n"
        f"- Plataforma: {info.get('platform', 'No especificado')}\n\n"
        f"Último mensaje directo del cliente: \"{last_message}\"\n"
        f"Historial completo de la conversación: {str(chat_history)}"
    )
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """Eres el Agente Analista Senior de CoreIA. Tu único objetivo es procesar la conversación completa y estructurar de manera implacable las especificaciones técnicas para la idea actual del cliente.

### 📄 Estructura para el ARCHIVO LOCAL (REQUERIMIENTOS_MVP.md):
1. **Objetivo del MVP**: Define claramente qué problema resuelve el software basándote EXCLUSIVAMENTE en la conversación actual.
2. **Historias de Usuario Críticas**: Redacta los flujos principales (Como... Quiero... Para...).
3. **Alcance Excluido**: Especifica qué cosas NO se van a construir en esta iteración.

### ⚙️ RIGOR TÉCNICO Y REGLAS DE NEGOCIO:
• Queda ESTRICTAMENTE PROHIBIDO incluir términos de proyectos anteriores (como energía solar, eficiencia energética o paneles) si el cliente está pidiendo otra cosa (ej: autolavado, peluquería, CRM).
• Extrae cada valor monetario o tarifa mencionada. Si menciona Pesos Colombianos, usa COP ($).
• Identifica si el cliente describe acciones interactiva ('elegir', 'sumar', 'calcular', 'agendar') para documentar que se requiere un COMPONENTE DINÁMICO.
• Si menciona 'PSE' o 'botón de pago', define la sección de Checkout simulated."""),
        ("human", "{contenido_cliente}")
    ])
    
    prompt = prompt_template.format_messages(contenido_cliente=human_context)
    response = llm.invoke(prompt)
    
    # 🧹 Limpieza e inyección en el archivo físico local
    filename = "REQUERIMIENTOS_MVP.md"
    if os.path.exists(filename):
        try:
            os.remove(filename)
        except Exception as e:
            print(f"⚠️ No se pudo eliminar el archivo anterior: {e}")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(response.content)
        
    commercial_content = (
        f"📋 **Análisis de Experiencia de Usuario:** Hemos estructurado el flujo ideal para que tus usuarios "
        f"interactúen de forma fluida con el módulo de *{core_feat}*. Definimos las reglas de negocio "
        f"para asegurar que el sistema sea intuitivo, rápido y resuelva el problema desde el primer día."
    )
        
    return {
        "analyst_doc": response.content,
        "chat_history": chat_history + [{"role": "analyst", "content": commercial_content}]
    }