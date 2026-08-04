import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState

def run_architect_agent(state: AgentState) -> dict:
    print("--- INICIANDO AGENTE ARQUITECTO COREIA ---")
    info = state.get("extracted_info", {})
    chat_history = state.get("chat_history", [])
    
    core_feat = info.get("core_feature", "Sistema Web")
    plat = info.get("platform", "Web")
    
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", (
            "Eres el Arquitecto de Software Cloud Principal de CoreIA. Diseña la infraestructura técnica "
            "pesada y el esquema SQL detallado EXCLUSIVAMENTE para la idea del proyecto actual.\n\n"
            "REGLA PROHIBITIVA ESTRICTA:\n"
            "Queda prohibido incluir conceptos de proyectos anteriores (como paneles solares, eficiencia energética) "
            "si la idea actual trata de otra industria (ej: CRM, Inmobiliaria, Peluquería, Autolavado).\n\n"
            "Estructura del Diseño:\n"
            "1. **Stack Tecnológico Recomendado**\n"
            "2. **Diseño de Base de Datos (SQL)** (Tablas, columnas y relaciones alineadas a la idea actual)\n"
            "3. **Estrategia de Despliegue Cloud**"
        )),
        ("user", "Diseña la infraestructura para la Funcionalidad Core: {core_feature}")
    ])
    
    prompt = prompt_template.format_messages(core_feature=core_feat)
    response = llm.invoke(prompt)
    
    # 🧹 Limpieza e inyección en el archivo físico local
    filename = "ARQUITECTURA_DISEÑO.md"
    if os.path.exists(filename):
        try:
            os.remove(filename)
        except Exception as e:
            print(f"⚠️ No se pudo eliminar el archivo de arquitectura anterior: {e}")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(response.content)
        
    # 📱 Mensaje Comercial para el historial del Cliente
    commercial_content = (
        f"🏗️ **Garantía de Estructura y Seguridad:** Diseñamos una arquitectura sólida "
        f"en la nube para la plataforma ({plat}). Esto asegura que los datos de tus clientes "
        f"estén completamente blindados, respaldados y que la aplicación responda en milisegundos."
    )
    
    return {
        "architect_doc": response.content,
        "chat_history": chat_history + [{"role": "architect", "content": commercial_content}]
    }