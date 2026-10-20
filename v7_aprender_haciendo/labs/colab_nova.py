"""Preparación de Google Colab para el curso Nova Assist. En tu equipo no hace nada.

Cada notebook empieza con una celda ☁️ que, solo en Colab, clona el curso y ejecuta:

    import colab_nova
    colab_nova.preparar(capitulo=N)

Qué hace `preparar`:

1. **Drive.** Monta Google Drive y recupera tu estado del curso (lab_state.json, partidas/, NovaAssist/, datos/…)
   desde `MyDrive/NovaAssist_curso/labs`. Colab borra la máquina al cerrar la sesión y cada notebook abre una
   máquina nueva; Drive es lo que une un capítulo con el siguiente.
2. **Dependencias.** Instala las versiones de `requirements.txt` (una vez por sesión).
3. **CLI.** Instala Node.js (si el de Colab es anterior al 20) y la AgentCore CLI 0.31.1, si el capítulo la usa.
4. **Credenciales.** Carga tus credenciales de AWS desde los **Secretos de Colab** (icono de la llave):
   `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` (si son temporales) y, opcional, `AWS_REGION`.

Mientras trabajas, `lab_utils` copia a Drive lo que cambia: al guardar estado (`state_set`), después de cada comando
de la CLI y al guardar la partida. `guardar_en_drive()` lo fuerza en cualquier momento.
"""
from __future__ import annotations

import hashlib
import io
import os
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

LABS = Path(__file__).resolve().parent
MONTAJE = Path("/content/drive")
CARPETA_DRIVE = "NovaAssist_curso"
CLI_VERSION = "0.31.1"
NODE_MINIMO, NODE_INSTALAR = 20, 22
REGION_POR_DEFECTO = "eu-central-1"
SECRETOS = ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN", "AWS_REGION")

_MARCAS = Path("/content/.nova_colab")          # lo ya hecho en esta sesión de Colab
_NO_COPIAR = {"node_modules", ".venv", "__pycache__", ".ipynb_checkpoints", "cdk.out", ".git"}
# Si la carpeta no es un clon de git, se sincroniza solo lo que crea el curso
_GENERADO = ("lab_state.json", "lab_state.json.bak", "partidas", "NovaAssist", "datos", "lambda", "mcp_local")


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
        print(f"⚠ Sin Drive ({type(e).__name__}): tu estado se perderá al cerrar la sesión.")
        return None
    destino = MONTAJE / "MyDrive" / CARPETA_DRIVE / "labs"
    destino.mkdir(parents=True, exist_ok=True)
    os.environ["NOVA_DRIVE_DIR"] = str(destino)
    return destino


def _raiz_git() -> Path | None:
    for p in (LABS, *LABS.parents):
        if (p / ".git").exists():
            return p
    return None


def ficheros_propios() -> list[Path]:
    """Ficheros de labs/ que no vienen del repositorio: los que va creando el curso."""
    raiz = _raiz_git()
    versionados: set[Path] | None = None
    if raiz:
        r = subprocess.run(["git", "ls-files", "-z"], cwd=raiz, capture_output=True, text=True)
        if r.returncode == 0:
            versionados = {(raiz / f).resolve() for f in r.stdout.split("\0") if f}
    bases = [LABS] if versionados is not None else [LABS / g for g in _GENERADO]
    salida = []
    for base in bases:
        if base.is_file():
            salida.append(base)
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in _NO_COPIAR]
            for nombre in filenames:
                p = Path(dirpath) / nombre
                if nombre.endswith(".pyc") or p.is_symlink():
                    continue
                if versionados is not None and p.resolve() in versionados:
                    continue
                salida.append(p)
    return salida


def _distinto(origen: Path, destino: Path) -> bool:
    if not destino.exists():
        return True
    a, b = origen.stat(), destino.stat()
    return a.st_size != b.st_size or int(a.st_mtime) > int(b.st_mtime)


