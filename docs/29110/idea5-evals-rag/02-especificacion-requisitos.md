# Especificación de Requisitos — Idea 5: Evals de RAG estilo RAGAS

Según proceso **SI.2** del Perfil Básico ISO/IEC 29110.

## Requisitos funcionales

| ID | Requisito |
|---|---|
| RF1 | `evals/run_evals.py` corre las métricas de retrieval y de generación contra la infraestructura real (Qdrant + Ollama) y termina con exit code 0 solo si ambas capas pasan sus umbrales. |
| RF2 | Las métricas de retrieval (Precision@k, Recall@k, MRR) se calculan sin ningún LLM — deterministas, reproducibles. |
| RF3 | Las métricas de generación (faithfulness, answer relevancy) usan el mismo `qwen3:14b` local como generador y como juez. |
| RF4 | El dataset dorado consiste en queries reales sobre contenido real ya indexado, con la fuente esperada anotada a mano. |
| RF5 | Cada caso de generación reporta su score individual, no solo el promedio — para poder investigar casos puntuales. |

## Requisitos no funcionales

| ID | Requisito |
|---|---|
| RNF1 | Cero llamadas a APIs externas de pago — mismo criterio que el resto del roadmap ("100% local y gratis"). |
| RNF2 | El corpus indexado debe estar actualizado antes de correr los evals (detectado como bug real: índice desactualizado por no haber reindexado tras nuevas entradas de bitácora). |
| RNF3 | Las limitaciones de la metodología (self-grading, no-determinismo, granularidad del ground truth) se documentan explícitamente, no se ocultan detrás de un score que parezca más objetivo de lo que es. |

## Fuera de alcance
- Usar la librería `ragas` (paquete de PyPI) en vez de una implementación propia.
- Ground truth a nivel de chunk/heading (queda como pendiente documentado, ver `04-verificacion.md`).
- Integración con CI/CD.
