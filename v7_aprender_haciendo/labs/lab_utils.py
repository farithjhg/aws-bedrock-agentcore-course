"""Utilidades compartidas por los notebooks del laboratorio Nova Assist (AgentCore, octubre 2026).

Uso en cada notebook:
    from lab_utils import *
"""
from __future__ import annotations

import base64
import importlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from types import SimpleNamespace

LAB_ROOT = Path(__file__).resolve().parent
PROJECT = LAB_ROOT / "NovaAssist"                 # lo crea el Lab 02
AGENT_DIR = PROJECT / "app" / "NovaAgent"
STATE_FILE = LAB_ROOT / "lab_state.json"         # ¡no versionar! puede contener secretos de laboratorio
DEFAULT_REGION = "eu-west-1"
EN_COLAB = "google.colab" in sys.modules      # en Colab, la celda ☁️ de cada notebook prepara la sesión (colab_nova.py)


# --------------------------------------------------------------------------- Google Drive (solo Colab)
def _a_drive(*rutas) -> None:
    """En Colab, copia a Drive lo que ha cambiado (o solo `rutas`). En tu equipo no hace nada."""
    if not os.environ.get("NOVA_DRIVE_DIR"):
        return
    try:
        import colab_nova
        colab_nova.guardar_en_drive(list(rutas) or None)
    except Exception as e:  # noqa: BLE001
        print(f"⚠ No se pudo copiar a Drive: {e}")


def guardar_en_drive() -> None:
    """En Colab, guarda ya en Google Drive el estado del curso (se hace solo al guardar estado, tras la CLI y al
    guardar la partida). En tu equipo no hace falta: los ficheros ya están en tu disco."""
    if not os.environ.get("NOVA_DRIVE_DIR"):
        print("(Sin Drive: en tu equipo no hace falta; en Colab, ejecuta la celda ☁️ del principio)")
        return
    import colab_nova
    print(f"☁️ Drive al día ({colab_nova.guardar_en_drive()} ficheros copiados)")


# --------------------------------------------------------------------------- estado compartido
def state_load() -> dict:
    return json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else {}


def state_get(key: str, default=None):
    return state_load().get(key, default)


def state_set(**values) -> None:
    state = state_load()
    state.update(values)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    _a_drive(STATE_FILE)
    for k, v in values.items():
        shown = "********" if "SECRET" in k or "PASSWORD" in k else v
        print(f"✔ {k} = {shown}")


def state_show() -> None:
    state = state_load()
    if not state:
        print("(estado vacío: empieza por el notebook 00)")
    for k, v in state.items():
        shown = "********" if "SECRET" in k or "PASSWORD" in k else v
        print(f"{k:30} {shown}")


def region() -> str:
    return state_get("REGION", DEFAULT_REGION)


def account_id() -> str:
    import boto3
    return boto3.client("sts").get_caller_identity()["Account"]


def requiere(*keys: str) -> None:
    """Falla pronto si falta algún valor que debía guardar un lab anterior."""
    faltan = [k for k in keys if not state_get(k)]
    if faltan:
        raise RuntimeError(f"Faltan en lab_state.json: {faltan}. Revisa los labs anteriores.")
    print("✔ prerrequisitos OK:", ", ".join(keys))


# --------------------------------------------------------------------------- configuración del agente
def write_settings() -> None:
    """Genera app/NovaAgent/settings.py desde lab_state.json (única fuente de verdad de IDs y URLs).

    Las variables de entorno siguen pudiendo sobrescribir cada valor en el Runtime.
    """
    s = state_load()
    content = f'''"""Generado por lab_utils.write_settings(): no editar a mano."""
import os

REGION = os.environ.get("AWS_REGION", {s.get("REGION", DEFAULT_REGION)!r})
MODEL_ID = os.environ.get("NOVA_MODEL_ID", {s.get("MODEL_ID", "")!r})
MEMORY_ID = os.environ.get("NOVA_MEMORY_ID", {s.get("MEMORY_ID", "")!r})
GATEWAY_URL = os.environ.get("NOVA_GATEWAY_URL", {s.get("GATEWAY_URL", "")!r})
GATEWAY_CREDENTIAL_PROVIDER = {s.get("GATEWAY_CREDENTIAL_PROVIDER", "")!r}
GATEWAY_SCOPES = {s.get("GATEWAY_SCOPES", ["gateway/invoke"])!r}
# namespace de memoria a largo plazo -> [top_k, relevance_score]
LTM_NAMESPACES = {s.get("LTM_NAMESPACES", {})!r}
# Bedrock Guardrails aplicado en la llamada al modelo (capítulo 10); vacío = sin guardrail
GUARDRAIL_ID = {s.get("GUARDRAIL_ID", "")!r}
GUARDRAIL_VERSION = {s.get("GUARDRAIL_VERSION", "")!r}
'''
    AGENT_DIR.mkdir(parents=True, exist_ok=True)
    (AGENT_DIR / "settings.py").write_text(content, encoding="utf-8")
    print(f"✔ settings.py regenerado en {AGENT_DIR}")


def add_dependency(dep: str) -> None:
    """Añade una dependencia al pyproject.toml del agente (lista `dependencies = [...]`)."""
    import re

    p = AGENT_DIR / "pyproject.toml"
    text = p.read_text(encoding="utf-8")
    if f'"{dep}"' in text:
        print(f"= {dep} ya estaba")
        return
    new, n = re.subn(r"(dependencies\s*=\s*\[)", lambda m: m.group(1) + f'\n    "{dep}",', text, count=1)
    if not n:
        raise RuntimeError("No encuentro 'dependencies = [' en pyproject.toml: añade la dependencia a mano.")
    p.write_text(new, encoding="utf-8")
    print(f"✔ añadida {dep}")


# Versiones probadas juntas (octubre 2026). strands-agents >= 1.57 rompe la integración de Memory
# de bedrock-agentcore 1.22 (ImportError: BidiAfterInvocationEvent).
VERSIONES = {
    "strands-agents": "strands-agents==1.55.1",
    "bedrock-agentcore": "bedrock-agentcore[strands-agents]==1.22.0",
    "strands-agents-tools": "strands-agents-tools[agent_core_code_interpreter]==0.8.9",
    "mcp": "mcp==1.30.0",
}


def fijar_dependencia(spec: str) -> None:
    """Fija una dependencia del agente desplegado: reemplaza la entrada existente del paquete o la añade."""
    import re
    base = re.split(r"[\[<>=!~ ]", spec, maxsplit=1)[0]
    p = AGENT_DIR / "pyproject.toml"
    text = p.read_text(encoding="utf-8")
    patron = re.compile(r'"' + re.escape(base) + r'(\[[^\]]*\])?\s*([<>=!~][^"]*)?"')
    if patron.search(text):
        text, accion = patron.sub(f'"{spec}"', text, count=1), "fijada"
    else:
        text, n = re.subn(r"(dependencies\s*=\s*\[)", lambda m: m.group(1) + f'\n    "{spec}",', text, count=1)
        if not n:
            raise RuntimeError("No encuentro 'dependencies = [' en pyproject.toml: añade la dependencia a mano.")
        accion = "añadida"
    p.write_text(text, encoding="utf-8")
    print(f"✔ {spec} ({accion})")


def agentcore_json() -> dict:
    return json.loads((PROJECT / "agentcore" / "agentcore.json").read_text(encoding="utf-8"))