def _copiar(origen: Path, destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(origen, destino)
    try:
        shutil.copystat(origen, destino)
    except OSError:
        pass


def guardar_en_drive(rutas=None) -> int:
    """Copia a Drive los ficheros del curso que han cambiado (o solo `rutas`). Devuelve cuántos copió."""
    drive = carpeta_drive()
    if not drive:
        return 0
    copiados = 0
    for p in (rutas or ficheros_propios()):
        p = Path(p)
        if not p.exists():
            continue
        destino = drive / p.resolve().relative_to(LABS)
        try:
            if _distinto(p, destino):
                _copiar(p, destino)
                copiados += 1
        except OSError as e:
            print(f"⚠ No se pudo copiar {p.name} a Drive: {e}")
    return copiados


def borrar_de_drive(ruta: Path) -> None:
    drive = carpeta_drive()
    if drive:
        (drive / Path(ruta).resolve().relative_to(LABS)).unlink(missing_ok=True)


def recuperar_de_drive() -> int:
    """Copia de Drive a la máquina de Colab el estado guardado en sesiones anteriores."""
    drive = carpeta_drive()
    if not drive:
        return 0
    copiados = 0
    for dirpath, dirnames, filenames in os.walk(drive):
        dirnames[:] = [d for d in dirnames if d not in _NO_COPIAR]
        for nombre in filenames:
            origen = Path(dirpath) / nombre
            destino = LABS / origen.relative_to(drive)
            if _distinto(origen, destino):
                _copiar(origen, destino)
                copiados += 1
    return copiados


# --------------------------------------------------------------------------- dependencias
def instalar_dependencias() -> None:
    if _hecho("pip"):
        return
    paquetes = [linea.strip() for linea in (LABS / "requirements.txt").read_text(encoding="utf-8").splitlines()
                if linea.strip() and not linea.startswith("#") and not linea.startswith("jupyterlab")]
    print("… instalando dependencias de Python (1–2 min)")
    _ejecutar([sys.executable, "-m", "pip", "install", "-q", *paquetes])
    _marcar("pip")


def _version_mayor(exe: str | None) -> int:
    if not exe:
        return 0
    r = subprocess.run([exe, "--version"], capture_output=True, text=True)
    try:
        return int((r.stdout or "").strip().lstrip("v").split(".")[0])
    except ValueError:
        return 0


def instalar_node() -> None:
    if _version_mayor(shutil.which("node")) >= NODE_MINIMO:
        return
    base = f"https://nodejs.org/dist/latest-v{NODE_INSTALAR}.x/"
    sumas = urllib.request.urlopen(base + "SHASUMS256.txt", timeout=60).read().decode()
    sha, nombre = next(linea.split() for linea in sumas.splitlines() if linea.endswith("-linux-x64.tar.xz"))
    print(f"… instalando {nombre[:-len('.tar.xz')]}")
    datos = urllib.request.urlopen(base + nombre, timeout=300).read()
    if hashlib.sha256(datos).hexdigest() != sha:
        raise RuntimeError("La descarga de Node.js no coincide con su SHA-256")
    destino = Path("/opt")
    with tarfile.open(fileobj=io.BytesIO(datos), mode="r:xz") as t:
        t.extractall(destino, **({"filter": "data"} if hasattr(tarfile, "data_filter") else {}))
    bin_node = destino / nombre[:-len(".tar.xz")] / "bin"
    os.environ["PATH"] = f"{bin_node}:{os.environ['PATH']}"


def instalar_cli() -> None:
    exe = shutil.which("agentcore")
    if exe:
        r = subprocess.run([exe, "--version"], capture_output=True, text=True)
        if CLI_VERSION in (r.stdout + r.stderr):
            return
    print(f"… instalando la AgentCore CLI {CLI_VERSION}")
    _ejecutar([shutil.which("npm") or "npm", "install", "-g", "--no-audit", "--no-fund", f"@aws/agentcore@{CLI_VERSION}"])


def reinstalar_modulos_node() -> None:
    """Los node_modules no se guardan en Drive: se reinstalan en los proyectos recuperados que los necesiten."""
    proyecto = LABS / "NovaAssist"
    if not proyecto.exists():
        return
    for paquete in proyecto.rglob("package.json"):
        if "node_modules" in paquete.parts or (paquete.parent / "node_modules").exists():
            continue
        print(f"… npm install en {paquete.parent.relative_to(LABS)}")
        _ejecutar([shutil.which("npm") or "npm", "install", "--no-audit", "--no-fund"], cwd=paquete.parent)


# --------------------------------------------------------------------------- credenciales
def cargar_credenciales() -> bool:
    """Lee las credenciales de AWS de los Secretos de Colab y las deja en el entorno (también para la CLI)."""
    from google.colab import userdata  # noqa: PLC0415
    valores = {}
    for clave in SECRETOS:
        try:
            valor = userdata.get(clave)
        except Exception as e:  # noqa: BLE001  (SecretNotFoundError, NotebookAccessError…)
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
def preparar(capitulo: int, cli: bool | None = None, drive: bool = True) -> None:
    """Deja la sesión de Colab lista para el capítulo. Se puede repetir: lo ya hecho no se rehace."""
    if not en_colab():
        print("(No estás en Colab: no hace falta preparar nada)")
        return
    if cli is None:
        cli = capitulo not in (1, 2, 17)
    print(f"☁️ Preparando Colab para el capítulo {capitulo}")
    destino = montar_drive() if drive else None
    if destino:
        if _hecho("recuperado"):
            print(f"✔ Drive al día ({guardar_en_drive()} ficheros copiados)")
        else:
            n = recuperar_de_drive()
            _marcar("recuperado")
            print(f"✔ Estado del curso: MyDrive/{CARPETA_DRIVE} "
                  + (f"({n} ficheros recuperados)" if n else "(vacío: se irá llenando capítulo a capítulo)"))
    instalar_dependencias()
    print("✔ Dependencias de Python")
    if cli:
        instalar_node()
        instalar_cli()
        reinstalar_modulos_node()
        print(f"✔ Node.js {_version_mayor(shutil.which('node'))} y AgentCore CLI {CLI_VERSION}")
    ok = cargar_credenciales()
    print("\n✅ Listo. Sigue con la celda siguiente." if ok else "\n⚠ Completa los secretos y repite esta celda.")
