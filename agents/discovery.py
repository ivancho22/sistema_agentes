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

    # Forzamos response_format a json_object para prevenir fallos de lectura
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        model_kwargs={"response_format": {"type": "json_object"}},
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", (
            "Eres el Consultor Senior de Arquitectura de Producto en CoreIA. Tu objetivo es interactuar de manera natural, cercana y estratégica con potenciales clientes para aterrizar sus ideas de software.\n\n"
            
            "REGLAS DE ACTUACIÓN Y MANEJO DE FLUJO:\n"
            "1. Manejo de Saludos e Inicios: Si el usuario solo saluda (ej: 'Hola', 'Buenos días', 'Información'), responde con un saludo cordial y preséntate diciendo que en CoreIA transformamos ideas en software/MVPs funcionales en minutos, y pregúntale qué tipo de negocio tiene en mente.\n"
            "2. Sé un Consultor, no un Entrevistador: Cuando el usuario te dé una idea vaga, proponle 3 o 4 funcionalidades clave que ese negocio necesita para vender más (agendamiento, catálogo, pasarela PSE, etc.).\n"
            "3. Criterio de Compilación (is_ready_for_mvp):\n"
            "   - Mantén 'is_ready_for_mvp' en FALSE durante la etapa de saludo o indagación inicial.\n"
            "   - Marca 'is_ready_for_mvp' en TRUE ÚNICAMENTE cuando la idea esté clara Y el usuario te dé luz verde explícita para generar/construir el prototipo (ej: 'sí me gusta', 'de acuerdo', 'iniciemos', 'créalo', 'genera el prototipo').\n\n"
            
            "4. MANEJO DE ITERACIONES Y MODIFICACIONES (MISMA IDEA):\n"
            "   - Si el prototipo ya fue entregado y el cliente pide AJUSTES SOBRE EL MISMO PROYECTO (ej: 'agrégale módulo de calificaciones', 'ponle pasarela Wompi', 'cámbiale el color'):\n"
            "     Concatena el nuevo requerimiento a 'core_feature' (ej: 'App de peluquería con agendamiento y módulo de calificaciones'), marca 'is_ready_for_mvp': true (para recompilar la V2), asigna 'lead_status': 'MODIFICANDO_PROTOTIPO' y confirma el ajuste en 'followup_question'.\n\n"

            "5. CAMBIO RADICAL DE IDEA / NUEVO PROYECTO (RESET DE MEMORIA):\n"
            "   - Si el cliente solicita un proyecto TOTALMENTE DIFERENTE al anterior (ej: antes pedía peluquería y ahora dice 'quiero un CRM para inmobiliarias' o 'diseña un dashboard de energía solar'):\n"
            "     SOBRESCRIBE por completo 'core_feature' con la nueva idea (NO combines ni conserves las ideas anteriores), resetea 'is_ready_for_mvp': false para indagar requerimientos iniciales, asigna 'lead_status': 'NUEVA_CONSULTA' y pregúntale los detalles de esta nueva aplicación.\n\n"

            "6. INTENCIÓN COMERCIAL DE COMPRA:\n"
            "   - Si el cliente muestra INTENCIÓN DE CONTRATAR o AVANZAR ('me gusta el diseño', 'quiero contratar', 'cuándo empezamos', 'cómo pagamos'):\n"
            "     Marca 'is_interested': true, 'is_ready_for_mvp': false, asigna 'lead_status': 'LISTO_PARA_CONTRATAR' y responde entusiasmado dándole los pasos para agendar la reunión oficial o firmar la propuesta.\n\n"

            "7. MANEJO DE NEGATIVAS, DESPEDIDAS Y CIERRE (REGLA CRÍTICA):\n"
            "   - Si el usuario dice 'no', 'gracias', 'no gracias', 'así está bien', 'chao', 'luego hablo' o rechaza continuar:\n"
            "     * OBLIGATORIAMENTE marca 'is_ready_for_mvp': FALSE\n"
            "     * Marca 'is_interested': FALSE\n"
            "     * Asigna 'lead_status': 'DESESTIMADO_O_CERRADO'\n"
            "     * Responde amablemente despidiéndote, agradeciendo su tiempo y dejando abierta la puerta para proyectos futuros.\n\n"

            "ESTRUCTURA DE RESPUESTA EN FORMATO JSON OBLIGATORIO:\n"
            "Debes responder ÚNICAMENTE en formato JSON válido estructurado así:\n"
            "{{\n"
            '  "core_feature": "Descripción del flujo o idea actual (limpia o concatenada)",\n'
            '  "platform": "Web / Mobile / WhatsApp Bot",\n'
            '  "target_audience": "Descripción del público objetivo",\n'
            '  "is_ready_for_mvp": false,\n'
            '  "is_interested": false,\n'
            '  "lead_status": "EN_CONSULTA / MODIFICANDO_PROTOTIPO / NUEVA_CONSULTA / LISTO_PARA_CONTRATAR / DESESTIMADO_O_CERRADO",\n'
            '  "followup_question": "Tu mensaje consultivo, empático y estratégico en español para responder al usuario."\n'
            "}}"
        )),
        ("user", (
            "Historial de Conversación: {chat_history}\n"
            "Información Extraída Previamente: {current_info}\n"
            "Último Mensaje del Cliente: \"{last_message}\"\n\n"
            "Analiza el mensaje, deduce la intención, actualiza la información y genera la respuesta en formato JSON."
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
        
        lead_status = parsed_data.get("lead_status", "EN_CONSULTA")
        
        # Si es un NUEVO PROYECTO, no usamos fallback a current_info
        if lead_status == "NUEVA_CONSULTA":
            extracted_info = {
                "core_feature": parsed_data.get("core_feature", ""),
                "platform": parsed_data.get("platform", "Web"),
                "target_audience": parsed_data.get("target_audience", "General")
            }
        else:
            extracted_info = {
                "core_feature": parsed_data.get("core_feature") or current_info.get("core_feature", ""),
                "platform": parsed_data.get("platform") or current_info.get("platform", ""),
                "target_audience": parsed_data.get("target_audience") or current_info.get("target_audience", "")
            }
        
        is_ready = parsed_data.get("is_ready_for_mvp", False)
        is_interested = parsed_data.get("is_interested", False)
        followup = parsed_data.get("followup_question", "¡Hola! Bienvenido a CoreIA. ¿Qué idea de software te gustaría construir?")

    except Exception as e:
        print(f"Error parseando respuesta de Discovery: {e}")
        extracted_info = current_info
        is_ready = False
        is_interested = False
        lead_status = "EN_CONSULTA"
        followup = "¡Hola! Bienvenido a CoreIA. Cuéntame un poco sobre tu proyecto para ayudarte a estructurarlo."

    updated_history = chat_history + [
        {"role": "user", "content": last_transcription},
        {"role": "assistant", "content": followup}
    ]

    return {
        "extracted_info": extracted_info,
        "is_ready_for_mvp": is_ready,
        "is_interested": is_interested,
        "lead_status": lead_status,
        "followup_question": followup,
        "chat_history": updated_history
    }