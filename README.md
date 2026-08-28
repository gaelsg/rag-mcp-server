# rag-mcp-server

Servidor MCP de RAG (Retrieval-Augmented Generation) sobre documentación propia. Fase 3 del roadmap de agentes: en vez de que un LLM razone solo con conocimiento genérico, busca semánticamente en tu propia base de conocimiento (por ahora, la bitácora de [proxmox-mcp-server](https://github.com/gaelsg/proxmox-mcp-server)) y trae los fragmentos relevantes como contexto.

## Arquitectura

- **Embeddings:** `bge-m3` (multilingüe, 1024 dims) corriendo local vía Ollama, acelerado por GPU (RTX 5080).
- **Vector DB:** Qdrant, en Docker/Podman, con almacenamiento persistente en `qdrant_storage/` (gitignored).
- **Corpus inicial:** `docs/bitacora/*.md` de proxmox-mcp-server, chunkeado por encabezado `##`.

## Setup

```bash
# 1. Ollama con el modelo de embeddings
sudo systemctl enable --now ollama
ollama pull bge-m3

# 2. Qdrant
docker run -d --name qdrant -p 6333:6333 -p 6334:6334 \
  -v ~/projects/rag-mcp-server/qdrant_storage:/qdrant/storage:Z \
  docker.io/qdrant/qdrant

# 3. Dependencias del proyecto
uv sync
cp .env.example .env
```

## Herramientas expuestas

- `index_corpus()` — reindexa (recrea la colección) todos los `.md` de `CORPUS_PATH` en Qdrant.
- `search_knowledge(query, top_k=5)` — búsqueda semántica, devuelve fragmentos con score, fuente y encabezado.

## Ejecutar

```bash
uv run rag-mcp-server
```

## Nota

`index_corpus()` hace `recreate_collection` (borra y reindexa todo) — simple para este tamaño de corpus, pero no incremental. Si el corpus crece mucho, cambiar a upsert selectivo por archivo modificado.
