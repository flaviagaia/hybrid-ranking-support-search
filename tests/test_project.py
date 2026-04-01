from __future__ import annotations

import unittest
from pathlib import Path

from src.modeling import run_pipeline


class HybridRankingSupportSearchTestCase(unittest.TestCase):
    def test_pipeline_contract(self) -> None:
        project_dir = Path(__file__).resolve().parents[1]
        summary = run_pipeline(project_dir)
        self.assertEqual(summary["document_count"], 6)
        self.assertEqual(summary["query_count"], 4)
        self.assertGreaterEqual(summary["hit_rate_at_1"], 0.75)


if __name__ == "__main__":
    unittest.main()
