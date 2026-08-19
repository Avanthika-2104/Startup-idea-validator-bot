"""Evidence-focused startup idea validator with offline and OpenAI modes."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from ai_client import generate_json
from server import serve


APP_TITLE = "VentureCheck Startup Validator"
BASE_DIR = Path(__file__).resolve().parent
SYSTEM_INSTRUCTIONS = """You are an evidence-focused startup discovery assistant.
Evaluate only the information supplied by the user. Never invent market size, competitors,
customer interviews, demand, revenue, or traction. Treat the result as a hypothesis review,
not proof that a business will succeed. Return only valid JSON matching the requested schema."""


def clean(value: Any, *, limit: int = 4000) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z][a-z'-]{2,}", text.lower()))


def bounded_score(text: str, *, base: int, divisor: int, bonus_terms: set[str]) -> int:
    words = tokens(text)
    score = base + min(12, len(words) // divisor)
    score += min(5, len(words & bonus_terms) * 2)
    return max(0, min(20, score))


def offline_generate(payload: dict[str, Any]) -> dict[str, Any]:
    idea = clean(payload.get("idea"))
    customer = clean(payload.get("customer"))
    problem = clean(payload.get("problem"))
    solution = clean(payload.get("solution") or idea)
    revenue = clean(payload.get("revenue"))
    advantage = clean(payload.get("advantage"))
    if len(idea) < 20 or len(customer) < 10 or len(problem) < 20:
        raise ValueError("Describe the idea, target customer, and problem in more detail.")

    scores = {
        "Problem clarity": bounded_score(problem, base=5, divisor=3, bonus_terms={"time", "cost", "delay", "error", "difficult", "manual"}),
        "Customer specificity": bounded_score(customer, base=4, divisor=2, bonus_terms={"team", "owner", "student", "manager", "company", "professional"}),
        "Solution fit": bounded_score(solution, base=4, divisor=3, bonus_terms=tokens(problem)),
        "Revenue logic": bounded_score(revenue, base=2, divisor=2, bonus_terms={"subscription", "monthly", "license", "fee", "commission", "paid"}),
        "Differentiation": bounded_score(advantage, base=2, divisor=2, bonus_terms={"faster", "simpler", "cheaper", "specialized", "automatic", "unique"}),
    }
    total = sum(scores.values())
    if total >= 75:
        verdict = "Promising hypothesis — validate with customers"
    elif total >= 55:
        verdict = "Worth testing — important assumptions remain"
    else:
        verdict = "Needs sharper definition before building"

    customer_label = customer.rstrip(".")
    return {
        "mode": "offline-demo",
        "score": total,
        "verdict": verdict,
        "dimension_scores": scores,
        "strengths": [
            f"The proposed user group is stated as: {customer_label}.",
            "The idea can be tested without building a complete product first.",
        ],
        "critical_assumptions": [
            f"People in this group experience the problem often enough: {customer_label}.",
            "The proposed solution is meaningfully better than the current workaround.",
            "At least one buyer has a clear reason and budget to pay.",
        ],
        "risks": [
            "The description is not evidence of real demand.",
            "Competitor and alternative-workflow research is still required.",
            "The buyer and the end user may be different people.",
        ],
        "validation_experiments": [
            {"name": "Problem interviews", "method": "Interview 7 target users without pitching the solution.", "success_metric": "At least 5 independently describe the same painful workflow."},
            {"name": "Landing-page test", "method": "Show the value proposition and one clear call to action.", "success_metric": "Measure qualified sign-ups rather than page views alone."},
            {"name": "Concierge pilot", "method": "Deliver the result manually for 3–5 users before automating it.", "success_metric": "Users return, complete the workflow, or agree to a paid pilot."},
        ],
        "next_questions": [
            "What do customers currently do instead?",
            "Who experiences the pain, and who approves payment?",
            "What measurable outcome should improve within the first week?",
        ],
        "disclaimer": "This is a structured hypothesis review, not market validation or financial advice.",
    }


def ai_generate(payload: dict[str, Any]) -> dict[str, Any]:
    required = {name: clean(payload.get(name)) for name in ("idea", "customer", "problem")}
    if any(len(value) < 10 for value in required.values()):
        raise ValueError("Describe the idea, target customer, and problem in more detail.")
    request = {
        "idea": required["idea"],
        "target_customer": required["customer"],
        "problem": required["problem"],
        "solution": clean(payload.get("solution") or required["idea"]),
        "revenue_model": clean(payload.get("revenue")),
        "differentiation": clean(payload.get("advantage")),
        "schema": {
            "mode": "openai", "score": "integer 0-100", "verdict": "string",
            "dimension_scores": {"dimension": "integer 0-20"},
            "strengths": ["string"], "critical_assumptions": ["string"], "risks": ["string"],
            "validation_experiments": [{"name": "string", "method": "string", "success_metric": "string"}],
            "next_questions": ["string"], "disclaimer": "string",
        },
    }
    result = generate_json(
        instructions=SYSTEM_INSTRUCTIONS,
        prompt="Review this startup hypothesis and propose evidence-gathering experiments:\n" + json.dumps(request),
        max_output_tokens=1800,
    )
    score = result.get("score")
    if not isinstance(score, int) or not 0 <= score <= 100:
        raise RuntimeError("The AI returned an invalid validation score.")
    if not isinstance(result.get("validation_experiments"), list):
        raise RuntimeError("The AI returned an invalid experiment plan.")
    result["mode"] = "openai"
    return result


def generate(payload: dict[str, Any]) -> dict[str, Any]:
    mode = clean(payload.get("mode") or "offline", limit=20).lower()
    if mode == "offline":
        return offline_generate(payload)
    if mode == "openai":
        return ai_generate(payload)
    raise ValueError("Mode must be offline or openai.")


def main() -> None:
    parser = argparse.ArgumentParser(description=APP_TITLE)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8002, type=int)
    args = parser.parse_args()
    serve(generate, title=APP_TITLE, base_dir=BASE_DIR, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
