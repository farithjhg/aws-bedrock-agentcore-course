"""Empaqueta el agente como zip para AgentCore Runtime (Linux arm64), sin Docker.

Hace lo mismo que el CLI `agentcore`: instala las dependencias con uv para la plataforma
del Runtime (Amazon Linux 2023, GLIBC 2.34, arm64) y añade el código de agent/.

Uso:  python scripts/empaquetar.py      →  build/agent.zip
"""
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CODIGO = RAIZ / "agent"
BUILD = RAIZ / "build"
STAGING = BUILD / "staging"
ZIP = BUILD / "agent.zip"
PYTHON = "3.13"  # debe coincidir con runtime = "PYTHON_3_13" en infra/main.tf
PLATAFORMAS = ["aarch64-manylinux2014", "aarch64-manylinux_2_28", "aarch64-manylinux_2_34"]


def instalar_dependencias() -> None:
    if shutil.which("uv") is None:
        sys.exit("Falta uv: https://docs.astral.sh/uv/getting-started/installation/")
    for plataforma in PLATAFORMAS:
        shutil.rmtree(STAGING, ignore_errors=True)
        r = subprocess.run(
            ["uv", "pip", "install", "-r", str(CODIGO / "requirements.txt"), "--target", str(STAGING),
             "--python-version", PYTHON, "--python-platform", plataforma, "--only-binary", ":all:"],
            capture_output=True, text=True,
        )
        if r.returncode == 0:
            print(f"Dependencias instaladas para {plataforma}")
            return
        print(f"  {plataforma}: no disponible, probando la siguiente…")
        ultimo_error = r.stderr
    sys.exit(f"No se pudieron instalar las dependencias:\n{ultimo_error}")


def crear_zip() -> None:
    for f in CODIGO.glob("*.py"):
        shutil.copy2(f, STAGING / f.name)
    ZIP.unlink(missing_ok=True)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(STAGING.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts:
                z.write(f, f.relative_to(STAGING).as_posix())  # rutas con / aunque empaquetes en Windows
    print(f"{ZIP.relative_to(RAIZ)}: {ZIP.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # la consola de Windows (cp1252) no imprime «…»
    BUILD.mkdir(exist_ok=True)
    instalar_dependencias()
    crear_zip()