def agentcore_json_write(data: dict) -> None:
    """Escribe agentcore.json (tras editarlo desde un notebook). Valida después con `agentcore validate`."""
    (PROJECT / "agentcore" / "agentcore.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                                                           encoding="utf-8")
    print("✔ agentcore.json actualizado")


def runtime_entry(nombre: str = "NovaAgent") -> dict:
    """Entrada del runtime en agentcore.json (clave `runtimes`), para declarar autorizador, cabeceras o endpoints."""
    data = agentcore_json()
    for rt in data.get("runtimes", []):
        if rt.get("name") == nombre:
            return rt
    raise RuntimeError(f"No encuentro el runtime {nombre} en agentcore.json")


def runtime_id() -> str:
    """ID del Runtime a partir del ARN guardado (arn:aws:bedrock-agentcore:…:runtime/<id>)."""
    requiere("AGENT_ARN")
    return state_get("AGENT_ARN").rsplit("/", 1)[-1]


def anadir_permiso_runtime(nombre: str, sentencias: list[dict], runtime: str = "NovaAgent") -> None:
    """Añade al rol de ejecución del Runtime un permiso mínimo (fichero JSON + `additionalPolicies` en agentcore.json).

    El rol que crea la CLI permite invocar modelos, Memory, Identity y configuration bundles; lo demás (Guardrails,
    Code Interpreter…) se concede de forma explícita. Después: `agentcore validate` y `agentcore deploy`.
    """
    ruta = AGENT_DIR / "permisos" / f"{nombre}.json"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps({"Version": "2012-10-17", "Statement": sentencias}, indent=2) + "\n", encoding="utf-8")
    data = agentcore_json()
    entrada = next(rt for rt in data["runtimes"] if rt["name"] == runtime)
    relativa = f"permisos/{nombre}.json"
    politicas = entrada.setdefault("additionalPolicies", [])
    if relativa not in politicas:
        politicas.append(relativa)
    agentcore_json_write(data)
    print(f"✔ permiso «{nombre}» para {runtime}: {[a for st in sentencias for a in st['Action']]}")


def cli(comando: str, cwd=None) -> int:
    """Ejecuta un comando de la AgentCore CLI (u otro) de forma portable, también en Windows.

    En Windows, `agentcore` es un .cmd de npm: hace falta `shell=True`. La salida se muestra en vivo.
    """
    import subprocess
    print("$", comando)
    r = subprocess.run(comando, shell=True, cwd=str(cwd or PROJECT), text=True)
    _a_drive()
    return r.returncode


def cli_args(*args: str, cwd=None, capturar: bool = False):
    """Ejecuta `agentcore` con argumentos sueltos (sin shell): los JSON y textos con espacios llegan intactos.

    Funciona también en Windows, donde la CLI es un .cmd de npm (se localiza con shutil.which).
    Con capturar=True devuelve la salida estándar (para `--json`).
    """
    import shutil
    import subprocess
    exe = shutil.which("agentcore") or "agentcore"
    print("$ agentcore", " ".join(a if len(a) < 60 else a[:57] + "…" for a in args))
    r = subprocess.run([exe, *args], cwd=str(cwd or PROJECT), text=True, encoding="utf-8",
                       capture_output=capturar)
    _a_drive()
    if capturar:
        if r.returncode:
            print(r.stderr)
        return r.stdout
    return r.returncode


def arbol(ruta=None, profundidad: int = 3, ignorar=("cdk", "node_modules", ".venv", "__pycache__", ".git")) -> None:
    """Lista un árbol de ficheros en Python (sustituye a `!find`, que en Windows es otro comando)."""
    base = Path(ruta or PROJECT)
    for p in sorted(base.rglob("*")):
        rel = p.relative_to(base)
        if any(parte in ignorar for parte in rel.parts) or len(rel.parts) > profundidad:
            continue
        print(("📁 " if p.is_dir() else "   ") + str(rel))


def comprobar_gateway() -> None:
    """Guardia del capítulo 7: comprueba que el deploy dejó el Gateway listo antes de seguir.

    Si falta algo, para con un mensaje claro en lugar de dejar que el siguiente paso falle con un error confuso.
    """
    faltan = []
    g = buscar_gateway("NovaGateway")
    if g:
        state_set(GATEWAY_URL=g["url"], GATEWAY_ARN=g["arn"])
    else:
        faltan.append("el Gateway NovaGateway no está desplegado")
    creds = [c.get("name") for c in agentcore_json().get("credentials", [])]
    prov = next((c for c in creds if c and "NovaGateway" in c), None)
    if prov:
        state_set(GATEWAY_CREDENTIAL_PROVIDER=prov)
    else:
        faltan.append("no hay credential provider para NovaGateway en agentcore.json (lo crea `agentcore deploy` al pedir el client id y el secret M2M)")
    if faltan:
        raise RuntimeError("⛔ Antes de continuar, despliega con `cli(\"agentcore deploy --yes\")`; si la CLI pide datos, "
                           "ejecuta `cd labs/NovaAssist && agentcore deploy` en una terminal (en Colab, la Terminal del panel "
                           "izquierdo, desde la carpeta del curso) e introduce el client id y el secret del pool M2M. "
                           "Falta: " + "; ".join(faltan))
    print("✔ Gateway listo:", state_get("GATEWAY_URL"), "· credential provider:", prov)


# --------------------------------------------------------------------------- localizar recursos desplegados
def _control():
    import boto3
    return boto3.client("bedrock-agentcore-control", region_name=region())


def buscar_runtime(fragmento: str = "NovaAgent") -> str | None:
    """Busca el ARN del runtime cuyo nombre contiene `fragmento`. Si falla, usa `agentcore status`."""
    try:
        for r in _control().list_agent_runtimes().get("agentRuntimes", []):
            if fragmento.lower() in r.get("agentRuntimeName", "").lower():
                print("✔ runtime:", r["agentRuntimeName"])
                return r["agentRuntimeArn"]
    except Exception as e:  # noqa: BLE001
        print("No se pudo listar runtimes:", e)
    print("⚠ No encontrado: copia el ARN de `agentcore status` y usa state_set(AGENT_ARN=...)")
    return None


def buscar_memoria(fragmento: str = "NovaMemory") -> str | None:
    try:
        for m in _control().list_memories().get("memories", []):
            mid = m.get("id") or m.get("memoryId", "")
            if fragmento.lower() in mid.lower():
                print("✔ memoria:", mid)
                return mid
    except Exception as e:  # noqa: BLE001
        print("No se pudo listar memorias:", e)
    print("⚠ No encontrada: copia el ID de `agentcore status` y usa state_set(MEMORY_ID=...)")
    return None


def estrategias_memoria(memory_id: str | None = None) -> list[dict]:
    """Estrategias REALES de la memoria: tipo, id y plantillas de namespace (no las supongas: la CLI crea las suyas)."""
    mem = _control().get_memory(memoryId=memory_id or state_get("MEMORY_ID"))["memory"]
    return [{"tipo": st.get("type", "?"), "id": st.get("strategyId"), "nombre": st.get("name", ""),
             "plantillas": list(st.get("namespaceTemplates") or st.get("namespaces") or [])}
            for st in mem.get("strategies", [])]


def namespaces_memoria(memory_id: str | None = None, mostrar: bool = True) -> list[tuple[str, list[str]]]:
    """(tipo, plantillas de namespace) de cada estrategia de la memoria."""
    salida = []
    for st in estrategias_memoria(memory_id):
        salida.append((st["tipo"], st["plantillas"]))
        if mostrar:
            print(f"• {st['tipo']:16} {st['nombre']}  →  {st['plantillas']}")
    return salida


def plantar_registro(actor_id: str, texto: str, tipo: str = "SEMANTIC", memory_id: str | None = None) -> str:
    """Escribe un registro de largo plazo como lo haría el extractor (para el experimento de envenenamiento)."""
    import boto3
    from datetime import datetime, timezone
    mid = memory_id or state_get("MEMORY_ID")
    st = next(e for e in estrategias_memoria(mid) if e["tipo"] == tipo)
    ns = namespace_resuelto(st["plantillas"][0].split("{sessionId}")[0], actor_id)
    r = boto3.client("bedrock-agentcore", region_name=region()).batch_create_memory_records(
        memoryId=mid, records=[{"requestIdentifier": "experimento-envenenamiento", "namespaces": [ns],
                                "content": {"text": texto}, "timestamp": datetime.now(timezone.utc),
                                "memoryStrategyId": st["id"]}])
    if r.get("failedRecords"):
        raise RuntimeError(r["failedRecords"])
    print(f"🧪 registro escrito en {ns}: «{texto}»")
    return r["successfulRecords"][0]["memoryRecordId"]


