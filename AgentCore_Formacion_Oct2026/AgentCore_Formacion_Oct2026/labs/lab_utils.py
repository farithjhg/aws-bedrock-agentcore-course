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


# --------------------------------------------------------------------------- estado compartido
def state_load() -> dict:
    return json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else {}


def state_get(key: str, default=None):
    return state_load().get(key, default)


def state_set(**values) -> None:
    state = state_load()
    state.update(values)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
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


# --------------------------------------------------------------------------- invocación

# --------------------------------------------------------------------------- taxímetro (tokens y coste)
_TAXI: dict[str, dict] = {}


def precios(entrada_por_millon: float, salida_por_millon: float) -> None:
    """Precio del modelo por millón de tokens (consúltalo en la página de precios de Bedrock)."""
    state_set(PRECIO_ENTRADA_MTOK=entrada_por_millon, PRECIO_SALIDA_MTOK=salida_por_millon)


def _coste(entrada: int, salida: int) -> float | None:
    pe, ps = state_get("PRECIO_ENTRADA_MTOK"), state_get("PRECIO_SALIDA_MTOK")
    if pe is None or ps is None:
        return None
    return entrada / 1e6 * pe + salida / 1e6 * ps


def taximetro_sumar(sesion: str, uso: dict | None) -> None:
    """Acumula el uso de tokens de una invocación en la sesión (conversación) correspondiente."""
    if not uso:
        return
    t = _TAXI.setdefault(sesion, {"turnos": 0, "entrada": 0, "salida": 0})
    t["turnos"] += 1
    t["entrada"] += int(uso.get("inputTokens", 0))
    t["salida"] += int(uso.get("outputTokens", 0))


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
    coste = _coste(t["entrada"], t["salida"])
    extra = f" · ≈ {coste:.4f} USD" if coste is not None else ""
    print(f"   🚕 conversación {sesion[:8]}: {t['turnos']} turnos · {t['entrada']:,} tokens de entrada · "
          f"{t['salida']:,} de salida{extra}")


def taximetro() -> None:
    """Resumen de todas las conversaciones de este notebook."""
    if not _TAXI:
        print("(taxímetro a cero)")
    for sesion, t in _TAXI.items():
        coste = _coste(t["entrada"], t["salida"])
        media = t["entrada"] // max(t["turnos"], 1)
        print(f"{sesion[:12]:12} turnos={t['turnos']:3} entrada={t['entrada']:8,} salida={t['salida']:7,} "
              f"entrada/turno={media:7,}" + (f" coste≈{coste:.4f} USD" if coste is not None else ""))


def taximetro_cerrar(capitulo: int) -> None:
    """Guarda el resumen del capítulo en el histórico para comparar capítulos (ver capítulo 6)."""
    if not _TAXI:
        return
    turnos = sum(t["turnos"] for t in _TAXI.values())
    entrada = sum(t["entrada"] for t in _TAXI.values())
    salida = sum(t["salida"] for t in _TAXI.values())
    hist = state_get("TAXIMETRO_HISTORICO", {})
    hist[str(capitulo)] = {"turnos": turnos, "entrada": entrada, "salida": salida,
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


_ULTIMA = {"respuesta": None}


def ultima_respuesta() -> str | None:
    """Texto de la última respuesta del agente (para evaluarla con un juez, capítulo 12)."""
    return _ULTIMA["respuesta"]


def _mostrar(prefijo: str, data, sesion: str | None = None) -> None:
    """Muestra la respuesta del agente, las herramientas usadas y el taxímetro de la conversación."""
    _ULTIMA["respuesta"] = data.get("respuesta") if isinstance(data, dict) else data
    if isinstance(data, dict):
        print(f"{prefijo} {data.get('respuesta', data)}")
        if data.get("herramientas"):
            print("   🔧 herramientas:", ", ".join(data["herramientas"]))
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
            token: str | None = None, canal: str = "web", idioma: str = "es") -> str:
    """Invoca el agente desplegado.

    - Sin token: SigV4 con boto3 (Labs 02–08).
    - Con token: HTTPS con Bearer, obligatorio cuando el Runtime usa autorizador JWT (Lab 09+).
    Devuelve el session_id para encadenar turnos.
    """
    session_id = session_id or new_session_id()
    arn = state_get("AGENT_ARN")
    if not arn:
        raise RuntimeError("Falta AGENT_ARN (Lab 02).")
    payload = {"prompt": prompt, "cliente_id": cliente_id, "canal": canal, "idioma": idioma}
    if token is None:
        import boto3
        client = boto3.client("bedrock-agentcore", region_name=region())
        resp = client.invoke_agent_runtime(agentRuntimeArn=arn, runtimeSessionId=session_id,
                                           payload=json.dumps(payload).encode(), qualifier="DEFAULT")
        body = "".join(chunk.decode("utf-8") for chunk in resp.get("response", []))
    else:
        url = (f"https://bedrock-agentcore.{region()}.amazonaws.com/runtimes/"
               f"{urllib.parse.quote(arn, safe='')}/invocations?qualifier=DEFAULT")
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST", headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Amzn-Bedrock-AgentCore-Runtime-Session-Id": session_id,
        })
        with urllib.request.urlopen(req) as r:
            body = r.read().decode("utf-8")
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        data = body
    _mostrar(f"[{session_id[:8]}]", data, session_id)
    return session_id


_MODULOS_AGENTE = ["settings", "prompts", "datos_pedidos", "herramientas", "memoria", "contexto", "identidad", "gateway", "main"]


def probar_local(prompt: str, session_id: str | None = None, cliente_id: str = "C-001",
                 headers: dict | None = None, canal: str = "web", idioma: str = "es") -> str:
    """Ejecuta el entrypoint de main.py en el kernel del notebook, recargando los módulos del agente.

    Es una prueba rápida sin desplegar; para el ciclo completo con Agent Inspector usa `agentcore dev`
    en una terminal.
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



# --------------------------------------------------------------------------- puntos de guardado
PARTIDAS = LAB_ROOT / "partidas"          # ¡no versionar! contienen lab_state.json
_EN_PARTIDA = ["NovaAssist/app", "NovaAssist/agentcore/agentcore.json", "NovaAssist/agentcore/aws-targets.json",
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
    print(f"💾 Partida guardada: final del capítulo {capitulo}")


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
        print("→ Después, en una terminal: cd labs/NovaAssist && agentcore deploy")
