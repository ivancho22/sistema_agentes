from langgraph.graph import StateGraph, END
from state import AgentState

# Importaciones de todos tus agentes
from agents.analyst import run_analyst_agent
from agents.architect import run_architect_agent
from agents.developer import run_developer_agent
from agents.designer import run_designer_agent  # 👈 Importante
from agents.sales import run_sales_agent        # 👈 Importante

# Inicialización del Grafo
workflow = StateGraph(AgentState)

# 1. REGISTRO DE NODOS (Asegúrate de que 'designer' esté aquí)
workflow.add_node("analyst", run_analyst_agent)
workflow.add_node("architect", run_architect_agent)
workflow.add_node("developer", run_developer_agent)
workflow.add_node("designer", run_designer_agent) # 👈 ¡FALTABA ESTA LÍNEA O ESTABA MAL NOMBRADA!
workflow.add_node("sales", run_sales_agent)

# 2. DEFINICIÓN DEL FLUJO Y ARISTAS
workflow.set_entry_point("analyst")
workflow.add_edge("analyst", "architect")
workflow.add_edge("architect", "developer")
workflow.add_edge("developer", "designer")
workflow.add_edge("designer", "sales")
workflow.add_edge("sales", END)

# Compilación del grafo
app_graph = workflow.compile()