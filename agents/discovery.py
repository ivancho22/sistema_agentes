import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from state import AgentState, MVPInformation

def run_discovery_agent(state: AgentState) -> dict:
    print("--- INICIANDO AGENTE DE DESCUBRIMIENTO (CONSULTOR EXPERTO COREIA) ---")
    
    last_transcription = state.get("last_transcription", "")
    current_info = state.get("extracted_info", {})
    chat_history = state.get("chat_history", [])

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", (
            "Eres el Consultor Senior de Arquitectura de Producto en CoreIA. Tu objetivo NO es solo llenar un formulario, sino GUIAR al cliente para aterrizar una solución de software de alto valor.\n\n"
            "Las personas suelen saber su punto de dolor, pero no cómo estructurar una aplicación. Tu deber es actuar como un experto que propone soluciones y opciones concretas según el nicho del negocio.\n\n"
            "REGLAS DE ACTUACIÓN:\n"
            "1. Sé un Consultor, no un Entrevistador: Cuando el usuario te dé una idea vaga (ej. 'quiero un autolavado'), NO le preguntes qué campos quiere. PROPÓNLE 3 o 4 funcionalidades clave que ese tipo de negocio siempre necesita para vender más (ej: Selección de tipo de vehículo, combos con adicionales, agenda de turnos en tiempo real, abono por PSE).\n"
            "2. Propón Opciones Fáciles de Confirmar: Haz que la interacción sea fácil de responder. En lugar de preguntas abiertas difíciles, dale alternativas concretas para que el cliente solo tenga que decir 'sí, me gusta la opción 2 y ponle además X cosa'.\n"
            "3. Identificación de Módulos Core: Necesitamos asegurar 3 datos clave para disparar la compilación: Funcionalidad Core, Plataforma y Público Objetivo / Modelo de Operación.\n"
            "4. Criterio de Compilación (is_ready_for_mvp): Marca 'is_ready_for_mvp' en true ÚNICAMENTE cuando hayas propuesto un flujo claro y el usuario te haya dado luz verde o detalles suficientes sobre su operación.\n\n"
            "ESTRUCTURA DE RESPUESTA EN FORMATO JSON OBLIGATORIO:\n"
            "Debes responder ÚNICAMENTE en formato JSON válido estructurado así:\n"
            "{{\n"
            '  "core_feature": "Descripción detallada del flujo propuesto y aceptado",\n'
            '  "platform": "Web / Mobile / WhatsApp Bot",\n'
            '  "target_audience": "Descripción del público objetivo",\n'
            '  "is_ready_for_mvp": false,\n'
            '  "followup_question": "Tu mensaje consultivo y empático para el usuario proponiendo opciones o guiándolo hacia la confirmación."\n'
            "}}"
        )),
        ("user", (
            "Historial de Conversación: {chat_history}\n"
            "Información Extraída Previamente: {current_info}\n"
            "Último Mensaje del Cliente: \"{last_message}\"\n\n"
            "Analiza el mensaje, actualiza la información recopilada y genera la propuesta consultiva o confirmación en formato JSON."
        ))
    ])

    prompt = prompt_template.format_messages(
        chat_history=json.dumps(chat_history, ensure_ascii=False),
        current_info=json.dumps(current_info, ensure_ascii=False),
        last_message=last_transcription
    )
    
    response = llm.invoke(prompt)
    
    try:
        cleaned_response = response.content.strip().replace("```json", "").replace("```", "").strip()
        parsed_data = json.loads(cleaned_response)
        
        extracted_info = {
            "core_feature": parsed_data.get("core_feature") or current_info.get("core_feature", ""),
            "platform": parsed_data.get("platform") or current_info.get("platform", ""),
            "target_audience": parsed_data.get("target_audience") or current_info.get("target_audience", "")
        }
        
        is_ready = parsed_data.get("is_ready_for_mvp", False)
        followup = parsed_data.get("followup_question", "¿Me podrías dar más detalles de tu proyecto?")

    except Exception as e:
        print(f"Error parseando respuesta de Discovery: {e}")
        extracted_info = current_info
        is_ready = False
        followup = "¡Entendido! Cuéntame un poco más sobre cómo sueñas que funcione tu aplicación."

    updated_history = chat_history + [
        {"role": "user", "content": last_transcription},
        {"role": "assistant", "content": followup}
    ]

    return {
        "extracted_info": extracted_info,
        "is_ready_for_mvp": is_ready,
        "followup_question": followup,
        "chat_history": updated_history
    }