import sys

import generation_metrics
import retrieval_metrics

if __name__ == "__main__":
    print("=== Retrieval metrics (deterministas: Precision@k, Recall@k, MRR) ===")
    retrieval_ok = retrieval_metrics.run()

    print("\n=== Generation metrics (qwen3:14b como juez local: faithfulness, answer relevancy) ===")
    generation_ok = generation_metrics.run()

    print(f"\nResultado: {'TODO OK' if retrieval_ok and generation_ok else 'HAY FALLOS'}")
    sys.exit(0 if retrieval_ok and generation_ok else 1)
