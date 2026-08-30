# Plan de Proyecto — Idea 5: Evals de RAG estilo RAGAS

Según proceso **PM.1** del Perfil Básico ISO/IEC 29110.

## Objetivo
Reemplazar "funcionó en la demo" por métricas reales de calidad de retrieval y generación sobre `rag-mcp-server` — las mismas familias de métricas que usa RAGAS (framework estándar de la industria para evaluar sistemas RAG), implementadas a mano y corriendo 100% local, sin depender de una API externa ni de una librería pesada con supuestos de OpenAI por defecto.

## Alcance

**Incluye:**
- Dataset dorado de queries reales (no sintéticas) sobre el corpus real ya indexado (bitácora de `proxmox-mcp-server` + `rag-mcp-server`), con la fuente esperada para cada una.
- Métricas de retrieval deterministas: Precision@k, Recall@k, MRR.
- Métricas de generación estilo RAGAS, con `qwen3:14b` local como generador y juez: faithfulness (afirmaciones de la respuesta vs. contexto recuperado) y answer relevancy (preguntas sintéticas generadas desde la respuesta vs. la query original, comparadas por similitud coseno de embeddings).
- Orquestador `evals/run_evals.py` con exit code, mismo patrón que `devops-multiagent/evals`.

**No incluye (fuera de alcance v1):**
- Usar la librería `ragas` real — se implementan las métricas a mano, más simple de auditar/entender y sin las dependencias pesadas de esa librería (pensada por defecto para APIs de OpenAI).
- Ground truth a nivel de chunk (heading) — el dataset dorado usa granularidad de archivo; ver el hallazgo documentado en `04-verificacion.md` sobre las consecuencias de esta decisión.
- Integrar los evals a un pipeline de CI (ver Idea 4 en `devops-multiagent` para el patrón ya construido) — no aplicado a este repo todavía.

## Entregables
1. `evals/golden_dataset.py`, `evals/retrieval_metrics.py`, `evals/generation_metrics.py`, `evals/run_evals.py` en `rag-mcp-server`.
2. Fix de un bug real encontrado al preparar los evals: `index_corpus()` indexaba `README.md` como si fuera una entrada de bitácora.
3. README actualizado con la sección de evals.
4. Esta serie de documentos 29110 + bitácora.

## Riesgos identificados
| Riesgo | Mitigación |
|---|---|
| El juez (LLM local) es el mismo modelo que genera — self-grading, sesgo hacia calificarse bien a sí mismo | Aceptado y documentado explícitamente, no escondido. Los scores se leen como señal relativa entre corridas, no como verdad objetiva. |
| Scores de generation no deterministas (sampling del LLM) | Documentado en la bitácora con un caso real (mismo query, mismo contexto, faithfulness 0.50 vs 0.80 en corridas distintas). Umbrales pensados sobre el promedio de la muestra, no por caso individual. |
| Dataset dorado chico (12 queries, corpus de 5 archivos) puede no generalizar | Aceptado para v1 — corpus real es chico hoy; el dataset crece junto con la bitácora real, no con datos inventados. |

## Criterios de aceptación
- `evals/run_evals.py` corre de punta a punta contra Qdrant y Ollama reales y termina con exit code 0.
- Recall@3 ≥ 0.9 y MRR ≥ 0.8 sobre el dataset dorado completo.
- Faithfulness promedio ≥ 0.8 y answer relevancy promedio ≥ 0.5 sobre la muestra de generación.
- Al menos un hallazgo real (no hipotético) sobre la calidad del sistema RAG actual, obtenido de correr los evals contra la infraestructura real, no simulada.
