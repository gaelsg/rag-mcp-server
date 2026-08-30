"""Metricas de retrieval deterministas (sin LLM): Precision@k, Recall@k, MRR.
Corren contra Qdrant real via search_knowledge(), la misma funcion que usa
el agente -- no un mock del pipeline de retrieval.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from golden_dataset import GOLDEN_DATASET
from rag_mcp_server.server import search_knowledge

TOP_K = 3

# Corpus real pero chico (5 archivos, ~34 chunks): se exige un piso alto
# porque cada query del dataset dorado tiene una unica fuente correcta y
# clara -- no hay ambiguedad real que justifique tolerancia.
MIN_RECALL = 0.9
MIN_MRR = 0.8


def precision_at_k(retrieved_sources: list[str], expected_sources: list[str]) -> float:
    if not retrieved_sources:
        return 0.0
    hits = sum(1 for s in retrieved_sources if s in expected_sources)
    return hits / len(retrieved_sources)


def recall_at_k(retrieved_sources: list[str], expected_sources: list[str]) -> float:
    if not expected_sources:
        return 1.0
    hits = sum(1 for s in expected_sources if s in retrieved_sources)
    return hits / len(expected_sources)


def reciprocal_rank(retrieved_sources: list[str], expected_sources: list[str]) -> float:
    for i, s in enumerate(retrieved_sources, start=1):
        if s in expected_sources:
            return 1 / i
    return 0.0


def run() -> bool:
    precisions, recalls, rrs = [], [], []
    print(f"{'query':<68} {'P@' + str(TOP_K):>6} {'R@' + str(TOP_K):>6} {'RR':>6}")
    for case in GOLDEN_DATASET:
        results = search_knowledge(query=case["query"], top_k=TOP_K)
        retrieved = [r["source"] for r in results]
        p = precision_at_k(retrieved, case["expected_sources"])
        r = recall_at_k(retrieved, case["expected_sources"])
        rr = reciprocal_rank(retrieved, case["expected_sources"])
        precisions.append(p)
        recalls.append(r)
        rrs.append(rr)
        print(f"{case['query'][:68]:<68} {p:>6.2f} {r:>6.2f} {rr:>6.2f}")

    mean_p = sum(precisions) / len(precisions)
    mean_r = sum(recalls) / len(recalls)
    mrr = sum(rrs) / len(rrs)
    print(f"\nPrecision@{TOP_K} promedio: {mean_p:.2f}")
    print(f"Recall@{TOP_K} promedio:    {mean_r:.2f}")
    print(f"MRR:                     {mrr:.2f}")

    ok = mean_r >= MIN_RECALL and mrr >= MIN_MRR
    if not ok:
        print(f"\nFALLO: recall < {MIN_RECALL} o MRR < {MIN_MRR}")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
