# 2026-09-01 — El corpus ahora indexa los 9 repos, no solo 2

Pedido del usuario: "conectar más agentes/RAGs del portafolio entre sí". Antes de diseñar nada
nuevo, se revisó qué había realmente conectado hoy -- y el hallazgo fue más básico de lo esperado:
`CORPUS_PATH` solo apuntaba a `proxmox-mcp-server` y a este mismo repo (más `plane-sync`, agregado
el mismo día). Los otros 7 repos del portafolio (`devops-multiagent`, `k8s-mcp-server`,
`nextcloud-mcp-server`, `observability`, `pm-agent`, `proxmox-iac`, `vault-secrets`) tienen
bitácoras reales y extensas -- Vault, GitOps, policy-as-code, supply chain, tracing, todo lo
documentado en el segundo roadmap y en la fase post-roadmap -- pero eran completamente invisibles
para el Diagnostician. No hacía falta arquitectura multi-RAG nueva para el primer paso real: hacía
falta terminar de conectar el RAG que ya existe.

## Cambio

`CORPUS_PATH` (`.env`/`.env.example`) pasa de 3 entradas a 10 -- las 9 carpetas `docs/bitacora/`
del portafolio más `plane-sync`. `index_corpus()` no cambió (mismo mecanismo de siempre, glob +
`recreate_collection`), solo la lista de directorios que lee.

## Verificado

Reindex real: de 12 archivos/61 chunks a **51 archivos/258 chunks**. Tres búsquedas semánticas
sobre contenido que antes era imposible de encontrar (el bug de sintaxis Rego en `observability`,
la protección SSRF de Plane en `devops-multiagent`, el gotcha de `nesting` en `proxmox-iac`) --
las tres devolvieron el resultado correcto como top match. Confirmado además con el flujo real que
se usa día a día (`devops-agent diagnose "¿qué incidentes reales tuvimos con Vault?"`) -- respuesta
correcta y grounded, dos incidentes reales de `vault-secrets` que el Diagnostician no podía ver
hasta este cambio.

## Pendiente (visión de más largo plazo, no esta iteración)

Esto sigue siendo un solo RAG (una colección de Qdrant), no "varios perfiles conectados" como
describía la visión original -- pero es la base correcta antes de pensar en separar por dominio:
no tenía sentido diseñar multi-RAG cuando ni siquiera el RAG único veía todo el portafolio.
