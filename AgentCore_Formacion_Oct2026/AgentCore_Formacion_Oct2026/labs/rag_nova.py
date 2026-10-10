"""Pipeline RAG de Nova Assist: troceado → Iceberg (linaje) → embeddings (Titan V2) → S3 Vectors (índice).

Las mismas funciones se usan en el Lab 08 (ingesta y consultas directas) y en el Lab 12 (recall@k).
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone

from lab_utils import region, state_get

MODELO_EMBEDDING = "amazon.titan-embed-text-v2:0"
DIMENSION = 1024
MAX_CHARS = 900


def trocear(doc: dict) -> list[dict]:
    """Trocea un documento Markdown por secciones '## '. Cada fragmento conserva su linaje."""
    secciones = re.split(r"\n(?=## )", doc["contenido_md"])
    titulo_doc = secciones[0].lstrip("# ").splitlines()[0]
    chunks = []
    for n, sec in enumerate(s for s in secciones[1:] if s.strip()):
        cabecera, _, cuerpo = sec.partition("\n")
        texto = f"{titulo_doc} — {cabecera.lstrip('# ').strip()}\n{cuerpo.strip()}"[:MAX_CHARS]
        chunks.append({
            "chunk_id": f"{doc['doc_id']}#{doc['version']}#{n:02d}",
            "doc_id": doc["doc_id"], "version": doc["version"], "tipo": doc["tipo"], "idioma": doc["idioma"],
            "seccion": cabecera.lstrip("# ").strip(), "texto": texto,
            "hash_sha256": hashlib.sha256(texto.encode()).hexdigest(),
            "modelo_embedding": MODELO_EMBEDDING, "vigente": bool(doc.get("vigente", True)),
            "fecha_ingesta": datetime.now(timezone.utc).replace(tzinfo=None),
        })
    return chunks


def embedding(texto: str) -> list[float]:
    import boto3
    rt = boto3.client("bedrock-runtime", region_name=region())
    r = rt.invoke_model(modelId=MODELO_EMBEDDING,
                        body=json.dumps({"inputText": texto, "dimensions": DIMENSION, "normalize": True}))
    return json.loads(r["body"].read())["embedding"]


def _s3v():
    import boto3
    return boto3.client("s3vectors", region_name=region())


def indexar(chunks: list[dict]) -> None:
    """Calcula embeddings y los escribe en S3 Vectors (lotes de hasta 500 vectores por llamada)."""
    vectores = [{
        "key": c["chunk_id"],
        "data": {"float32": embedding(c["texto"])},
        "metadata": {  # filtrables: doc_id, version, tipo, idioma, vigente · no filtrables: texto, seccion
            "doc_id": c["doc_id"], "version": c["version"], "tipo": c["tipo"], "idioma": c["idioma"],
            "vigente": c["vigente"], "texto": c["texto"], "seccion": c["seccion"],
        },
    } for c in chunks]
    for i in range(0, len(vectores), 500):
        _s3v().put_vectors(vectorBucketName=state_get("VECTOR_BUCKET"), indexName=state_get("VECTOR_INDEX"),
                           vectors=vectores[i:i + 500])
    print(f"✔ {len(vectores)} vectores escritos en {state_get('VECTOR_BUCKET')}/{state_get('VECTOR_INDEX')}")


def buscar(consulta: str, top_k: int = 5, filtro: dict | None = None) -> list[dict]:
    """Consulta DIRECTA a S3 Vectors (desarrollo y evaluación; el agente usa la herramienta del Gateway)."""
    kwargs = {"vectorBucketName": state_get("VECTOR_BUCKET"), "indexName": state_get("VECTOR_INDEX"),
              "queryVector": {"float32": embedding(consulta)}, "topK": top_k,
              "returnMetadata": True, "returnDistance": True}
    if filtro:
        kwargs["filter"] = filtro
    res = _s3v().query_vectors(**kwargs)["vectors"]
    return [{"chunk_id": v["key"], "distancia": round(v["distance"], 4), **v.get("metadata", {})} for v in res]


def mostrar(resultados: list[dict]) -> None:
    for r in resultados:
        print(f"{r['distancia']:.4f}  {r['chunk_id']:38} {r.get('seccion', '')}")


def borrar_vectores(keys: list[str]) -> None:
    for i in range(0, len(keys), 500):
        _s3v().delete_vectors(vectorBucketName=state_get("VECTOR_BUCKET"), indexName=state_get("VECTOR_INDEX"),
                              keys=keys[i:i + 500])
    print(f"✔ {len(keys)} vectores eliminados del índice")