def buscar_en_memoria(actor_id: str, consulta: str, top_k: int = 5, memory_id: str | None = None) -> list[dict]:
    """Lo que recuperaría el agente de la memoria a largo plazo para una consulta (lo que entra en su contexto)."""
    import boto3
    mid = memory_id or state_get("MEMORY_ID")
    dp = boto3.client("bedrock-agentcore", region_name=region())
    salida = []
    for tipo, prefijo in _prefijos_cliente(actor_id, mid):
        if tipo == "SUMMARIZATION":
            continue
        resp = dp.retrieve_memory_records(memoryId=mid, namespace=prefijo,
                                          searchCriteria={"searchQuery": consulta, "topK": top_k})
        for rec in resp.get("memoryRecordSummaries", []):
            salida.append({"tipo": tipo, "score": round(rec.get("score") or 0, 3),
                           "texto": rec.get("content", {}).get("text", "")})
    for r in sorted(salida, key=lambda r: -r["score"]):
        print(f"• [{r['tipo']} · {r['score']}] {r['texto']}")
    return salida


# top_k y umbral de relevancia por tipo de estrategia (ajústalos en el capítulo 6 si el contexto crece)
RETRIEVAL_POR_TIPO = {"USER_PREFERENCE": [5, 0.6], "SEMANTIC": [10, 0.4], "SUMMARIZATION": [3, 0.3]}


def configurar_ltm(memory_id: str | None = None) -> dict:
    """Construye LTM_NAMESPACES a partir de las plantillas reales de la memoria y regenera settings.py.

    Las plantillas se guardan tal cual ({actorId}, {sessionId}): el session manager de Strands las resuelve.
    """
    ltm = {}
    for tipo, plantillas in namespaces_memoria(memory_id):
        for plantilla in plantillas:
            if "{sessionId}" in plantilla:
                continue   # los resúmenes son de UNA sesión: no sirven para reconocer al cliente mañana
            ltm[plantilla] = RETRIEVAL_POR_TIPO.get(tipo, [5, 0.4])
    if not ltm:
        raise RuntimeError("La memoria no tiene estrategias de largo plazo: revisa `agentcore add memory --strategies …`.")
    state_set(LTM_NAMESPACES=ltm)
    write_settings()
    return ltm


def namespace_resuelto(plantilla: str, actor_id: str, session_id: str = "") -> str:
    """Resuelve una plantilla de namespace para un cliente (para listar o borrar registros desde el notebook)."""
    return plantilla.format(actorId=actor_id, sessionId=session_id, memoryStrategyId="")


def _prefijos_cliente(actor_id: str, memory_id: str | None = None) -> list[tuple[str, str]]:
    """(tipo de estrategia, prefijo de namespace) de un cliente. En las plantillas por sesión se corta en {sessionId}."""
    salida = []
    for tipo, plantillas in namespaces_memoria(memory_id, mostrar=False):
        for plantilla in plantillas:
            base = plantilla.split("{sessionId}")[0]
            salida.append((tipo, namespace_resuelto(base, actor_id)))
    return salida


def registros_memoria(actor_id: str, tipo: str | None = None, memory_id: str | None = None) -> list[dict]:
    """Registros de largo plazo de un cliente (opcionalmente de un tipo: USER_PREFERENCE, SEMANTIC, SUMMARIZATION)."""
    import boto3
    mid = memory_id or state_get("MEMORY_ID")
    dp = boto3.client("bedrock-agentcore", region_name=region())
    registros = []
    for t, prefijo in _prefijos_cliente(actor_id, mid):
        if tipo and t != tipo:
            continue
        token = None
        while True:
            resp = dp.list_memory_records(memoryId=mid, namespace=prefijo, **({"nextToken": token} if token else {}))
            for rec in resp.get("memoryRecordSummaries", []):
                registros.append({"tipo": t, "id": rec["memoryRecordId"], "texto": rec.get("content", {}).get("text", ""),
                                  "namespace": (rec.get("namespaces") or [prefijo])[0]})
            token = resp.get("nextToken")
            if not token:
                break
    return registros


def esperar_registros(actor_id: str, tipo: str | None = None, contiene: str | None = None,
                      intentos: int = 10, espera: int = 30) -> list[dict]:
    """Espera a que la extracción asíncrona de Memory produzca registros (suele tardar entre 30 s y 2 min)."""
    import time
    for _ in range(intentos):
        recs = [r for r in registros_memoria(actor_id, tipo)
                if not contiene or contiene.lower() in r["texto"].lower()]
        if recs:
            for r in recs:
                print(f"• [{r['tipo']}] {r['texto']}")
            return recs
        print(f"Aún sin registros; esperando {espera} s…")
        time.sleep(espera)
    print("⚠ No han aparecido registros: la extracción la decide un modelo y puede no guardar nada.")
    return []


def borrar_memoria_cliente(actor_id: str, memory_id: str | None = None, incluir_eventos: bool = True) -> int:
    """Derecho de supresión (RGPD): borra los registros de largo plazo de un cliente y, opcionalmente,
    los eventos de corto plazo de todas sus sesiones."""
    import boto3
    mid = memory_id or state_get("MEMORY_ID")
    dp = boto3.client("bedrock-agentcore", region_name=region())
    borrados = 0
    for r in registros_memoria(actor_id, memory_id=mid):
        dp.delete_memory_record(memoryId=mid, memoryRecordId=r["id"])
        borrados += 1
    eventos = 0
    if incluir_eventos:
        token = None
        while True:
            resp = dp.list_sessions(memoryId=mid, actorId=actor_id, **({"nextToken": token} if token else {}))
            for ses in resp.get("sessionSummaries", []):
                tk = None
                while True:
                    ev = dp.list_events(memoryId=mid, sessionId=ses["sessionId"], actorId=actor_id,
                                        includePayloads=False, **({"nextToken": tk} if tk else {}))
                    for e in ev.get("events", []):
                        dp.delete_event(memoryId=mid, sessionId=ses["sessionId"], eventId=e["eventId"], actorId=actor_id)
                        eventos += 1
                    tk = ev.get("nextToken")
                    if not tk:
                        break
            token = resp.get("nextToken")
            if not token:
                break
    print(f"🧹 {actor_id}: {borrados} registro(s) de largo plazo y {eventos} evento(s) de corto plazo borrados")
    return borrados + eventos


def buscar_gateway(fragmento: str = "NovaGateway") -> dict | None:
    """Devuelve {'url': ..., 'arn': ...} del gateway cuyo nombre contiene `fragmento`."""
    try:
        ctl = _control()
        for g in ctl.list_gateways().get("items", []):
            if fragmento.lower() in g.get("name", "").lower():
                d = ctl.get_gateway(gatewayIdentifier=g["gatewayId"])
                url = d["gatewayUrl"]
                url = url if url.rstrip("/").endswith("/mcp") else url.rstrip("/") + "/mcp"
                print("✔ gateway:", g["name"])
                return {"url": url, "arn": d["gatewayArn"]}
    except Exception as e:  # noqa: BLE001
        print("No se pudo listar gateways:", e)
    print("⚠ No encontrado: copia URL y ARN de `agentcore status` y usa state_set(GATEWAY_URL=..., GATEWAY_ARN=...)")
    return None


def buscar_gateway_http(fragmento: str) -> dict | None:
    """Gateway HTTP (protocolo None, capítulo 13): {'id', 'url_base'}; los targets se llaman en <url_base>/<target>/invocations."""
    ctl = _control()
    for g in ctl.list_gateways().get("items", []):
        if fragmento.lower() in g.get("name", "").lower():
            d = ctl.get_gateway(gatewayIdentifier=g["gatewayId"])
            url = d.get("gatewayUrl") or f"https://{g['gatewayId']}.gateway.bedrock-agentcore.{region()}.amazonaws.com"
            url = url.rstrip("/")
            url = url[:-4] if url.endswith("/mcp") else url
            print("✔ gateway:", g["name"], "·", url)
            return {"id": g["gatewayId"], "url_base": url}
    print("⚠ No encontrado: ¿has desplegado? (agentcore status)")
    return None


