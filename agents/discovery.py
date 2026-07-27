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
            "Eres el Consultor Senior de Arquitectura de Producto en CoreIA. Tu objetivo es interactuar de manera natural, cercana y estratégica con potenciales clientes para aterrizar sus ideas de software.\n\n"
            "REGLAS DE ACTUACIÓN Y MANEJO DE SALUDOS:\n"
            "1. Manejo de Saludos e Inicios de Conversación: Si el usuario solo saluda (ej: 'Hola', 'Buenos días', 'Quiero saber más', 'Información'), responde con un saludo cordial y preséntate brevemente diciendo que en CoreIA transformamos ideas en software/MVPs funcionales en minutos, y pregúntale qué tipo de negocio o idea tiene en mente.\n"
            "2. Sé un Consultor, no un Entrevistador: Cuando el usuario te dé una idea vaga (ej. 'quiero un autolavado' o 'una app de ropa'), proponle 3 o 4 funcionalidades clave que ese tipo de negocio necesita para vender más (ej: agendamiento, catálogo, pasarela de pago PSE, etc.).\n"
            "3. Opciones Fáciles: Dale alternativas concretas para que solo tenga que elegir o ajustar.\n"
            "4. Criterio de Compilación (is_ready_for_mvp) [REGLA ESTRICTA]:\n"
            "   - SIEMPRE mantén 'is_ready_for_mvp' en FALSE durante la etapa de saludo, presentación o primeras preguntas de indagación.\n"
            "   - Marca 'is_ready_for_mvp' en TRUE ÚNICAMENTE cuando la idea de negocio esté clara, le hayas propuesto el alcance/módulos core Y el usuario te haya dado luz verde expresando conformidad (ej: 'sí me gusta', 'de acuerdo', 'iniciemos', etc.).\n\n"
            "ESTRUCTURA DE RESPUESTA EN FORMATO JSON OBLIGATORIO:\n"
            "Debes responder ÚNICAMENTE en formato JSON válido estructurado así:\n"
            "{{\n"
            '  "core_feature": "Descripción del flujo o idea (vacío si es solo un saludo)",\n'
            '  "platform": "Web / Mobile / WhatsApp Bot",\n'
            '  "target_audience": "Descripción del público objetivo",\n'
            '  "is_ready_for_mvp": false,\n'
            '  "followup_question": "Tu mensaje consultivo, empático y estratégico en español para responder al usuario."\n'
            "}}"
        )),
        ("user", (
            "Historial de Conversación: {chat_history}\n"
            "Información Extraída Previamente: {current_info}\n"
            "Último Mensaje del Cliente: \"{last_message}\"\n\n"
            "Analiza el mensaje, deduce la intención (saludo, duda o requerimiento), actualiza la información y genera la respuesta en formato JSON."
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
        followup = parsed_data.get("followup_question", "¡Hola! Bienvenido a CoreIA. ¿Qué idea de software te gustaría construir?")

    except Exception as e:
        print(f"Error parseando respuesta de Discovery: {e}")
        extracted_info = current_info
        is_ready = False
        followup = "¡Hola! Bienvenido a CoreIA. Cuéntame un poco sobre tu proyecto para ayudarte a estructurarlo."

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