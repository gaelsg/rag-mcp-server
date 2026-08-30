"""Dataset dorado: queries reales sobre la bitacora indexada, con la fuente
esperada para cada una. Armado a mano leyendo el contenido real de
docs/bitacora/*.md en proxmox-mcp-server y rag-mcp-server -- no sintetico,
no generado por un LLM. Cada query corresponde a algo que de verdad esta
documentado en una sola entrada (o en un numero acotado de entradas).
"""

GOLDEN_DATASET = [
    {
        "query": "por que se separaron los tokens de lectura y escritura de proxmox",
        "expected_sources": ["proxmox-mcp-server/2026-08-28.md"],
    },
    {
        "query": "que modelo de embeddings usa el sistema RAG y por que se eligio",
        "expected_sources": ["rag-mcp-server/2026-08-28.md"],
    },
    {
        "query": "por que mcp-agent termino siendo administrador global en Portainer en vez de solo lectura",
        "expected_sources": ["proxmox-mcp-server/2026-08-28-idea3.md"],
    },
    {
        "query": "como se resolvio que Qdrant no sobreviviera un reboot del servidor",
        "expected_sources": ["rag-mcp-server/2026-08-29.md"],
    },
    {
        "query": "donde viven los secretos de Proxmox despues de la migracion a Vault",
        "expected_sources": ["proxmox-mcp-server/2026-08-29-vault.md"],
    },
    {
        "query": "que pasa si Vault no responde cuando arranca el servidor de proxmox",
        "expected_sources": ["proxmox-mcp-server/2026-08-29-vault.md"],
    },
    {
        "query": "por que falla curl a qdrant con localhost pero funciona con 127.0.0.1",
        "expected_sources": ["rag-mcp-server/2026-08-28.md"],
    },
    {
        "query": "que guardrails tienen las tools de escritura de power management en proxmox",
        "expected_sources": ["proxmox-mcp-server/2026-08-28.md"],
    },
    {
        "query": "como se resolvio el problema de nombres de archivo ambiguos entre corpus del RAG",
        "expected_sources": ["rag-mcp-server/2026-08-28.md"],
    },
    {
        "query": "por que Portainer Community Edition no sirve para dar acceso de solo lectura real",
        "expected_sources": ["proxmox-mcp-server/2026-08-28-idea3.md"],
    },
    {
        "query": "que es Podman Quadlet y por que se prefirio sobre podman generate systemd",
        "expected_sources": ["rag-mcp-server/2026-08-29.md"],
    },
    {
        "query": "que se descubrio al probar list_containers sobre la infraestructura real de Proxmox",
        "expected_sources": ["proxmox-mcp-server/2026-08-28.md"],
    },
]
