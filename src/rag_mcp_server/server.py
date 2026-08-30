import os
import re
import uuid
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from mcp.server.mcpserver import MCPServer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

load_dotenv()

mcp = MCPServer("rag-mcp-server")

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "bge-m3")
EMBED_DIM = 1024

QDRANT_HOST = os.environ.get("QDRANT_HOST", "127.0.0.1")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
COLLECTION = os.environ.get("QDRANT_COLLECTION", "bitacora")

CORPUS_PATHS = [
    Path(p.strip()).expanduser()
    for p in os.environ.get(
        "CORPUS_PATH",
        "~/projects/proxmox-mcp-server/docs/bitacora,~/projects/rag-mcp-server/docs/bitacora",
    ).split(",")
]


def _qdrant() -> QdrantClient:
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def _embed(text: str) -> list[float]:
    resp = requests.post(
        f"{OLLAMA_HOST}/api/embed",
        json={"model": EMBED_MODEL, "input": text},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["embeddings"][0]


def _chunk_markdown(text: str, source: str) -> list[dict[str, Any]]:
    """Parte un markdown en chunks por encabezado ## (o el documento completo si no hay)."""
    sections = re.split(r"\n(?=## )", text)
    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        heading_match = re.match(r"^#+\s*(.+)", section)
        heading = heading_match.group(1) if heading_match else source
        chunks.append({"text": section, "source": source, "heading": heading})
    return chunks


@mcp.tool()
def index_corpus() -> dict[str, Any]:
    """Reindexa todos los .md de CORPUS_PATH (bitacora de proxmox-mcp-server) en Qdrant."""
    client = _qdrant()
    client.recreate_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=EMBED_DIM, distance=Distance.COSINE),
    )

    # docs/bitacora/2026-08-28.md -> proyecto = parents[1] (raiz del repo)
    files = sorted(
        (path, corpus_path.parents[1].name)
        for corpus_path in CORPUS_PATHS
        for path in corpus_path.glob("[0-9]*.md")
    )
    points: list[PointStruct] = []
    for path, project in files:
        text = path.read_text(encoding="utf-8")
        source = f"{project}/{path.name}"
        for chunk in _chunk_markdown(text, source):
            vector = _embed(chunk["text"])
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "text": chunk["text"],
                        "source": chunk["source"],
                        "heading": chunk["heading"],
                    },
                )
            )

    if points:
        client.upsert(collection_name=COLLECTION, points=points)

    return {"files_indexed": len(files), "chunks_indexed": len(points)}


@mcp.tool()
def search_knowledge(query: str, top_k: int = 5) -> list[dict[str, Any]]:
    """Busca en la base de conocimiento (bitacora indexada) los fragmentos mas relevantes para query."""
    vector = _embed(query)
    results = _qdrant().query_points(
        collection_name=COLLECTION,
        query=vector,
        limit=top_k,
    )
    return [
        {
            "score": point.score,
            "source": point.payload.get("source"),
            "heading": point.payload.get("heading"),
            "text": point.payload.get("text"),
        }
        for point in results.points
    ]


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
