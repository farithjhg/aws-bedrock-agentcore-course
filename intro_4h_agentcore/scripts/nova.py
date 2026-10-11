"""Cliente del agente desplegado. Lo usan la demo (notebook) y la línea de comandos.

Uso:  python scripts/nova.py "¿Dónde está mi pedido TN-1003?" --cliente C-001 [--sesion ID]
"""
import argparse
import json
import subprocess
import sys
import uuid
from functools import lru_cache
from pathlib import Path

import boto3

INFRA = Path(__file__).resolve().parents[1] / "infra"


@lru_cache
def salidas_terraform() -> dict:
    """Lee las salidas de `terraform output` (ARN del agente, región, ID de memoria…)."""
    r = subprocess.run(["terraform", f"-chdir={INFRA}", "output", "-json"],
                       capture_output=True, text=True, check=True)
    return {k: v["value"] for k, v in json.loads(r.stdout).items()}


def nueva_sesion() -> str:
    # runtimeSessionId necesita al menos 33 caracteres.
    return f"sesion-{uuid.uuid4().hex}"


def invocar(prompt: str, cliente_id: str = "C-001", sesion: str | None = None) -> dict:
    s = salidas_terraform()
    cliente = boto3.client("bedrock-agentcore", region_name=s["region"])
    resp = cliente.invoke_agent_runtime(
        agentRuntimeArn=s["agent_runtime_arn"],
        runtimeSessionId=sesion or nueva_sesion(),
        payload=json.dumps({"prompt": prompt, "cliente_id": cliente_id}).encode("utf-8"),
    )
    # Leer todo y decodificar una vez: decodificar trozo a trozo rompe tildes y eñes.
    return json.loads(resp["response"].read().decode("utf-8"))


def recuerdos(cliente_id: str = "C-001") -> list[str]:
    """Preferencias que Memory ha extraído (largo plazo) para un cliente."""
    s = salidas_terraform()
    cliente = boto3.client("bedrock-agentcore", region_name=s["region"])
    namespace = s["namespace_preferencias"].replace("{actorId}", cliente_id)
    resp = cliente.list_memory_records(memoryId=s["memory_id"], namespace=namespace)
    return [r["content"]["text"] for r in resp.get("memoryRecordSummaries", [])]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # la consola de Windows (cp1252) no imprime emojis ni tildes
    p = argparse.ArgumentParser(description="Habla con Nova Assist desplegado en AgentCore Runtime")
    p.add_argument("prompt")
    p.add_argument("--cliente", default="C-001")
    p.add_argument("--sesion", default=None)
    a = p.parse_args()
    r = invocar(a.prompt, a.cliente, a.sesion)
    print(r["respuesta"])
    print(f"\n🚕 tokens: {r['tokens']}")