# --------------------------------------------------------------------------- invocación

# --------------------------------------------------------------------------- taxímetro (tokens y coste)
_TAXI: dict[str, dict] = {}

# Fórmula ÚNICA de coste del curso (la usan el taxímetro y las páginas de teoría de los capítulos 6 y 12):
#   coste = entrada × P_in + caché_leída × 0,1 × P_in + caché_escrita × 1,25 × P_in + salida × P_out
# (precios por token; multiplicadores de prompt caching de los modelos Claude en Bedrock, TTL de 5 minutos)
FACTOR_CACHE_LECTURA = 0.10
FACTOR_CACHE_ESCRITURA = 1.25


def precios(entrada_por_millon: float, salida_por_millon: float) -> None:
    """Precio del modelo por millón de tokens (consúltalo en la página de precios de Bedrock)."""
    state_set(PRECIO_ENTRADA_MTOK=entrada_por_millon, PRECIO_SALIDA_MTOK=salida_por_millon)


def _coste(entrada: int, salida: int, cache_leida: int = 0, cache_escrita: int = 0) -> float | None:
    pe, ps = state_get("PRECIO_ENTRADA_MTOK"), state_get("PRECIO_SALIDA_MTOK")
    if pe is None or ps is None:
        return None
    return (entrada + cache_leida * FACTOR_CACHE_LECTURA + cache_escrita * FACTOR_CACHE_ESCRITURA) / 1e6 * pe \
        + salida / 1e6 * ps


def taximetro_sumar(sesion: str, uso: dict | None) -> None:
    """Acumula el uso de tokens de una invocación en la sesión (conversación) correspondiente."""
    if not uso:
        return
    t = _TAXI.setdefault(sesion, {"turnos": 0, "entrada": 0, "salida": 0, "cache_leida": 0, "cache_escrita": 0,
                                  "por_turno": []})
    e, sa = int(uso.get("inputTokens", 0)), int(uso.get("outputTokens", 0))
    cl, ce = int(uso.get("cacheReadInputTokens", 0)), int(uso.get("cacheWriteInputTokens", 0))
    t["turnos"] += 1
    t["entrada"] += e
    t["salida"] += sa
    t["cache_leida"] += cl
    t["cache_escrita"] += ce
    t["por_turno"].append({"entrada": e, "salida": sa, "cache_leida": cl, "cache_escrita": ce})


def medir(resultado, sesion: str = "local") -> None:
    """Para agentes ejecutados en el notebook: suma el uso de un AgentResult/MultiAgentResult."""
    uso = getattr(resultado, "accumulated_usage", None)
    if uso is None:
        uso = getattr(getattr(resultado, "metrics", None), "accumulated_usage", None)
    taximetro_sumar(sesion, dict(uso) if uso else None)
    _linea_taxi(sesion)


def _linea_taxi(sesion: str) -> None:
    t = _TAXI.get(sesion)
    if not t:
        return
    coste = _coste(t["entrada"], t["salida"], t["cache_leida"], t["cache_escrita"])
    extra = f" · ≈ {coste:.4f} USD" if coste is not None else ""
    cache = f" · caché: {t['cache_leida']:,} leídos" if t["cache_leida"] or t["cache_escrita"] else ""
    print(f"   🚕 conversación {sesion[:8]}: {t['turnos']} turnos · {t['entrada']:,} tokens de entrada · "
          f"{t['salida']:,} de salida{cache}{extra}")


def taximetro() -> None:
    """Resumen de todas las conversaciones de este notebook."""
    if not _TAXI:
        print("(taxímetro a cero)")
    for sesion, t in _TAXI.items():
        coste = _coste(t["entrada"], t["salida"], t["cache_leida"], t["cache_escrita"])
        media = t["entrada"] // max(t["turnos"], 1)
        print(f"{sesion[:12]:12} turnos={t['turnos']:3} entrada={t['entrada']:8,} caché_leída={t['cache_leida']:8,} "
              f"salida={t['salida']:7,} entrada/turno={media:7,}" + (f" coste≈{coste:.4f} USD" if coste is not None else ""))


def turnos(sesion: str) -> list[dict]:
    """Tokens de cada turno de una conversación (entrada, salida, caché leída y escrita)."""
    return list(_TAXI.get(sesion, {}).get("por_turno", []))


def comparar_conversaciones(sesion_a: str, sesion_b: str, etiquetas=("antes", "después")) -> None:
    """Tabla turno a turno de dos conversaciones: tokens de entrada (sin caché) y leídos de caché."""
    a, b = _TAXI.get(sesion_a, {}).get("por_turno", []), _TAXI.get(sesion_b, {}).get("por_turno", [])
    print(f"{'turno':>5} | {etiquetas[0] + ' entrada':>16} {'caché':>8} | {etiquetas[1] + ' entrada':>16} {'caché':>8}")
    for i in range(max(len(a), len(b))):
        fa = a[i] if i < len(a) else {}
        fb = b[i] if i < len(b) else {}
        print(f"{i + 1:>5} | {fa.get('entrada', 0):>16,} {fa.get('cache_leida', 0):>8,} | "
              f"{fb.get('entrada', 0):>16,} {fb.get('cache_leida', 0):>8,}")


