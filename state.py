from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel, Field

class MVPInformation(BaseModel):
    """Estructura de la información requerida para el MVP"""
    target_audience: Optional[str] = Field(None, description="A quién va dirigida la app")
    core_feature: Optional[str] = Field(None, description="La funcionalidad principal e imprescindible")
    database_needed: Optional[bool] = Field(None, description="Si requiere almacenar datos de usuarios")
    platform: Optional[str] = Field(None, description="Web, Móvil, o Script de automatización")

class AgentState(TypedDict):
    # Transcripción del último audio recibido
    last_transcription: str
    # Información estructurada acumulada hasta el momento
    extracted_info: dict
    # Pregunta que el agente de recepción le hará de vuelta al cliente
    followup_question: Optional[str]
    # Historial de la conversación para mantener el contexto
    chat_history: List[dict]
    # Determina si ya estamos listos para pasar a los siguientes agentes
    is_ready_for_mvp: bool
    commercial_proposal: Optional[str]
    is_interested: Optional[bool]       # True si quiere contratar
    feedback_notes: Optional[str]       # Ajustes solicitados para la V2, V3...
    lead_status: Optional[str]          # 'EN_NEGOCIACION', 'INTERESADO', 'REVISION'