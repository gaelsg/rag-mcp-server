# Diseño — Idea 5: Evals de RAG estilo RAGAS

Según proceso **SI.3** del Perfil Básico ISO/IEC 29110.

## Componentes

```
evals/run_evals.py
   │
   ├── retrieval_metrics.run()  (determinista)
   │       │
   │       ├── golden_dataset.GOLDEN_DATASET (12 queries reales)
   │       └── search_knowledge()  ──► Qdrant real
   │               │
   │               └── Precision@3, Recall@3, MRR
   │
   └── generation_metrics.run()  (LLM-as-judge)
           │
           ├── SAMPLE = golden_dataset[:6]
           ├── search_knowledge() ──► contexto real
           ├── _generate_answer(query, context) ──► Ollama (qwen3:14b)
           ├── _decompose_claims(answer)          ──► Ollama (qwen3:14b)
           ├── _claim_supported(claim, context) x N ──► Ollama (qwen3:14b)
           │       └── faithfulness = soportadas / total
           ├── answer_relevancy(query, answer)
           │       ├── genera preguntas sintéticas ──► Ollama (qwen3:14b)
           │       ├── embed(query), embed(cada pregunta) ──► Ollama (bge-m3)
           │       └── promedio de similitud coseno
           └── promedios + umbrales
```

## Decisiones de diseño

**Implementación propia de las métricas, no la librería `ragas`.** El objetivo del roadmap es aprendizaje demostrable, no integrar una caja negra — construir faithfulness y answer relevancy a mano (siguiendo la metodología real que documenta RAGAS: descomposición en afirmaciones atómicas + juicio contra contexto; preguntas sintéticas + similitud coseno) obliga a entender exactamente qué miden esos números. Efecto secundario: cero dependencias nuevas pesadas, todo corre sobre infraestructura que ya existía (Ollama, `requests`).

**Ground truth de retrieval a nivel de archivo, no de chunk.** Más simple de armar a mano leyendo la bitácora real. Trade-off aceptado y su consecuencia real quedó documentada en la verificación: Recall@3 puede "pasar" aunque el chunk específicamente relevante no esté entre los recuperados, si otro chunk del mismo archivo sí lo está.

**Faithfulness vía descomposición en afirmaciones atómicas, no un único score holístico.** Pedirle al modelo "¿es fiel esta respuesta, sí o no?" de un tirón es una caja negra con un solo número. Descomponer en afirmaciones y juzgar cada una por separado (a) es lo que realmente hace RAGAS, (b) da trazabilidad — se puede ver exactamente qué afirmación falló y por qué — y (c) fue lo que permitió diagnosticar el hallazgo real documentado en `04-verificacion.md`.

**Answer relevancy vía preguntas sintéticas + similitud coseno, no un juicio directo de "¿es relevante?".** Mismo criterio: es el método real de RAGAS para esta métrica (generar N preguntas que la respuesta podría estar contestando, compararlas con la pregunta original) y es más robusto que pedirle a un LLM que se autoevalúe con una etiqueta subjetiva — acá el juicio final lo da una medida geométrica (coseno) sobre embeddings, no otra llamada de "sí/no" al mismo modelo.

**Juez = generador (mismo `qwen3:14b`), sin separar roles.** Alternativa considerada: usar un modelo distinto (más grande, o una API externa) como juez para reducir el sesgo de auto-evaluación. Descartada por romper el criterio "100% local y gratis" del proyecto — se documenta la limitación en vez de resolverla con una dependencia externa que contradice el resto del roadmap.

**Subconjunto de 6 queries para generation, no las 12 completas.** Cada caso de `generation_metrics` dispara ~5 llamadas al LLM local (respuesta, descomposición, N juicios de afirmación, N preguntas sintéticas) — correr las 12 hubiera multiplicado el tiempo de corrida sin agregar señal proporcional sobre una muestra ya representativa de los 5 archivos del corpus.

**Bug de indexado corregido antes de construir el dataset, no documentado como "conocido" y dejado.** `README.md` de `docs/bitacora/` se indexaba como si fuera contenido real (glob sin filtrar). Corregirlo antes de anotar el ground truth evita que el dataset dorado quede contaminado desde el día uno con una fuente que no debería existir.