def taximetro_cerrar(capitulo: int) -> None:
    """Guarda el resumen del capítulo en el histórico para comparar capítulos (ver capítulo 6)."""
    if not _TAXI:
        return
    turnos = sum(t["turnos"] for t in _TAXI.values())
    entrada = sum(t["entrada"] for t in _TAXI.values())
    salida = sum(t["salida"] for t in _TAXI.values())
    cache = sum(t.get("cache_leida", 0) for t in _TAXI.values())
    hist = state_get("TAXIMETRO_HISTORICO", {})
    hist[str(capitulo)] = {"turnos": turnos, "entrada": entrada, "salida": salida, "cache_leida": cache,
                           "entrada_por_turno": entrada // max(turnos, 1)}
    _guardar("TAXIMETRO_HISTORICO", hist)
    print(f"🚕 Capítulo {capitulo}: {turnos} turnos · {entrada // max(turnos, 1):,} tokens de entrada por turno")


def taximetro_historico() -> None:
    hist = state_get("TAXIMETRO_HISTORICO", {})
    if not hist:
        print("(sin histórico todavía)")
    for cap in sorted(hist, key=int):
        h = hist[cap]
        barra = "█" * max(1, h["entrada_por_turno"] // 500)
        print(f"Cap. {cap:>2}  {h['entrada_por_turno']:7,} tokens/turno  {barra}")


# --------------------------------------------------------------------------- cuaderno de deudas
DEUDAS = {
    "D0": "El agente responde con lo que sabe de fábrica, no con las políticas de TiendaNova",
    "D1": "Un cliente puede consultar pedidos de otro cliente",
    "D2": "Nada limita el importe de los reembolsos",
    "D3": "Los importes los calcula el modelo «de cabeza»",
    "D4": "El cliente_id llega en el payload: cualquiera puede suplantar a otro y leer su memoria",
    "D5": "La memoria puede guardar falsas «autorizaciones»",
    "D6": "El coste por conversación crece sin control",
    "D7": "No hay login de clientes: el agente no sabe quién le habla",
    "D8": "Los documentos del RAG pueden traer instrucciones maliciosas",
}
_ICONO = {"abierta": "🔴", "parcial": "🟡", "pagada": "🟢"}


def _guardar(clave: str, valor) -> None:
    state = state_load()
    state[clave] = valor
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def deuda(codigo: str, estado: str, capitulo: int, nota: str = "", descripcion: str | None = None) -> None:
    """Abre, actualiza o salda una deuda del cuaderno (estado: abierta | parcial | pagada).

    Para deudas nuevas (por ejemplo, en el capítulo 16) indica también `descripcion`.
    """
    cuaderno_ = state_get("CUADERNO_DEUDAS", {})
    entrada = cuaderno_.get(codigo, {"abierta_en": capitulo,
                                     "descripcion": descripcion or DEUDAS.get(codigo, codigo)})
    entrada.update(estado=estado, actualizada_en=capitulo, nota=nota)
    cuaderno_[codigo] = entrada
    _guardar("CUADERNO_DEUDAS", cuaderno_)


def cuaderno() -> None:
    """Muestra el cuaderno de deudas: lo que sabemos que está mal y aún no hemos resuelto."""
    cuaderno_ = state_get("CUADERNO_DEUDAS", {})
    print("📒 Cuaderno de deudas")
    if not cuaderno_:
        print("   (vacío)")
    for codigo in sorted(cuaderno_):
        e = cuaderno_[codigo]
        nota = f" — {e['nota']}" if e.get("nota") else ""
        print(f"   {_ICONO.get(e['estado'], '•')} {codigo} {e.get('descripcion') or DEUDAS.get(codigo, codigo)} "
              f"(cap. {e['abierta_en']} → {e['estado']} en cap. {e['actualizada_en']}){nota}")


_ULTIMA = {"respuesta": None, "herramientas": [], "datos": None}


def ultima_respuesta() -> str | None:
    """Texto de la última respuesta del agente (para comprobarla o evaluarla con un juez)."""
    return _ULTIMA["respuesta"]


def ultimas_herramientas() -> list[str]:
    """Herramientas que usó el agente en la última respuesta."""
    return list(_ULTIMA["herramientas"] or [])


def ultimo_dato(clave: str):
    """Un campo de la última respuesta del agente: «actor», «guardrail», «variante», «version_codigo»…"""
    datos = _ULTIMA["datos"]
    return datos.get(clave) if isinstance(datos, dict) else None


def ultima_microvm() -> dict | None:
    """Huella de la microVM que atendió la última invocación (capítulos 3 y 4)."""
    datos = _ULTIMA["datos"]
    return datos.get("microvm") if isinstance(datos, dict) else None


def _mostrar(prefijo: str, data, sesion: str | None = None) -> None:
    """Muestra la respuesta del agente, las herramientas usadas y el taxímetro de la conversación."""
    _ULTIMA["datos"] = data
    _ULTIMA["respuesta"] = data.get("respuesta") if isinstance(data, dict) else data
    _ULTIMA["herramientas"] = data.get("herramientas", []) if isinstance(data, dict) else []
    if isinstance(data, dict):
        print(f"{prefijo} {data.get('respuesta', data)}")
        if data.get("herramientas"):
            print("   🔧 herramientas:", ", ".join(data["herramientas"]))
        if data.get("actor"):
            print("   🪪 el agente atiende a:", data["actor"])
        if data.get("microvm"):
            m = data["microvm"]
            print(f"   🖥️ microVM {m.get('id')} · invocación nº {m.get('invocacion')} en esta microVM")
        if data.get("guardrail"):
            print("   🛡️ el guardrail ha intervenido")
        if data.get("variante"):
            print("   🧪 variante del A/B:", data["variante"])
        if data.get("version_codigo"):
            print("   🏷️ versión del código:", data["version_codigo"])
        if sesion:
            taximetro_sumar(sesion, data.get("tokens"))
            _linea_taxi(sesion)
    else:
        print(f"{prefijo} {data}")
    print()


def new_session_id() -> str:
    """ID de sesión de 36 caracteres (UUID4), válido como runtimeSessionId."""
    return str(uuid.uuid4())


def invocar(prompt: str, session_id: str | None = None, cliente_id: str = "C-001",
            token: str | None = None, canal: str = "web", idioma: str = "es",
            qualifier: str = "DEFAULT", url: str | None = None) -> str:
    """Invoca el agente desplegado y devuelve el session_id para encadenar turnos.

    - Sin token ni url: SigV4 con boto3 (capítulos 3–8).
    - Con token: HTTPS con Bearer, obligatorio cuando el Runtime usa autorizador JWT (capítulo 9 en adelante).
    - Con url y sin token: petición firmada con SigV4 a esa URL (Gateway HTTP del capítulo 13).
    - `qualifier`: endpoint del Runtime (DEFAULT, pre, prod…), capítulo 15.
    """
    session_id = session_id or new_session_id()
    payload = {"prompt": prompt, "cliente_id": cliente_id, "canal": canal, "idioma": idioma}
    cuerpo = json.dumps(payload).encode()
    if token is None and url is None:
        import boto3
        arn = state_get("AGENT_ARN")
        if not arn:
            raise RuntimeError("Falta AGENT_ARN (capítulo 3).")
        client = boto3.client("bedrock-agentcore", region_name=region())
        resp = client.invoke_agent_runtime(agentRuntimeArn=arn, runtimeSessionId=session_id,
                                           payload=cuerpo, qualifier=qualifier)
        # Los trozos del stream pueden partir un carácter multibyte (ñ, á…): se acumulan los bytes
        # y se decodifica UNA sola vez.
        body = b"".join(resp.get("response", [])).decode("utf-8")
    else:
        if url is None:
            arn = state_get("AGENT_ARN")
            url = (f"https://bedrock-agentcore.{region()}.amazonaws.com/runtimes/"
                   f"{urllib.parse.quote(arn, safe='')}/invocations?qualifier={qualifier}")
        cabeceras = {"Content-Type": "application/json",
                     "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": session_id}
        if token is not None:
            cabeceras["Authorization"] = f"Bearer {token}"
        else:
            cabeceras = _firmar_sigv4(url, cuerpo, cabeceras)
        req = urllib.request.Request(url, data=cuerpo, method="POST", headers=cabeceras)
        try:
            with urllib.request.urlopen(req) as r:
                body = r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            detalle = e.read().decode("utf-8", errors="replace")[:300]
            raise RuntimeError(f"HTTP {e.code} al invocar: {detalle}") from None
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        data = body
    _mostrar(f"[{session_id[:8]}]", data, session_id)
    return session_id


def _firmar_sigv4(url: str, cuerpo: bytes, cabeceras: dict, servicio: str = "bedrock-agentcore") -> dict:
    """Firma una petición HTTP con las credenciales de AWS del notebook (SigV4)."""
    import boto3
    from botocore.auth import SigV4Auth
    from botocore.awsrequest import AWSRequest
    credenciales = boto3.Session().get_credentials().get_frozen_credentials()
    peticion = AWSRequest(method="POST", url=url, data=cuerpo, headers=cabeceras)
    SigV4Auth(credenciales, servicio, region()).add_auth(peticion)
    return dict(peticion.headers.items())


def parar_sesion(session_id: str, qualifier: str = "DEFAULT") -> None:
    """Termina la microVM de una sesión del Runtime, como haría la inactividad (15 min) o un redespliegue."""
    import boto3
    boto3.client("bedrock-agentcore", region_name=region()).stop_runtime_session(
        agentRuntimeArn=state_get("AGENT_ARN"), runtimeSessionId=session_id, qualifier=qualifier)
    print(f"⏹️ microVM de la sesión {session_id[:8]} terminada")


def version_runtime() -> int:
    """Versión más reciente del Runtime (cada despliegue crea una versión inmutable)."""
    return int(_control().get_agent_runtime(agentRuntimeId=runtime_id())["agentRuntimeVersion"])


_MODULOS_AGENTE = ["settings", "prompts", "datos_pedidos", "herramientas", "memoria", "contexto", "modelo", "identidad",
                   "gateway", "presupuesto", "main"]   # «respuesta» no se recarga: su huella es la del proceso


def probar_local(prompt: str, session_id: str | None = None, cliente_id: str = "C-001",
                 headers: dict | None = None, canal: str = "web", idioma: str = "es") -> str:
    """Ejecuta el entrypoint de main.py en el kernel del notebook, recargando los módulos del agente.

    Es una prueba rápida sin desplegar; para el ciclo completo con Agent Inspector usa `agentcore dev`
    en una terminal de tu equipo (en Colab no hay navegador local para el Inspector).
    """
    if str(AGENT_DIR) not in sys.path:
        sys.path.insert(0, str(AGENT_DIR))
    for name in _MODULOS_AGENTE:
        if (AGENT_DIR / f"{name}.py").exists():
            if name in sys.modules:
                importlib.reload(sys.modules[name])
            else:
                importlib.import_module(name)
    session_id = session_id or new_session_id()
    ctx = SimpleNamespace(session_id=session_id, request_headers=headers or {})
    out = sys.modules["main"].invoke(
        {"prompt": prompt, "cliente_id": cliente_id, "canal": canal, "idioma": idioma}, ctx)
    _mostrar(f"[local {session_id[:8]}]", out, session_id)
    return session_id


# --------------------------------------------------------------------------- Gateway (MCP) y tokens
def mcp_tools_list(token: str | None = None) -> list[dict]:
    """Llama a tools/list en el Gateway y muestra los nombres (formato Target___herramienta)."""
    url = state_get("GATEWAY_URL")
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}).encode()
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req) as r:
        raw = r.read().decode("utf-8")
    if raw.lstrip().startswith(("event:", "data:")):
        raw = "\n".join(line[5:].strip() for line in raw.splitlines() if line.startswith("data:"))
    tools = json.loads(raw)["result"]["tools"]
    for t in tools:
        print("•", t["name"])
    return tools


