import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState

def run_developer_agent(state: AgentState) -> dict:
    print("--- INICIANDO AGENTE DESARROLLADOR COREIA ---")
    chat_history = state.get("chat_history", [])
    info = state.get("extracted_info", {})
    
    analyst_doc = state.get("analyst_doc", "")
    architect_doc = state.get("architect_doc", "")
    
    core_feature = info.get("core_feature", "Sistema Web Interactivo")
    platform = info.get("platform", "Web")
    target = info.get("target_audience", "Usuarios Generales")

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    human_context = (
        f"Idea de Negocio EXCLUSIVA: {core_feature}\n"
        f"Plataforma: {platform}\n"
        f"Público Objetivo: {target}\n\n"
        f"--- REQUERIMIENTOS Y ARQUITECTURA TÉCNICA ---\n"
        f"{analyst_doc}\n\n{architect_doc}"
    )

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", (
            "Eres el Líder de Desarrollo Backend de CoreIA. Escribe el código fuente real, limpio y estructurado "
            "en FastAPI y SQL para el backend del proyecto actual.\n\n"
            "REGLA PROHIBITIVA ESTRICTA:\n"
            "Queda prohibido utilizar tablas o código de proyectos anteriores (como energía solar o paneles) "
            "si la idea actual trata de otra industria (ej: CRM, Inmobiliaria, Peluquería, Autolavado).\n\n"
            "REQUISITOS:\n"
            "1. Script DDL SQL (schema.sql) adaptado ÚNICAMENTE a la idea de negocio actual.\n"
            "2. Código Python Completo (main.py) con endpoints en FastAPI para gestionar las operaciones clave."
        )),
        ("human", "{contexto_desarrollo}")
    ])
    
    prompt = prompt_template.format_messages(contexto_desarrollo=human_context)
    response = llm.invoke(prompt)
    
    # 🧹 Limpieza e inyección en el archivo físico local
    filename = "CODIGO_GENERADO_FACTORIA.md"
    if os.path.exists(filename):
        try:
            os.remove(filename)
        except Exception as e:
            print(f"⚠️ Error al eliminar CODIGO_GENERADO_FACTORIA.md previo: {e}")

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(response.content)
    except Exception as e:
        print(f"⚠️ Error escribiendo CODIGO_GENERADO_FACTORIA.md: {e}")

    commercial_content = (
        f"💻 **Lógica de Negocio Desplegada:** Se han programado los cimientos del backend "
        f"y la base de datos SQL para la funcionalidad *{core_feature}*."
    )
    
    return {
        "generated_code": response.content,
        "chat_history": chat_history + [{"role": "developer", "content": commercial_content}]
    }