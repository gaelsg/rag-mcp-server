# Verificación — Idea 5: Evals de RAG estilo RAGAS

Según proceso **SI.5** del Perfil Básico ISO/IEC 29110. Casos mapeados a los criterios de aceptación del [plan de proyecto](01-plan-proyecto.md).

| # | Caso de prueba | Resultado |
|---|---|---|
| 1 | `evals/run_evals.py` corre de punta a punta contra infra real, exit code 0 | ✅ Corrida real (2026-08-30) contra Qdrant (`127.0.0.1:6333`) y Ollama (`127.0.0.1:11434`, `qwen3:14b` + `bge-m3`) reales: `Resultado: TODO OK`. |
| 2 | Recall@3 ≥ 0.9 y MRR ≥ 0.8 sobre el dataset completo | ✅ Recall@3 = **1.00** (12/12 queries), MRR = **0.89**. Precision@3 = 0.64 (no es criterio de aceptación, reportado igual — ver hallazgo abajo). |
| 3 | Faithfulness ≥ 0.8 y answer relevancy ≥ 0.5 sobre la muestra de generación | ✅ Faithfulness = **0.97** (una corrida) / 0.92 (otra corrida, ver nota de no-determinismo). Answer relevancy = **0.70** / 0.68. Ambas corridas por encima de umbral. |
| 4 | Al menos un hallazgo real sobre la calidad del sistema, no hipotético | ✅ Ver "Hallazgo real" abajo. |

## Hallazgo real: Recall@3 = 1.00 no implica que se haya recuperado el chunk correcto

Investigando por qué la query "qué modelo de embeddings usa el sistema RAG y por qué se eligió" tuvo faithfulness bajo en una corrida (0.50 — el modelo respondió honestamente "la información no está en el contexto" en vez de alucinar), se encontró la causa raíz inspeccionando el retrieval directo:

- El archivo correcto (`rag-mcp-server/2026-08-28.md`) sí apareció en el top-3 de resultados — pero vía el chunk `## Pendiente` (score 0.381), no `## Decisiones` (score 0.346, el que realmente contiene la respuesta sobre `bge-m3`).
- Pidiendo el top-6 en vez de top-3 se confirmó: `## Decisiones` rankeó **6to**, fuera del corte usado en la eval.
- Como el ground truth del dataset dorado es a nivel de *archivo*, no de *chunk*, la métrica de Recall@3 contó esto como un acierto — técnicamente el archivo correcto "apareció", aunque el fragmento específico con la respuesta no.

**Conclusión del hallazgo:** las dos capas de evals se validaron mutuamente de una forma reveladora — retrieval (con ground truth demasiado grueso) dio una señal falsamente optimista, mientras que generation (evaluando el resultado final real) sí detectó que el sistema no tenía lo necesario para responder, y además el modelo se comportó bien ante esa carencia (admitió no saber en vez de inventar). Es evidencia a favor de mantener ambas capas de evals, no solo la de retrieval — una sola capa hubiera reportado "todo bien" sobre un caso que en la práctica falla.

No corregido en esta iteración (ver pendientes en `01-plan-proyecto.md` / bitácora) — requiere rehacer el ground truth a nivel de heading, cambio de mayor alcance que el de esta idea.

## Nota sobre no-determinismo, verificada empíricamente

La misma query, mismo contexto recuperado, dos corridas distintas de `generation_metrics.py`: faithfulness 0.50 en una, 0.80 en otra (Ollama sin temperatura fija, sampling real). Documentado explícitamente para que los umbrales se lean como señal de tendencia sobre el promedio, no como un valor exacto reproducible por caso — mismo criterio de honestidad ya aplicado con la regla `VaultSealed` no verificada en la Idea 3 de `observability`.

## Incidente durante la implementación

**Índice de Qdrant desactualizado y contaminado con `README.md`.** Antes de armar el dataset dorado se encontró que la última reindexación era de varios días atrás (faltaban 3 de 6 archivos de bitácora ya escritos) y que `CORPUS_PATHS` indexaba `docs/bitacora/README.md` como si fuera una entrada real (glob `*.md` sin filtrar por nombre de fecha). Corregido: `glob("[0-9]*.md")` + reindexado (5 archivos, 34 chunks) antes de construir el ground truth, para no anotar queries contra un corpus que no reflejaba el estado real.

## Conclusión
4 de 4 criterios de aceptación verificados contra infraestructura real. El hallazgo más valioso de esta idea no fue "los números pasan" sino la interacción entre las dos capas de evals exponiendo una limitación real del propio diseño del dataset dorado — documentado como pendiente concreto, no como nota vaga.
