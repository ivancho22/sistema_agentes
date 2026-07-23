import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState

def run_architect_agent(state: AgentState) -> dict:
    print("--- INICIANDO AGENTE ARQUITECTO ---")
    info = state.get("extracted_info", {})
    chat_history = state.get("chat_history", [])
    
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", (
            "Eres el Arquitecto de Software Cloud Principal de CoreIA. Diseña la infraestructura técnica "
            "pesada y el esquema SQL detallado para el archivo local.\n\n"
            "Estructura para el ARCHIVO LOCAL:\n"
            "1. **Stack Tecnológico Recomendado**\n"
            "2. **Diseño de Base de Datos (SQL)** (Tablas, columnas y relaciones)\n"
            "3. **Estrategia de Despliegue Cloud**"
        )),
        ("user", "Diseña la infraestructura para el Core Funcional: {core_feature}")
    ])
    
    prompt = prompt_template.format_messages(core_feature=info.get("core_feature", "No especificado"))
    response = llm.invoke(prompt)
    
    # 💾 Guardar diseño de ingeniería interno
    with open("ARQUITECTURA_DISEÑO.md", "w", encoding="utf-8") as f:
        f.write(response.content)
        
    # 📱 Mensaje Comercial para el historial del Cliente
    commercial_content = (
        f"🏗️ **Garantía de Estructura y Seguridad:** Diseñamos una arquitectura sólida "
        f"en la nube para la plataforma ({info.get('platform')}). Esto asegura que los datos de tus clientes "
        f"estén completamente blindados, respaldados y que la aplicación responda en milisegundos."
    )
    
    return {
        "chat_history": chat_history + [{"role": "architect", "content": commercial_content}]
    }