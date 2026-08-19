from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from app import generate, offline_generate


SAMPLE = {
    "idea": "A tool that converts support-ticket history into a weekly action plan for small SaaS teams.",
    "customer": "Customer-success managers at small subscription software companies",
    "problem": "Managers manually review hundreds of tickets and miss repeated issues that increase resolution time.",
    "solution": "Summarize recurring ticket themes and rank the actions likely to reduce support workload.",
    "revenue": "Monthly subscription paid by the customer-success team",
    "advantage": "A simpler workflow specialized for small teams with limited analytics staff",
    "mode": "offline",
}


class StartupValidatorTests(unittest.TestCase):
    def test_score_is_bounded_and_dimensioned(self) -> None:
        result = offline_generate(SAMPLE)
        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 100)
        self.assertEqual(sum(result["dimension_scores"].values()), result["score"])

    def test_generates_three_validation_experiments(self) -> None:
        self.assertEqual(len(generate(SAMPLE)["validation_experiments"]), 3)

    def test_output_is_deterministic(self) -> None:
        self.assertEqual(generate(SAMPLE), generate(SAMPLE))

    def test_vague_input_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            generate({"idea": "An app", "customer": "People", "problem": "It helps", "mode": "offline"})

    def test_openai_mode_requires_local_key(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError):
                generate({**SAMPLE, "mode": "openai"})


if __name__ == "__main__":
    unittest.main()
