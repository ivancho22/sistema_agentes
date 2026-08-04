import os
import re
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState

def run_developer_agent(state: AgentState) -> dict:
    print("--- INICIANDO AGENTE DESARROLLADOR COREIA ---")
    chat_history = state.get("chat_history", [])
    info = state.get("extracted_info", {})
    
    core_feature = info.get("core_feature", "Sistema Web Interactivo")
    platform = info.get("platform", "Web")
    target = info.get("target_audience", "Usuarios Generales")

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2, # Temperatura baja para código preciso
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # 1. Prompt para el Backend y Schema SQL (CODIGO_GENERADO_FACTORIA.md)
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", (
            "Eres el Líder de Desarrollo de CoreIA. Tu objetivo es escribir el código "
            "fuente real, limpio y estructurado en FastAPI y SQL para el backend del proyecto.\n\n"
            "REQUISITOS:\n"
            "1. Script DDL SQL (schema.sql) adaptado ÚNICAMENTE a la idea de negocio actual.\n"
            "2. Código Python Completo (main.py) con endpoints en FastAPI para gestionar las operaciones clave."
        )),
        ("user", f"Escribe el código fuente de producción para resolver la idea: '{core_feature}' en plataforma '{platform}' para '{target}'.")
    ])
    
    prompt = prompt_template.format_messages()
    response = llm.invoke(prompt)
    
    # 💾 Guardar código de ingeniería backend localmente
    try:
        with open("CODIGO_GENERADO_FACTORIA.md", "w", encoding="utf-8") as f:
            f.write(response.content)
    except Exception as e:
        print(f"⚠️ Error escribiendo CODIGO_GENERADO_FACTORIA.md: {e}")

    # 2. Guardar en el estado para que Designer/Graph lo consuman sin ambigüedades
    commercial_content = (
        f"💻 **Lógica de Negocio Desplegada:** Se han programado los cimientos del backend "
        f"y la base de datos SQL para la funcionalidad '{core_feature}'."
    )
    
    return {
        "generated_code": response.content,
        "chat_history": chat_history + [{"role": "developer", "content": commercial_content}]
    }