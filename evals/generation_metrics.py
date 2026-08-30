"""Metricas de generacion estilo RAGAS: faithfulness y answer relevancy.

Ambas requieren un LLM. Usan el mismo modelo local (qwen3:14b, via Ollama)
como generador Y como juez -- limitacion real y documentada, no ignorada:
es self-grading, no un juez independiente mas fuerte. Ver docs/29110 para
el detalle y por que se acepto igual (cero costo, 100% local, honesto
sobre el limite en vez de fingir objetividad que no existe).
"""

import math
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from golden_dataset import GOLDEN_DATASET
from rag_mcp_server.server import _embed, search_knowledge

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
MODEL = os.environ.get("JUDGE_MODEL", "qwen3:14b")
TOP_K = 3
N_SYNTHETIC_QUESTIONS = 3

# Subconjunto del dataset dorado: cada caso aca dispara ~5 llamadas al LLM
# local (generar respuesta, descomponer en claims, juzgar cada claim,
# generar preguntas sinteticas). Correr los 12 en cada CI hubiera sido
# minutos por corrida sin agregar señal nueva sobre la muestra completa.
SAMPLE = GOLDEN_DATASET[:6]

MIN_FAITHFULNESS = 0.8
MIN_ANSWER_RELEVANCY = 0.5


def _chat(prompt: str) -> str:
    resp = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        },
        timeout=180,
    )
    resp.raise_for_status()
    content = resp.json()["message"]["content"]
    if "</think>" in content:
        content = content.split("</think>", 1)[1]
    return content.strip()


def _generate_answer(query: str, context: str) -> str:
    prompt = (
        "Responde la pregunta usando SOLO la informacion del contexto. "
        "Se conciso, en español. Si el contexto no alcanza, decilo.\n\n"
        f"Contexto:\n{context}\n\nPregunta: {query}\n\nRespuesta:"
    )
    return _chat(prompt)


def _decompose_claims(answer: str) -> list[str]:
    prompt = (
        "Descompone la siguiente respuesta en afirmaciones atomicas "
        "independientes, una por linea, sin numerar ni agregar texto "
        f"extra:\n\n{answer}"
    )
    raw = _chat(prompt)
    return [line.strip("-* ").strip() for line in raw.splitlines() if line.strip()]


def _claim_supported(claim: str, context: str) -> bool:
    prompt = (
        f"Contexto:\n{context}\n\n"
        f'Afirmacion: "{claim}"\n\n'
        "Esta afirmacion esta respaldada por el contexto de arriba? "
        "Responde una sola palabra: SI o NO."
    )
    verdict = _chat(prompt).strip().upper()
    return verdict.startswith("SI") or verdict.startswith("SÍ")


def faithfulness(query: str, context: str) -> tuple[float, str]:
    answer = _generate_answer(query, context)
    claims = _decompose_claims(answer)
    if not claims:
        return 1.0, answer
    supported = sum(1 for c in claims if _claim_supported(c, context))
    return supported / len(claims), answer


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def answer_relevancy(query: str, answer: str) -> float:
    prompt = (
        f"Genera {N_SYNTHETIC_QUESTIONS} preguntas distintas que la "
        "siguiente respuesta podria estar contestando, una por linea, "
        f"sin numerar:\n\n{answer}"
    )
    raw = _chat(prompt)
    synthetic_qs = [q.strip("-* ").strip() for q in raw.splitlines() if q.strip()]
    synthetic_qs = synthetic_qs[:N_SYNTHETIC_QUESTIONS]
    if not synthetic_qs:
        return 0.0
    query_vec = _embed(query)
    sims = [_cosine(query_vec, _embed(q)) for q in synthetic_qs]
    return sum(sims) / len(sims)


def run() -> bool:
    faith_scores, relevancy_scores = [], []
    for case in SAMPLE:
        results = search_knowledge(query=case["query"], top_k=TOP_K)
        context = "\n\n".join(r["text"] for r in results)
        f_score, answer = faithfulness(case["query"], context)
        r_score = answer_relevancy(case["query"], answer)
        faith_scores.append(f_score)
        relevancy_scores.append(r_score)
        print(f"- {case['query'][:60]}")
        print(f"  faithfulness={f_score:.2f}  answer_relevancy={r_score:.2f}")

    mean_faith = sum(faith_scores) / len(faith_scores)
    mean_rel = sum(relevancy_scores) / len(relevancy_scores)
    print(f"\nFaithfulness promedio:     {mean_faith:.2f}")
    print(f"Answer relevancy promedio: {mean_rel:.2f}")

    ok = mean_faith >= MIN_FAITHFULNESS and mean_rel >= MIN_ANSWER_RELEVANCY
    if not ok:
        print(
            f"\nFALLO: faithfulness < {MIN_FAITHFULNESS} o "
            f"answer_relevancy < {MIN_ANSWER_RELEVANCY}"
        )
    return ok


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
