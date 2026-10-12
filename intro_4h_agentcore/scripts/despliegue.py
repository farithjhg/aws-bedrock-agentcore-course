"""Despliegue y apagado de la demo desde Python: lo mismo que los comandos del README, pero desde una celda.

    from despliegue import *
    modelos()                  # lista los inference profiles eu.anthropic de la cuenta
    desplegar("eu.anthropic…") # empaqueta el agente, terraform init y apply
    apagar()                   # terraform destroy

Funciona en tu equipo (con Terraform y uv instalados) y en Google Colab (la celda ☁️ los instala).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
INFRA = RAIZ / "infra"
TFVARS = INFRA / "terraform.tfvars"
REGION_POR_DEFECTO = "eu-west-1"


def _terraform() -> str:
    exe = shutil.which("terraform")
    if not exe:
        raise RuntimeError("Falta Terraform. En tu equipo, instálalo (PREREQUISITOS.md §2); en Colab, ejecuta la celda ☁️.")
    return exe


def _tf(*args: str, capturar: bool = False) -> str:
    """Ejecuta terraform -chdir=infra … mostrando la salida en vivo (o capturándola)."""
    cmd = [_terraform(), f"-chdir={INFRA}", *args]
    print("$ terraform", " ".join(args))
    r = subprocess.run(cmd, text=True, encoding="utf-8", capture_output=capturar)
    if r.returncode:
        if capturar:
            print(r.stderr)
        raise RuntimeError(f"terraform {args[0]} ha fallado (código {r.returncode})")
    return r.stdout if capturar else ""


def _a_drive() -> None:
    """En Colab, copia a Drive el estado de Terraform y las variables (colab_intro). En tu equipo no hace nada."""
    if os.environ.get("NOVA_DRIVE_DIR"):
        try:
            import colab_intro
            colab_intro.guardar_en_drive()
        except Exception as e:  # noqa: BLE001
            print(f"⚠ No se pudo copiar el estado a Drive: {e}")


def region() -> str:
    if TFVARS.exists():
        for linea in TFVARS.read_text(encoding="utf-8").splitlines():
            if linea.strip().startswith("region"):
                return linea.split("=", 1)[1].split("#")[0].strip().strip('"')
    return os.environ.get("AWS_REGION", REGION_POR_DEFECTO)


def modelos(region_aws: str | None = None) -> list[str]:
    """Inference profiles eu.anthropic disponibles en la cuenta (el paso 1 del README)."""
    import boto3
    bedrock = boto3.client("bedrock", region_name=region_aws or region())
    perfiles, token = [], None
    while True:
        resp = bedrock.list_inference_profiles(typeEquals="SYSTEM_DEFINED", **({"nextToken": token} if token else {}))
        perfiles += [p["inferenceProfileId"] for p in resp["inferenceProfileSummaries"]]
        token = resp.get("nextToken")
        if not token:
            break
    ids = sorted(p for p in perfiles if p.startswith("eu.anthropic"))
    for p in ids:
        print(p)
    return ids


def escribir_tfvars(model_id: str, region_aws: str | None = None) -> Path:
    """Escribe infra/terraform.tfvars (equivale a copiar y rellenar terraform.tfvars.example)."""
    assert "<" not in model_id and model_id.startswith(("eu.", "global.")), "Elige un inference profile de modelos()"
    TFVARS.write_text(f'region   = "{region_aws or region()}"\nmodel_id = "{model_id}"\n', encoding="utf-8")
    print("✔", TFVARS.relative_to(RAIZ), "→", model_id)
    _a_drive()
    return TFVARS


def empaquetar() -> Path:
    """build/agent.zip con el código de agent/ y sus dependencias para Linux arm64 (scripts/empaquetar.py)."""
    r = subprocess.run([sys.executable, str(RAIZ / "scripts" / "empaquetar.py")], text=True, encoding="utf-8")
    if r.returncode:
        raise RuntimeError("El empaquetado ha fallado")
    return RAIZ / "build" / "agent.zip"


def init() -> None:
    if not (Path(os.environ.get("TF_DATA_DIR", INFRA / ".terraform")) / "providers").exists():
        _tf("init", "-input=false")
    else:
        print("= terraform init ya hecho")


def desplegar(model_id: str | None = None, region_aws: str | None = None) -> dict:
    """Empaqueta, inicializa y aplica. Con model_id escribe terraform.tfvars; sin él, usa el que ya haya."""
    if model_id:
        escribir_tfvars(model_id, region_aws)
    elif not TFVARS.exists():
        raise RuntimeError("Falta infra/terraform.tfvars: llama a desplegar(model_id=…) con un perfil de modelos()")
    empaquetar()
    init()
    try:
        _tf("apply", "-input=false", "-auto-approve")
    finally:
        _a_drive()
    s = salidas()
    print("\n✅ Desplegado:", s.get("agent_runtime_arn"))
    return s


def salidas() -> dict:
    """Las salidas de Terraform (ARN del agente, región, ID de memoria…)."""
    return {k: v["value"] for k, v in json.loads(_tf("output", "-json", capturar=True)).items()}


def apagar() -> None:
    """terraform destroy: borra el Runtime, la Memory, el rol y el bucket (con sus versiones del zip)."""
    init()
    try:
        _tf("destroy", "-input=false", "-auto-approve")
    finally:
        _a_drive()
    print("\n✅ Todo apagado. Comprueba mañana en Cost Explorer que no hay cargos nuevos.")


__all__ = ["modelos", "escribir_tfvars", "empaquetar", "init", "desplegar", "salidas", "apagar"]
