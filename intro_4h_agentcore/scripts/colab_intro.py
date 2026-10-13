"""Preparación de Google Colab para la demo de AgentCore en 4 horas. En tu equipo no hace nada.

La celda ☁️ de demo/demo_intro.ipynb, solo en Colab, clona el repositorio y ejecuta:

    import colab_intro
    colab_intro.preparar()

Qué hace `preparar`:

1. **Drive.** Monta Google Drive y recupera, de `MyDrive/NovaAssist_intro`, lo que une una sesión con la siguiente:
   `infra/terraform.tfvars`, el estado de Terraform (`infra/terraform.tfstate*`) y `build/agent.zip`.
   Sin eso, un `destroy` en otra sesión no sabría qué borrar.
2. **Herramientas.** Instala las dependencias de Python, `uv` (empaqueta el agente para Linux arm64) y Terraform.
   Los proveedores de Terraform van a `/content` (TF_DATA_DIR), no a Drive: pesan cientos de MB y se descargan en un minuto.
3. **Credenciales.** Carga tus credenciales de AWS desde los **Secretos de Colab** (icono de la llave):
   `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` (si son temporales) y, opcional, `AWS_REGION`.

`despliegue.py` copia el estado a Drive después de cada `apply` y `destroy`; `guardar_en_drive()` lo fuerza.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MONTAJE = Path("/content/drive")
CARPETA_DRIVE = "NovaAssist_intro"
TERRAFORM_RESERVA = "1.13.0"          # si no se puede consultar la última versión estable
TF_DATA_DIR = Path("/content/tf_data")   # proveedores de Terraform, fuera de Drive
BIN = Path("/content/bin")
REGION_POR_DEFECTO = "eu-west-1"
SECRETOS = ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_REGION")
# Lo que persiste entre sesiones de Colab (rutas relativas a la raíz de la intro)
PERSISTE = ("infra/terraform.tfvars", "infra/terraform.tfstate", "infra/terraform.tfstate.backup", "build/agent.zip",
            "infra/cuenta/terraform.tfstate", "infra/cuenta/terraform.tfstate.backup")

_MARCAS = Path("/content/.nova_intro")


def en_colab() -> bool:
    return "google.colab" in sys.modules


def _hecho(nombre: str) -> bool:
    return (_MARCAS / nombre).exists()


def _marcar(nombre: str) -> None:
    _MARCAS.mkdir(parents=True, exist_ok=True)
    (_MARCAS / nombre).touch()


def _ejecutar(args: list[str], cwd: Path | None = None) -> None:
    r = subprocess.run(args, cwd=str(cwd) if cwd else None, capture_output=True, text=True)
    if r.returncode:
        print((r.stdout or "")[-1500:], (r.stderr or "")[-1500:], sep="\n")
        raise RuntimeError(f"Falló: {' '.join(args[:4])}…")


# --------------------------------------------------------------------------- Drive
def carpeta_drive() -> Path | None:
    d = os.environ.get("NOVA_DRIVE_DIR")
    return Path(d) if d else None


def montar_drive() -> Path | None:
    from google.colab import drive  # noqa: PLC0415 (solo existe en Colab)
    try:
        if not (MONTAJE / "MyDrive").exists():
            drive.mount(str(MONTAJE))
    except Exception as e:  # noqa: BLE001
        print(f"⚠ Sin Drive ({type(e).__name__}): el estado de Terraform se perderá al cerrar la sesión. "
              "Ejecuta apagar() antes de cerrarla.")
        return None
    destino = MONTAJE / "MyDrive" / CARPETA_DRIVE
    destino.mkdir(parents=True, exist_ok=True)
    os.environ["NOVA_DRIVE_DIR"] = str(destino)
    return destino


def guardar_en_drive() -> int:
    """Copia a Drive las variables, el estado de Terraform y el zip del agente. Devuelve cuántos ficheros copió."""
    drive = carpeta_drive()
    if not drive:
        return 0
    copiados = 0
    for rel in PERSISTE:
        origen = RAIZ / rel
        destino = drive / rel
        if origen.exists():
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(origen, destino)
            copiados += 1
        elif destino.exists() and "terraform.tfstate" in rel:
            destino.unlink()   # el estado ya no existe (p. ej. tras destroy): tampoco en Drive
    return copiados


def recuperar_de_drive() -> int:
    drive = carpeta_drive()
    if not drive:
        return 0
    copiados = 0
    for rel in PERSISTE:
        origen = drive / rel
        if origen.exists():
            destino = RAIZ / rel
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(origen, destino)
            copiados += 1
    return copiados


# --------------------------------------------------------------------------- herramientas
def instalar_dependencias() -> None:
    if _hecho("pip"):
        return
    paquetes = [l.strip() for l in (RAIZ / "requirements.txt").read_text(encoding="utf-8").splitlines()
                if l.strip() and not l.startswith("#") and not l.startswith("jupyterlab")]
    print("… instalando dependencias de Python (1–2 min)")
    _ejecutar([sys.executable, "-m", "pip", "install", "-q", *paquetes, "uv"])
    _marcar("pip")


def _ultima_version_terraform() -> str:
    try:
        with urllib.request.urlopen("https://releases.hashicorp.com/terraform/index.json", timeout=30) as r:
            versiones = json.load(r)["versions"]
        estables = [v for v in versiones if "-" not in v and v.startswith("1.")]
        return max(estables, key=lambda v: [int(x) for x in v.split(".")])
    except Exception:  # noqa: BLE001
        return TERRAFORM_RESERVA


def instalar_terraform() -> None:
    if shutil.which("terraform"):
        return
    version = _ultima_version_terraform()
    base = f"https://releases.hashicorp.com/terraform/{version}/terraform_{version}"
    print(f"… instalando Terraform {version}")
    sumas = urllib.request.urlopen(f"{base}_SHA256SUMS", timeout=60).read().decode()
    nombre = f"terraform_{version}_linux_amd64.zip"
    sha = next(l.split()[0] for l in sumas.splitlines() if l.endswith(nombre))
    datos = urllib.request.urlopen(f"{base}_linux_amd64.zip", timeout=300).read()
    if hashlib.sha256(datos).hexdigest() != sha:
        raise RuntimeError("La descarga de Terraform no coincide con su SHA-256")
    BIN.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(datos)) as z:
        z.extract("terraform", BIN)
    (BIN / "terraform").chmod(0o755)
    os.environ["PATH"] = f"{BIN}:{os.environ['PATH']}"


# --------------------------------------------------------------------------- credenciales
def cargar_credenciales() -> bool:
    from google.colab import userdata  # noqa: PLC0415
    valores = {}
    for clave in SECRETOS:
        try:
            valor = userdata.get(clave)
        except Exception as e:  # noqa: BLE001
            if "Access" in type(e).__name__:
                print(f"⚠ Este notebook no tiene acceso al secreto {clave}: actívalo en el panel 🔑")
            valor = None
        if valor:
            valores[clave] = valor.strip()
    if not {"AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"} <= valores.keys():
        print("🔑 Faltan las credenciales de AWS. En el panel Secretos (icono de la llave, a la izquierda) añade\n"
              "   AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY y, si son temporales, AWS_SESSION_TOKEN;\n"
              "   activa «Acceso del notebook» y vuelve a ejecutar esta celda.")
        return False
    for clave in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"):
        os.environ[clave] = valores[clave]
    if "AWS_SESSION_TOKEN" in valores:
        os.environ["AWS_SESSION_TOKEN"] = valores["AWS_SESSION_TOKEN"]
    else:
        os.environ.pop("AWS_SESSION_TOKEN", None)
    region = valores.get("AWS_REGION") or os.environ.get("AWS_REGION") or REGION_POR_DEFECTO
    os.environ["AWS_REGION"] = os.environ["AWS_DEFAULT_REGION"] = region
    os.environ.pop("AWS_PROFILE", None)
    try:
        import boto3  # noqa: PLC0415
        yo = boto3.client("sts", region_name=region).get_caller_identity()
        print(f"✔ AWS: cuenta {yo['Account']} · {yo['Arn'].split(':')[-1]} · región {region}")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"✗ Las credenciales no funcionan ({type(e).__name__}). Si son temporales, puede que hayan caducado:\n"
              "   cópialas de nuevo en los Secretos y vuelve a ejecutar esta celda.")
        return False


# --------------------------------------------------------------------------- todo junto
def preparar(drive: bool = True) -> None:
    """Deja la sesión de Colab lista para la demo. Se puede repetir: lo ya hecho no se rehace."""
    if not en_colab():
        print("(No estás en Colab: no hace falta preparar nada)")
        return
    print("☁️ Preparando Colab para la demo de Nova Assist")
    os.environ["TF_DATA_DIR"] = str(TF_DATA_DIR)
    os.environ["NOVA_STAGING_DIR"] = "/content/build_staging"   # las dependencias empaquetadas, fuera de Drive
    os.environ.setdefault("TF_IN_AUTOMATION", "1")
    if drive and montar_drive():
        if _hecho("recuperado"):
            print(f"✔ Drive al día ({guardar_en_drive()} ficheros copiados)")
        else:
            n = recuperar_de_drive()
            _marcar("recuperado")
            estado = "hay un despliegue anterior: sus salidas siguen disponibles" if (RAIZ / "infra/terraform.tfstate").exists() \
                else "sin despliegue anterior"
            print(f"✔ Estado en MyDrive/{CARPETA_DRIVE} ({n} ficheros recuperados; {estado})")
    instalar_dependencias()
    print("✔ Dependencias de Python y uv")
    instalar_terraform()
    r = subprocess.run(["terraform", "version"], capture_output=True, text=True)
    print("✔", (r.stdout or "").strip().splitlines()[0] if r.returncode == 0 and r.stdout.strip() else "Terraform")
    ok = cargar_credenciales()
    print("\n✅ Listo. Sigue con la celda siguiente." if ok else "\n⚠ Completa los secretos y repite esta celda.")