def mcp_call(herramienta: str, argumentos: dict, token: str | None = None) -> dict:
    """Llama a una herramienta del Gateway SIN pasar por el modelo (tools/call).

    Sirve para comprobar de forma determinista qué decide el Gateway (Policy, límites) con independencia
    de lo que haría el modelo. Devuelve {"ok": bool, "http": código, "texto": respuesta resumida}.
    """
    url = state_get("GATEWAY_URL")
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": herramienta, "arguments": argumentos}}).encode()
    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
               "Authorization": f"Bearer {token or token_m2m()}"}
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            raw, codigo = r.read().decode("utf-8"), r.status
    except urllib.error.HTTPError as e:
        return {"ok": False, "http": e.code, "texto": e.read().decode("utf-8", errors="replace")[:300]}
    if raw.lstrip().startswith(("event:", "data:")):
        raw = "\n".join(line[5:].strip() for line in raw.splitlines() if line.startswith("data:"))
    msg = json.loads(raw)
    if "error" in msg:
        return {"ok": False, "http": codigo, "texto": json.dumps(msg["error"], ensure_ascii=False)[:300]}
    res = msg.get("result", {})
    texto = " ".join(c.get("text", "") for c in res.get("content", []) if isinstance(c, dict))
    return {"ok": not res.get("isError", False), "http": codigo, "texto": texto[:300]}


