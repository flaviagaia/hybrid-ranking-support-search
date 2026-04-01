from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.sample_data import ensure_support_dataset


def _normalize(values: np.ndarray) -> np.ndarray:
    values = values.astype("float32")
    minimum = float(values.min())
    maximum = float(values.max())
    if maximum - minimum < 1e-8:
        return np.zeros_like(values, dtype="float32")
    return (values - minimum) / (maximum - minimum)


def run_pipeline(base_dir: str | Path) -> dict:
    base_path = Path(base_dir)
    dataset = ensure_support_dataset(base_path)
    docs = pd.read_csv(dataset["documents_path"])
    queries = pd.read_csv(dataset["queries_path"])

    corpus = (docs["title"] + " " + docs["content"]).tolist()
    vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    doc_matrix = vectorizer.fit_transform(corpus)

    results = []
    hit_count = 0

    for _, query_row in queries.iterrows():
        query_matrix = vectorizer.transform([query_row["query_text"]])
        lexical_scores = cosine_similarity(query_matrix, doc_matrix).reshape(-1)
        semantic_scores = cosine_similarity(query_matrix, doc_matrix).reshape(-1)
        quality_scores = docs["quality_score"].to_numpy(dtype="float32")
        click_scores = docs["click_score"].to_numpy(dtype="float32")
        priority_scores = docs["priority_flag"].to_numpy(dtype="float32")

        lexical_component = _normalize(lexical_scores)
        semantic_component = _normalize(semantic_scores)
        quality_component = _normalize(quality_scores)
        click_component = _normalize(click_scores)
        priority_component = _normalize(priority_scores)

        final_scores = (
            0.4 * lexical_component
            + 0.3 * semantic_component
            + 0.15 * quality_component
            + 0.1 * click_component
            + 0.05 * priority_component
        )

        ranked = docs.copy()
        ranked["lexical_score"] = np.round(lexical_component, 4)
        ranked["semantic_score"] = np.round(semantic_component, 4)
        ranked["business_score"] = np.round(quality_component * 0.6 + click_component * 0.4, 4)
        ranked["hybrid_score"] = np.round(final_scores, 4)
        ranked = ranked.sort_values(by="hybrid_score", ascending=False).reset_index(drop=True)

        top_doc_id = ranked.loc[0, "doc_id"]
        if top_doc_id == query_row["relevant_doc_id"]:
            hit_count += 1

        results.append(
            {
                "query_id": query_row["query_id"],
                "query_text": query_row["query_text"],
                "relevant_doc_id": query_row["relevant_doc_id"],
                "top_doc_id": top_doc_id,
                "top_hybrid_score": float(ranked.loc[0, "hybrid_score"]),
            }
        )

    result_df = pd.DataFrame(results)
    hit_rate_at_1 = float((result_df["top_doc_id"] == result_df["relevant_doc_id"]).mean())

    processed_dir = base_path / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = processed_dir / "hybrid_ranking_results.csv"
    report_path = processed_dir / "hybrid_ranking_report.json"

    result_df.to_csv(artifact_path, index=False)

    summary = {
        "dataset_source": "support_search_hybrid_ranking_sample",
        "document_count": int(len(docs)),
        "query_count": int(len(queries)),
        "hit_rate_at_1": round(hit_rate_at_1, 4),
        "result_artifact": str(artifact_path),
        "report_artifact": str(report_path),
    }
    report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary
