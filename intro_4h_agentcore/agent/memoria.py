"""AgentCore Memory. Si MEMORY_ID no está definido (ejecución local), el agente no tiene memoria."""
import os
import uuid

from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

# Terraform define la plantilla del namespace y la pasa aquí: una sola fuente de verdad.
PLANTILLA_PREFERENCIAS = os.environ.get("PREFS_NAMESPACE_TEMPLATE", "/users/{actorId}/preferences")


def crear_session_manager(session_id: str | None, actor_id: str):
    memory_id = os.environ.get("MEMORY_ID")
    if not memory_id:
        return None
    namespace = PLANTILLA_PREFERENCIAS.replace("{actorId}", actor_id)
    config = AgentCoreMemoryConfig(
        memory_id=memory_id,
        session_id=session_id or uuid.uuid4().hex,
        actor_id=actor_id,
        # Memoria a largo plazo: preferencias extraídas de conversaciones anteriores.
        retrieval_config={namespace: RetrievalConfig(top_k=3, relevance_score=0.3)},
    )
    return AgentCoreMemorySessionManager(config, os.environ.get("AWS_REGION"))
