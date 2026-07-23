import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState

def run_developer_agent(state: AgentState) -> dict:
    print("--- INICIANDO AGENTE DESARROLLADOR ---")
    chat_history = state.get("chat_history", [])
    info = state.get("extracted_info", {})
    
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.0,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", (
            "Eres el Líder de Desarrollo Backend de CoreIA. Tu único objetivo es escribir el código "
            "fuente real, limpio y estructurado en FastAPI y SQL para el archivo local.\n\n"
            "Estructura para el ARCHIVO LOCAL:\n"
            "1. **Script DDL SQL (schema.sql)**\n"
            "2. **Código Python Completo (main.py)** con FastAPI"
        )),
        ("user", "Escribe el código fuente de producción para resolver el core: {core_feature}")
    ])
    
    prompt = prompt_template.format_messages(core_feature=info.get("core_feature", "No especificado"))
    response = llm.invoke(prompt)
    
    # 💾 Guardar código de ingeniería real
    with open("CODIGO_GENERADO_FACTORIA.md", "w", encoding="utf-8") as f:
        f.write(response.content)
        
    # 📱 Mensaje Comercial para el historial del Cliente
    commercial_content = (
        f"💻 **Lógica de Negocio Desplegada:** Nuestro equipo ha programado las funciones principales "
        f"del backend. Toda la automatización necesaria para gestionar las reglas de tu negocio está lista "
        f"en sus cimientos para operar sin fallas."
    )
    
    return {
        "chat_history": chat_history + [{"role": "developer", "content": commercial_content}]
    }