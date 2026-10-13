"""Despliegue y apagado de la demo desde Python: lo mismo que los comandos del README, pero desde una celda.

    from despliegue import *
    preparar_cuenta(email_alertas="tu@correo")   # opcional: presupuesto con alertas (y Transaction Search) en infra/cuenta
    modelos()                  # lista los inference profiles eu.anthropic de la cuenta
    desplegar("eu.anthropic…") # empaqueta el agente, terraform init y apply
    apagar()                   # terraform destroy
    apagar_cuenta()            # terraform destroy de infra/cuenta (solo si la cuenta deja de usarse)

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
CUENTA = INFRA / "cuenta"              # el terreno de la cuenta: presupuesto y Transaction Search (pila aparte)
TFVARS = INFRA / "terraform.tfvars"
REGION_POR_DEFECTO = "eu-west-1"


def _terraform() -> str:
    exe = shutil.which("terraform")
    if not exe:
        raise RuntimeError("Falta Terraform. En tu equipo, instálalo (PREREQUISITOS.md §2); en Colab, ejecuta la celda ☁️.")
    return exe


def _tf(*args: str, capturar: bool = False, carpeta: Path | None = None) -> str:
    """Ejecuta terraform -chdir=infra … mostrando la salida en vivo (o capturándola)."""
    carpeta = carpeta or INFRA
    cmd = [_terraform(), f"-chdir={carpeta}", *args]
    print(f"$ terraform ({carpeta.relative_to(RAIZ)})", " ".join(a for a in args if not a.startswith("-var=email")))
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


def init(carpeta: Path | None = None) -> None:
    carpeta = carpeta or INFRA
    datos = Path(os.environ["TF_DATA_DIR"]) if os.environ.get("TF_DATA_DIR") else carpeta / ".terraform"
    if not (datos / "providers").exists():
        _tf("init", "-input=false", carpeta=carpeta)
    else:
        print("= terraform init ya hecho")


# --------------------------------------------------------------------------- el terreno de la cuenta (infra/cuenta)
def _env_cuenta():
    """TF_DATA_DIR propio para la pila de la cuenta cuando se trabaja con TF_DATA_DIR (Colab)."""
    previo = os.environ.get("TF_DATA_DIR")
    if previo:
        os.environ["TF_DATA_DIR"] = previo + "_cuenta"
    return previo


def _restaurar_env(previo) -> None:
    if previo:
        os.environ["TF_DATA_DIR"] = previo


def preparar_cuenta(email_alertas: str, presupuesto_usd: int = 20, observabilidad: bool = False,
                    region_aws: str | None = None) -> dict:
    """Prepara la cuenta: presupuesto con alertas y, si observabilidad=True, Transaction Search (vista de la consola).

    Es una pila aparte (infra/cuenta) que no se cae con apagar(): el presupuesto es de la cuenta, no de la demo.
    """
    assert "@" in email_alertas, "email_alertas: destinatario de las alertas del presupuesto"
    previo = _env_cuenta()
    try:
        init(CUENTA)
        _tf("apply", "-input=false", "-auto-approve", f"-var=region={region_aws or region()}",
            f"-var=presupuesto_usd={presupuesto_usd}", f"-var=email_alertas={email_alertas}",
            f"-var=observabilidad={'true' if observabilidad else 'false'}", carpeta=CUENTA)
        salidas = {k: v["value"] for k, v in json.loads(_tf("output", "-json", capturar=True, carpeta=CUENTA)).items()}
    finally:
        _restaurar_env(previo)
        _a_drive()
    print("\n✅ Cuenta preparada:", salidas)
    return salidas


def apagar_cuenta() -> None:
    """terraform destroy de infra/cuenta: borra el presupuesto y desactiva Transaction Search. Solo si la cuenta deja de usarse."""
    previo = _env_cuenta()
    try:
        init(CUENTA)
        _tf("destroy", "-input=false", "-auto-approve", carpeta=CUENTA)
    finally:
        _restaurar_env(previo)
        _a_drive()
    print("\n✅ Terreno de la cuenta apagado.")


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


__all__ = ["modelos", "escribir_tfvars", "empaquetar", "init", "desplegar", "salidas", "apagar", "preparar_cuenta", "apagar_cuenta"]
