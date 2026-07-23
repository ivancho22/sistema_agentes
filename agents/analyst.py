import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState


def run_analyst_agent(state: AgentState) -> dict:
    print("--- INICIANDO AGENTE ANALISTA ---")
    info = state.get("extracted_info", {})
    
    last_message = state.get("last_transcription", "No especificado")
    chat_history = state.get("chat_history", [])
    
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # 💡 Formateamos el texto del usuario usando Python puro para blindar las llaves de LangChain
    human_context = (
        f"Ficha técnica básica recopilada:\n"
        f"- Público objetivo: {info.get('target_audience', 'No especificado')}\n"
        f"- Funcionalidad core: {info.get('core_feature', 'No especificado')}\n"
        f"- Requiere Base de Datos: {'Sí' if info.get('database_needed') else 'No'}\n"
        f"- Plataforma: {info.get('platform', 'No especificado')}\n\n"
        f"Último mensaje directo del cliente: \"{last_message}\"\n"
        f"Historial completo de la conversación: {str(chat_history)}"
    )
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """Eres el Agente Analista Senior de CoreIA. Tu único objetivo es procesar la conversación completa y estructurar de manera implacable las especificaciones técnicas que alimentarán al Desarrollador y al Diseñador.

Sigue estas directrices estrictas de análisis:

### 📄 Estructura para el ARCHIVO LOCAL (REQUERIMIENTOS_MVP.md):
1. **Objetivo del MVP**: Define claramente qué problema resuelve el software basándote en la conversación.
2. **Historias de Usuario Críticas**: Redacta los flujos principales usando el formato estándar (Como... Quiero... Para...).
3. **Alcance Excluido**: Especifica qué cosas NO se van a construir en esta iteración para no perder foco.

### ⚙️ RIGOR TÉCNICO DE EXTRACCIÓN (REGLAS DE NEGOCIO):
• Analiza a fondo el último mensaje recibido y el historial. Extrae cada valor monetario, tarifa o precio mencionado por el cliente de manera exacta. Si menciona Pesos Colombianos, usa COP ($).
• Queda estrictamente PROHIBIDO generalizar o inventar precios por defecto (como usar $5 o $10). Si el cliente dice "Lavado Básico por 25000 pesos", debes mapearlo exactamente con ese valor y texto real.
• Identifica si el cliente describe acciones como "elegir", "seleccionar", "sumar" o "calcular", y documenta explícitamente que se requiere un COMPONENTE INTERACTIVO DINÁMICO en el frontend gestionado con JavaScript.
• Si se menciona "PSE" o "botón de pago", define la sección de Checkout indicando que requiere simular la transacción con una alerta interactiva.

Tu salida debe ser el contenido en Markdown ultra-específico para garantizar que el Desarrollador no tenga que improvisar ningún dato."""),
        ("human", "{contenido_cliente}") # 🚨 Una única llave limpia controlada al 100%
    ])
    
    # Pasamos el bloque de texto ya armado directamente
    prompt = prompt_template.format_messages(
        contenido_cliente=human_context
    )
    
    response = llm.invoke(prompt)
    
    # 💾 Guardar plano de ingeniería interno
    with open("REQUERIMIENTOS_MVP.md", "w", encoding="utf-8") as f:
        f.write(response.content)
        
    # 📱 Mensaje Comercial para el historial del Cliente
    commercial_content = (
        f"📋 **Análisis de Experiencia de Usuario:** Hemos estructurado el flujo ideal para que tus usuarios "
        f"interactúen de forma fluida con el módulo de *{info.get('core_feature')}*. Definimos las reglas de negocio "
        f"para asegurar que el sistema sea intuitivo, rápido y resuelva el problema desde el primer día."
    )
        
    return {
        "chat_history": chat_history + [{"role": "analyst", "content": commercial_content}]
    }