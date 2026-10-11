"""Nova Assist: el agente de atención al cliente de TiendaNova, desplegado en AgentCore Runtime.

Payload de entrada: {"prompt": "...", "cliente_id": "C-001"}
Respuesta:          {"respuesta": "...", "cliente_id": "...", "tokens": {...}}

Nota sobre el estado: creamos un Agent nuevo en cada invocación a propósito, para que
nunca se comparta estado entre clientes. Runtime sí mantiene la misma microVM para el
mismo runtimeSessionId; la continuidad de la conversación la pone AgentCore Memory.
"""
import os

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel

from herramientas import crear_herramientas
from memoria import crear_session_manager

SYSTEM_PROMPT = """Eres Nova Assist, el asistente de atención al cliente de TiendaNova.
- Responde en español, breve y amable.
- Usa siempre las herramientas para datos de pedidos, plazos e importes; nunca los inventes.
- Si una herramienta devuelve un error o dice que algo no es posible, explícalo con claridad.
- Si conoces preferencias del cliente (por ejemplo, su canal de contacto), tenlas en cuenta."""

app = BedrockAgentCoreApp()


def crear_agente(cliente_id: str, session_id: str | None = None) -> Agent:
    modelo = BedrockModel(
        model_id=os.environ["MODEL_ID"],
        region_name=os.environ.get("AWS_REGION", "eu-west-1"),
        temperature=0.2,
    )
    return Agent(
        model=modelo,
        system_prompt=SYSTEM_PROMPT,
        tools=crear_herramientas(cliente_id),
        session_manager=crear_session_manager(session_id, cliente_id),
        callback_handler=None,
    )


@app.entrypoint
def invoke(payload, context):
    cliente_id = payload.get("cliente_id", "C-001")
    session_id = getattr(context, "session_id", None)
    agente = crear_agente(cliente_id, session_id)
    resultado = agente(payload["prompt"])
    uso = resultado.metrics.accumulated_usage
    return {
        "respuesta": str(resultado).strip(),
        "cliente_id": cliente_id,
        "tokens": {"entrada": uso.get("inputTokens", 0), "salida": uso.get("outputTokens", 0)},
    }


if __name__ == "__main__":
    app.run()
