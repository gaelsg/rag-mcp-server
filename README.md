# rag-mcp-server

Servidor MCP de RAG (Retrieval-Augmented Generation) sobre documentación propia. Fase 3 del roadmap de agentes: en vez de que un LLM razone solo con conocimiento genérico, busca semánticamente en tu propia base de conocimiento (por ahora, la bitácora de [proxmox-mcp-server](https://github.com/gaelsg/proxmox-mcp-server)) y trae los fragmentos relevantes como contexto.

## Arquitectura

- **Embeddings:** `bge-m3` (multilingüe, 1024 dims) corriendo local vía Ollama, acelerado por GPU (RTX 5080).
- **Vector DB:** Qdrant, en Docker/Podman, con almacenamiento persistente en `qdrant_storage/` (gitignored).
- **Corpus inicial:** `docs/bitacora/*.md` de proxmox-mcp-server, chunkeado por encabezado `##`. Solo archivos con nombre de fecha (`[0-9]*.md`) — se excluye `README.md` a propósito, ver `docs/bitacora/`.

## Setup

```bash
# 1. Ollama con el modelo de embeddings
sudo systemctl enable --now ollama
ollama pull bge-m3

# 2. Qdrant, como servicio systemd --user via Podman Quadlet (sobrevive reboots)
mkdir -p ~/.config/containers/systemd
cp systemd/qdrant.container ~/.config/containers/systemd/
loginctl enable-linger $USER   # para que arranque sin sesion activa
systemctl --user daemon-reload
systemctl --user start qdrant.service

# 3. Dependencias del proyecto
uv sync
cp .env.example .env
```

Qdrant corre gestionado por systemd (Podman Quadlet, `~/.config/containers/systemd/qdrant.container`), no `docker run` manual — así sobrevive un reinicio del server sin intervención. Ver `systemd/qdrant.container` y `docs/bitacora/2026-08-29.md`.

## Herramientas expuestas

- `index_corpus()` — reindexa (recrea la colección) todos los `.md` de `CORPUS_PATH` en Qdrant.
- `search_knowledge(query, top_k=5)` — búsqueda semántica, devuelve fragmentos con score, fuente y encabezado.

## Ejecutar

```bash
uv run rag-mcp-server
```

## Tracing

Con `OTEL_EXPORTER_OTLP_ENDPOINT` seteado (ver `.env.example`), `search_knowledge` queda en Jaeger con dos spans hijos reales (`ollama.embed`, `qdrant.query_points`) además del span automático de la tool call — separa cuánto tiempo se va en embedding vs. en la consulta al vector DB. Ver [`devops-multiagent`](https://github.com/gaelsg/devops-multiagent#tracing-distribuido-opentelemetry--jaeger) para el detalle completo.

## Evals (estilo RAGAS)

```bash
uv run python evals/run_evals.py
```

Dos capas, igual que en `devops-multiagent`:

- **`evals/retrieval_metrics.py`** — Precision@k, Recall@k, MRR, deterministas, contra Qdrant real. `evals/golden_dataset.py` tiene 12 queries reales (no sintéticas) sobre el contenido real de la bitácora, cada una con su fuente esperada armada a mano leyendo los `.md`.
- **`evals/generation_metrics.py`** — faithfulness (¿la respuesta generada solo afirma lo que dice el contexto recuperado?) y answer relevancy (¿la respuesta responde lo que se preguntó?), estilo RAGAS: `qwen3:14b` genera la respuesta, la descompone en afirmaciones atómicas, y juzga cada una contra el contexto; para relevancy, genera preguntas sintéticas a partir de la respuesta y mide similitud coseno (embeddings `bge-m3`) contra la query original.

**Limitación documentada, no escondida:** el juez es el mismo modelo local que genera (`qwen3:14b`) — self-grading, no un juez independiente más fuerte. Se aceptó por ser 100% local y gratis, coherente con el resto del proyecto; los scores hay que leerlos como señal relativa (¿bajó vs. la corrida anterior?), no como verdad absoluta. Detalle completo en `docs/29110/idea5-evals-rag/`.

## Nota

`index_corpus()` hace `recreate_collection` (borra y reindexa todo) — simple para este tamaño de corpus, pero no incremental. Si el corpus crece mucho, cambiar a upsert selectivo por archivo modificado.