def token_m2m() -> str:
    """Token client_credentials del pool de servicios (Lab 07). Solo para pruebas desde el notebook:
    en el Runtime, el agente obtiene el token a través de AgentCore Identity."""
    s = state_load()
    url = f"https://{s['M2M_DOMAIN']}.auth.{region()}.amazoncognito.com/oauth2/token"
    data = urllib.parse.urlencode({"grant_type": "client_credentials",
                                   "scope": " ".join(s.get("GATEWAY_SCOPES", ["gateway/invoke"]))}).encode()
    basic = base64.b64encode(f"{s['M2M_CLIENT_ID']}:{s['M2M_CLIENT_SECRET']}".encode()).decode()
    req = urllib.request.Request(url, data=data, method="POST", headers={
        "Content-Type": "application/x-www-form-urlencoded", "Authorization": f"Basic {basic}"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())["access_token"]


def token_cliente(username: str, password: str | None = None) -> str:
    """Access token de un cliente final del pool de clientes (Lab 09)."""
    import boto3
    idp = boto3.client("cognito-idp", region_name=region())
    r = idp.initiate_auth(ClientId=state_get("CLIENTES_CLIENT_ID"), AuthFlow="USER_PASSWORD_AUTH",
                          AuthParameters={"USERNAME": username,
                                          "PASSWORD": password or state_get("CLIENTES_PASSWORD")})
    return r["AuthenticationResult"]["AccessToken"]


# --------------------------------------------------------------------------- evaluación por lotes (capítulo 15)
def evaluacion_por_lotes(session_ids: list[str], evaluadores=("Builtin.GoalSuccessRate", "Builtin.Helpfulness"),
                         endpoint: str = "DEFAULT", runtime: str = "NovaAgent", espera_max: int = 1200) -> dict:
    """Lanza una batch evaluation con la CLI sobre unas sesiones y devuelve {evaluador: puntuación media}.

    Las trazas tardan entre 5 y 10 minutos en estar disponibles: si la CLI dice que no encuentra spans, espera y repite.
    """
    import re
    import time
    import boto3
    salida = cli_args("run", "batch-evaluation", "-r", runtime, "-e", *evaluadores, "--endpoint", endpoint,
                      "-s", *session_ids, "--wait", "--json", capturar=True) or ""
    m = re.search(r'"batchEvaluationId"\s*:\s*"([^"]+)"', salida)
    if not m:
        raise RuntimeError("No encuentro el id de la evaluación en la salida de la CLI:\n" + salida[:500])
    dp = boto3.client("bedrock-agentcore", region_name=region())
    inicio = time.time()
    while True:
        ev = dp.get_batch_evaluation(batchEvaluationId=m.group(1))
        if ev["status"] in ("COMPLETED", "COMPLETED_WITH_ERRORS", "FAILED", "STOPPED") or time.time() - inicio > espera_max:
            break
        print("…", ev["status"])
        time.sleep(30)
    res = ev.get("evaluationResults", {})
    print(f"Evaluación {m.group(1)}: {ev['status']} · sesiones evaluadas {res.get('numberOfSessionsCompleted', 0)}"
          f"/{res.get('totalNumberOfSessions', 0)}")
    notas = {e.get("evaluatorId"): (e.get("statistics") or {}).get("averageScore")
             for e in res.get("evaluatorSummaries", [])}
    for k, v in notas.items():
        print(f"   {k:28} {v if v is None else round(v, 3)}")
    return notas


# --------------------------------------------------------------------------- datos: S3 Tables (Iceberg) y Athena
DATOS_DIR = LAB_ROOT / "datos"
ICEBERG_NAMESPACE = "tiendanova"


def catalogo_iceberg():
    """Catálogo PyIceberg contra el endpoint Iceberg REST de S3 Tables (firma SigV4, servicio 's3tables')."""
    from pyiceberg.catalog import load_catalog
    r = region()
    return load_catalog("s3tables", **{
        "type": "rest",
        "warehouse": state_get("TABLE_BUCKET_ARN"),
        "uri": f"https://s3tables.{r}.amazonaws.com/iceberg",
        "rest.sigv4-enabled": "true",
        "rest.signing-name": "s3tables",
        "rest.signing-region": r,
    })


def escribir_tabla(nombre: str, filas: list[dict], modo: str = "overwrite"):
    """Crea la tabla Iceberg si no existe y escribe las filas (overwrite o append)."""
    import pyarrow as pa
    cat = catalogo_iceberg()
    ident = f"{ICEBERG_NAMESPACE}.{nombre}"
    if cat.table_exists(ident):
        tbl = cat.load_table(ident)
        datos = pa.Table.from_pylist(filas, schema=tbl.schema().as_arrow())
        tbl.overwrite(datos) if modo == "overwrite" else tbl.append(datos)
    else:
        datos = pa.Table.from_pylist(filas)
        tbl = cat.create_table(ident, schema=datos.schema)
        tbl.append(datos)
    print(f"✔ {ident}: {len(filas)} filas ({modo})")
    return tbl


def leer_tabla(nombre: str, filtro=None, snapshot_id: int | None = None) -> list[dict]:
    """Lee una tabla Iceberg (opcionalmente con filtro PyIceberg o en un snapshot anterior: time travel)."""
    tbl = catalogo_iceberg().load_table(f"{ICEBERG_NAMESPACE}.{nombre}")
    kwargs = {"snapshot_id": snapshot_id} if snapshot_id else {}
    if filtro is not None:
        kwargs["row_filter"] = filtro
    return tbl.scan(**kwargs).to_arrow().to_pylist()


def athena(sql: str, params: list[str] | None = None) -> list[dict]:
    """Consulta SQL sobre S3 Tables vía Athena (catálogo federado s3tablescatalog)."""
    import time
    import boto3
    cli = boto3.client("athena", region_name=region())
    kwargs = {
        "QueryString": sql,
        "QueryExecutionContext": {"Catalog": state_get("ATHENA_CATALOG"), "Database": ICEBERG_NAMESPACE},
        "ResultConfiguration": {"OutputLocation": state_get("ATHENA_OUTPUT")},
    }
    if params:
        kwargs["ExecutionParameters"] = params
    qid = cli.start_query_execution(**kwargs)["QueryExecutionId"]
    while True:
        st = cli.get_query_execution(QueryExecutionId=qid)["QueryExecution"]["Status"]
        if st["State"] in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
        time.sleep(0.3)
    if st["State"] != "SUCCEEDED":
        raise RuntimeError(f"Athena {st['State']}: {st.get('StateChangeReason')}")
    filas = cli.get_query_results(QueryExecutionId=qid)["ResultSet"]["Rows"]
    cols = [c.get("VarCharValue") for c in filas[0]["Data"]]
    return [dict(zip(cols, [c.get("VarCharValue") for c in f["Data"]])) for f in filas[1:]]



# --------------------------------------------------------------------------- limpieza (capítulo 17)
def intentar(descripcion: str, fn) -> bool:
    """Ejecuta una operación de borrado y continúa aunque falle (recurso ya borrado, sin permisos…)."""
    try:
        fn()
        print("✔", descripcion)
        return True
    except Exception as e:  # noqa: BLE001
        nombre = type(e).__name__
        if any(k in nombre for k in ("NotFound", "NoSuch", "ResourceNotFound")):
            print("= ", descripcion, "(ya no existe)")
        else:
            print("·", descripcion, "→", nombre, str(e)[:160])
        return False


def borrar_rol_iam(nombre: str) -> None:
    """Borra un rol de IAM con todo lo que tenga dentro (políticas gestionadas, en línea y perfiles de instancia)."""
    import boto3
    iam = boto3.client("iam")
    for pol in iam.list_attached_role_policies(RoleName=nombre)["AttachedPolicies"]:
        iam.detach_role_policy(RoleName=nombre, PolicyArn=pol["PolicyArn"])
    for pol in iam.list_role_policies(RoleName=nombre)["PolicyNames"]:
        iam.delete_role_policy(RoleName=nombre, PolicyName=pol)
    for perfil in iam.list_instance_profiles_for_role(RoleName=nombre)["InstanceProfiles"]:
        iam.remove_role_from_instance_profile(InstanceProfileName=perfil["InstanceProfileName"], RoleName=nombre)
    iam.delete_role(RoleName=nombre)


def vaciar_y_borrar_bucket(nombre: str) -> None:
    """Vacía un bucket S3 (incluidas versiones) y lo borra."""
    import boto3
    b = boto3.resource("s3", region_name=region()).Bucket(nombre)
    b.object_versions.all().delete()
    b.objects.all().delete()
    b.delete()


def grupos_de_logs_laboratorio() -> list[str]:
    """Grupos de logs de CloudWatch del laboratorio (Runtime, Lambdas, Memory, Gateway…): contienen «nova» en el nombre."""
    import boto3
    logs = boto3.client("logs", region_name=region())
    nombres = []
    for pagina in logs.get_paginator("describe_log_groups").paginate():
        nombres += [g["logGroupName"] for g in pagina["logGroups"] if "nova" in g["logGroupName"].lower()]
    return nombres


def inventario_laboratorio(mostrar: bool = True) -> dict[str, list[str]]:
    """Lo que queda en la cuenta con nombre del laboratorio (Nova). Tras la limpieza debería estar vacío."""
    import boto3
    r = region()
    inv: dict[str, list[str]] = {}

    def anotar(servicio, fn):
        try:
            nombres = [n for n in fn() if n and "nova" in n.lower()]
        except Exception as e:  # noqa: BLE001
            nombres = [f"(no se pudo listar: {type(e).__name__})"]
        if nombres:
            inv[servicio] = nombres

    ctl = boto3.client("bedrock-agentcore-control", region_name=r)
    anotar("AgentCore Runtime", lambda: [x["agentRuntimeName"] for x in ctl.list_agent_runtimes().get("agentRuntimes", [])])
    anotar("AgentCore Memory", lambda: [x.get("id") or x.get("memoryId") for x in ctl.list_memories().get("memories", [])])
    anotar("AgentCore Gateway", lambda: [x["name"] for x in ctl.list_gateways().get("items", [])])
    anotar("AgentCore Policy", lambda: [x.get("name", "") for x in ctl.list_policy_engines().get("policyEngines", [])])
    anotar("AgentCore Identity (OAuth)", lambda: [x["name"] for x in
                                                 ctl.list_oauth2_credential_providers().get("credentialProviders", [])])
    anotar("Evaluaciones online", lambda: [x["onlineEvaluationConfigName"] for x in
                                           ctl.list_online_evaluation_configs().get("onlineEvaluationConfigs", [])])
    anotar("Configuration bundles", lambda: [x["bundleName"] for x in ctl.list_configuration_bundles().get("bundles", [])])
    anotar("Lambda", lambda: [f["FunctionName"] for f in boto3.client("lambda", region_name=r).list_functions()["Functions"]])
    anotar("IAM (roles)", lambda: [x["RoleName"] for x in boto3.client("iam").list_roles(MaxItems=1000)["Roles"]])
    anotar("Cognito", lambda: [x["Name"] for x in boto3.client("cognito-idp", region_name=r).list_user_pools(
        MaxResults=60)["UserPools"]])
    anotar("Bedrock Guardrails", lambda: [x["name"] for x in boto3.client("bedrock", region_name=r).list_guardrails()["guardrails"]])
    anotar("S3", lambda: [b["Name"] for b in boto3.client("s3").list_buckets()["Buckets"]])
    anotar("S3 Tables", lambda: [b["name"] for b in boto3.client("s3tables", region_name=r).list_table_buckets()["tableBuckets"]])
    anotar("S3 Vectors", lambda: [b["vectorBucketName"] for b in
                                  boto3.client("s3vectors", region_name=r).list_vector_buckets().get("vectorBuckets", [])])
    anotar("CloudFormation", lambda: [x["StackName"] for x in boto3.client("cloudformation", region_name=r).list_stacks(
        StackStatusFilter=["CREATE_COMPLETE", "UPDATE_COMPLETE", "UPDATE_ROLLBACK_COMPLETE", "ROLLBACK_COMPLETE",
                           "DELETE_FAILED", "CREATE_FAILED"])["StackSummaries"]])
    anotar("CloudWatch Logs", lambda: grupos_de_logs_laboratorio())
    if mostrar:
        if not inv:
            print("✔ No queda nada del laboratorio en la cuenta")
        for servicio, nombres in inv.items():
            print(f"• {servicio}: {', '.join(nombres[:8])}{' …' if len(nombres) > 8 else ''}")
    return inv


def archivar_estado() -> None:
    """Archiva lab_state.json como .bak (si existe) al terminar el curso. Idempotente."""
    if STATE_FILE.exists():
        destino = STATE_FILE.with_suffix(".json.bak")
        if destino.exists():
            destino.unlink()
        STATE_FILE.rename(destino)
        if os.environ.get("NOVA_DRIVE_DIR"):
            import colab_nova
            colab_nova.borrar_de_drive(STATE_FILE)
            _a_drive(destino)
        print("lab_state.json archivado como lab_state.json.bak")
    else:
        print("(no hay lab_state.json que archivar)")


# --------------------------------------------------------------------------- puntos de guardado
PARTIDAS = LAB_ROOT / "partidas"          # ¡no versionar! contienen lab_state.json
_EN_PARTIDA = ["NovaAssist/app", "NovaAssist/agentcore/agentcore.json", "NovaAssist/agentcore/aws-targets.json",
               "NovaAssist/agentcore/.env.local",   # secretos que la CLI guarda para los credential providers
               "NovaAssist/tools.json", "NovaAssist/politicas_tools.json", "NovaAssist/politicas", "lambda"]

# clave de lab_state.json -> capítulo que la crea
PRODUCE = {
    "REGION": 0, "MODEL_ID": 0, "TABLE_BUCKET_ARN": 0, "LAB_BUCKET": 0, "ATHENA_CATALOG": 0,
    "AGENT_ARN": 3, "MEMORY_ID": 4, "LTM_NAMESPACES": 5,
    "LAMBDA_ARN": 7, "M2M_CLIENT_ID": 7, "GATEWAY_URL": 7, "GATEWAY_ARN": 7, "GATEWAY_CREDENTIAL_PROVIDER": 7,
    "VECTOR_BUCKET": 8, "VECTOR_INDEX": 8, "LAMBDA_POLITICAS_ARN": 8,
    "CLIENTES_POOL_ID": 9, "CLIENTES_CLIENT_ID": 9,
    "GUARDRAIL_ID": 10, "EVAL_SESSIONS": 12,
}
# El capítulo 17 (limpieza) no produce estado: lo archiva.


def guardar_partida(capitulo: int) -> None:
    """Guarda el estado local al final de un capítulo (estado, código del agente y configuración de la CLI)."""
    import shutil
    destino = PARTIDAS / f"cap{capitulo:02d}"
    if destino.exists():
        shutil.rmtree(destino)
    destino.mkdir(parents=True)
    if STATE_FILE.exists():
        shutil.copy2(STATE_FILE, destino / "lab_state.json")
    ignorar = shutil.ignore_patterns(".venv", "__pycache__", "node_modules", "*.pyc")
    for rel in _EN_PARTIDA:
        origen = LAB_ROOT / rel
        if origen.is_dir():
            shutil.copytree(origen, destino / rel, ignore=ignorar)
        elif origen.exists():
            (destino / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(origen, destino / rel)
    _a_drive()
    print(f"💾 Partida guardada: final del capítulo {capitulo}"
          + (" (y copiada a Google Drive)" if os.environ.get("NOVA_DRIVE_DIR") else ""))


def cargar_partida(capitulo: int) -> None:
    """Restaura la partida del final de un capítulo. Después, `agentcore deploy` sincroniza la nube."""
    import shutil
    origen = PARTIDAS / f"cap{capitulo:02d}"
    if not origen.exists():
        raise FileNotFoundError(f"No hay partida del capítulo {capitulo} en {PARTIDAS}")
    for rel in _EN_PARTIDA:
        src, dst = origen / rel, LAB_ROOT / rel
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        elif src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    if (origen / "lab_state.json").exists():
        shutil.copy2(origen / "lab_state.json", STATE_FILE)
    print(f"🎮 Partida cargada: final del capítulo {capitulo}. Ejecuta `agentcore deploy` si el capítulo usa el Runtime.")


def empaquetar_pedidos() -> None:
    """Escribe app/NovaAgent/datos_pedidos.py desde datos/tiendanova.json (capítulo 3)."""
    ds = json.loads((DATOS_DIR / "tiendanova.json").read_text(encoding="utf-8"))
    pedidos = {p["pedido_id"]: p for p in ds["pedidos"]}
    AGENT_DIR.mkdir(parents=True, exist_ok=True)
    (AGENT_DIR / "datos_pedidos.py").write_text(
        '"""Generado desde datos/tiendanova.json (capítulo 0, Parte C)."""\nimport json\n\n'
        f"PEDIDOS = json.loads({json.dumps(json.dumps(pedidos, ensure_ascii=False), ensure_ascii=False)})\n",
        encoding="utf-8")
    print(len(pedidos), "pedidos empaquetados con el agente")


def codigo_referencia(hasta: int) -> None:
    """Escribe el código canónico del agente al final del capítulo `hasta`, extraído de los propios notebooks."""
    import nbformat
    if not (PROJECT / "agentcore").exists():
        raise RuntimeError("Falta el proyecto de la CLI: ejecuta la sección «El proyecto» del capítulo 3.")
    write_settings()
    if hasta >= 3:
        empaquetar_pedidos()
        fijar_dependencia(VERSIONES["strands-agents"])
        fijar_dependencia(VERSIONES["bedrock-agentcore"])
    if hasta >= 7:
        fijar_dependencia(VERSIONES["mcp"])
    if hasta >= 11:
        fijar_dependencia(VERSIONES["strands-agents-tools"])
    escritos = 0
    for nb in sorted(LAB_ROOT.glob("[0-9][0-9]_*.ipynb")):
        if int(nb.name[:2]) > hasta:
            break
        for c in nbformat.read(nb, as_version=4).cells:
            if c.cell_type == "code" and c.source.startswith("%%writefile "):
                primera, cuerpo = c.source.split("\n", 1)
                ruta = LAB_ROOT / primera.split(maxsplit=1)[1].strip()
                ruta.parent.mkdir(parents=True, exist_ok=True)
                ruta.write_text(cuerpo if cuerpo.endswith("\n") else cuerpo + "\n", encoding="utf-8")
                escritos += 1
    if hasta >= 7:
        for modulo in ("herramientas", "datos_pedidos"):
            (AGENT_DIR / f"{modulo}.py").unlink(missing_ok=True)
    print(f"✔ Código de referencia del final del capítulo {hasta} ({escritos} ficheros)")


def requisitos(capitulo: int) -> list[str]:
    """Comprueba lo que debe existir al empezar un capítulo y dice qué capítulo lo crea."""
    faltan = []
    if capitulo >= 2 and not (DATOS_DIR / "tiendanova.json").exists():
        faltan.append("datos/tiendanova.json (capítulo 0, Parte C)")
    if capitulo >= 4 and not (PROJECT / "agentcore").exists():
        faltan.append("proyecto NovaAssist (capítulo 3)")
    for clave, cap in sorted(PRODUCE.items(), key=lambda kv: kv[1]):
        if cap < capitulo and not state_get(clave):
            faltan.append(f"{clave} (capítulo {cap})")
    if faltan:
        print(f"⚠ Para empezar el capítulo {capitulo} falta:")
        for f in faltan:
            print("   ✗", f)
    else:
        print(f"✔ Tienes todo lo necesario para el capítulo {capitulo}")
    return faltan


def ponerse_al_dia(capitulo: int) -> None:
    """Recupera el punto de partida de un capítulo.

    Si hay partida del capítulo anterior, la carga. Si no, escribe el código de referencia y lista qué recursos
    de la nube faltan (y en qué capítulo se crean). Las partidas no son portables entre cuentas de AWS.
    """
    previo = capitulo - 1
    if (PARTIDAS / f"cap{previo:02d}").exists():
        cargar_partida(previo)
    elif capitulo >= 4:
        codigo_referencia(previo)
    faltan = requisitos(capitulo)
    if faltan:
        print("→ Ejecuta en esos capítulos solo las celdas que crean cada recurso (la guía del formador las indica).")
    if capitulo >= 4:
        print('→ Después, despliega: cli("agentcore deploy --yes")  (o en una terminal: cd labs/NovaAssist && agentcore deploy)')
