from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

import pandas as pd


DOCUMENTS = [
    ("DOC-1001", "Billing refund workflow", "How to request a refund for a duplicated invoice payment.", 0.86, 120, 0),
    ("DOC-1002", "Password reset guide", "Reset the employee portal password and recover MFA access.", 0.92, 340, 0),
    ("DOC-1003", "Invoice processing exception", "Handle invoice OCR failures and route finance exceptions.", 0.88, 88, 1),
    ("DOC-1004", "Shipping delay escalation", "Escalation playbook for delayed deliveries and customer follow-up.", 0.81, 76, 0),
    ("DOC-1005", "Chargeback dispute policy", "Respond to card chargebacks and provide payment evidence.", 0.9, 156, 1),
    ("DOC-1006", "Subscription cancellation FAQ", "Cancel recurring plans and confirm contract end dates.", 0.79, 190, 0),
]

QUERIES = [
    ("Q-1001", "customer asked for refund of duplicated payment", "DOC-1001"),
    ("Q-1002", "portal password reset and mfa recovery", "DOC-1002"),
    ("Q-1003", "ocr invoice error needs finance review", "DOC-1003"),
    ("Q-1004", "chargeback documentation and dispute response", "DOC-1005"),
]


def _atomic_write(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", suffix=".csv", delete=False, dir=path.parent, encoding="utf-8") as tmp_file:
        temp_path = Path(tmp_file.name)
    try:
        df.to_csv(temp_path, index=False)
        temp_path.replace(path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def ensure_support_dataset(base_dir: str | Path) -> dict[str, str]:
    base_path = Path(base_dir)
    raw_dir = base_path / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    documents_path = raw_dir / "support_documents.csv"
    queries_path = raw_dir / "evaluation_queries.csv"

    documents_df = pd.DataFrame(
        DOCUMENTS,
        columns=["doc_id", "title", "content", "quality_score", "click_score", "priority_flag"],
    )
    queries_df = pd.DataFrame(QUERIES, columns=["query_id", "query_text", "relevant_doc_id"])

    _atomic_write(documents_df, documents_path)
    _atomic_write(queries_df, queries_path)

    return {"documents_path": str(documents_path), "queries_path": str(queries_path)}
