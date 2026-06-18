"""Evaluate the synthetic IRIP demo data from a direct script invocation."""

# ruff: noqa: E402

import argparse
import asyncio
import csv
import json
import sys
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.models.schemas import (
    CrmPreflightRequest,
    MeetingExtractRequest,
    PromptOptimizeRequest,
    RagQueryRequest,
)
from backend.app.services.crm import preflight
from backend.app.services.ingestion import chunk_text
from backend.app.services.meeting_intelligence import extract_meeting
from backend.app.services.rag import answer_query
from backend.app.services.storage import store
from backend.app.services.token_optimizer import optimize_prompt

DEMO_DATA = ROOT / "demo_data"


async def run_evaluation() -> dict[str, Any]:
    report = {
        "meeting_extraction": await evaluate_meetings(),
        "crm_preflight": evaluate_crm_seed(),
        "rag": evaluate_rag(),
        "token_optimizer": evaluate_prompt_tests(),
    }
    report["overall"] = {
        "meeting_average_score": _avg(
            case["score"] for case in report["meeting_extraction"]["cases"]
        ),
        "crm_required_field_pass_rate": report["crm_preflight"]["required_field_pass_rate"],
        "rag_hit_rate": report["rag"]["hit_rate"],
        "prompt_average_reduction": report["token_optimizer"]["average_reduction"],
    }
    return report


async def evaluate_meetings() -> dict[str, Any]:
    cases = []
    transcript_dir = DEMO_DATA / "meeting_transcripts"
    expected_dir = DEMO_DATA / "expected_outputs"
    for transcript_path in sorted(transcript_dir.glob("*.txt")):
        expected = json.loads((expected_dir / f"{transcript_path.stem}.json").read_text())
        transcript = transcript_path.read_text(encoding="utf-8")
        response = await extract_meeting(
            MeetingExtractRequest(
                transcript_text=transcript,
                company_hint=expected["company"],
                interaction_date=expected.get("required_crm_fields", {}).get("MeetingDate"),
            )
        )
        company_score = _contains_score(
            response.crm_payload.get("CompanyName", ""), expected["company"]
        )
        person_score = _list_recall(
            [person.get("full_name", "") for person in response.extracted_entities["people"]],
            expected["people"],
        )
        action_score = _list_recall(
            [item.get("description", "") for item in response.action_items],
            expected["action_items"],
        )
        crm_score = _field_score(response.crm_payload, expected["required_crm_fields"])
        score = round(mean([company_score, person_score, action_score, crm_score]), 3)
        cases.append(
            {
                "case_id": transcript_path.stem,
                "score": score,
                "company_score": company_score,
                "person_recall": person_score,
                "action_recall": action_score,
                "crm_required_field_score": crm_score,
                "crm_payload": response.crm_payload,
                "confidence": response.confidence,
            }
        )
    return {"cases": cases}


def evaluate_crm_seed() -> dict[str, Any]:
    rows = list(csv.DictReader((DEMO_DATA / "crm_seed.csv").open(encoding="utf-8")))
    review = preflight(CrmPreflightRequest(target_object="Interaction", records=rows))
    required_fields = review.required_field_status
    pass_rate = sum(1 for value in required_fields.values() if value == "ok") / len(
        required_fields
    )
    return {
        "valid": review.valid,
        "required_field_status": required_fields,
        "required_field_pass_rate": round(pass_rate, 3),
        "warning_count": len(review.warnings),
        "warnings": review.warnings,
        "recommended_action": review.recommended_action,
    }


def evaluate_rag() -> dict[str, Any]:
    seed_research_docs()
    queries = [
        {
            "query": "Northstar residential mortgage finance collateral reporting",
            "expected_doc": "northstar_public_pension_notes.md",
        },
        {
            "query": "HarborView servicing quality Midwest insurance introduction",
            "expected_doc": "harborview_consultants_notes.md",
        },
    ]
    cases = []
    hits = 0
    for query in queries:
        result = answer_query(RagQueryRequest(query=query["query"], top_k=3))
        cited_docs = [citation.get("doc_title") for citation in result.citations]
        hit = query["expected_doc"] in cited_docs
        hits += int(hit)
        cases.append(
            {
                "query": query["query"],
                "expected_doc": query["expected_doc"],
                "hit": hit,
                "citations": result.citations,
            }
        )
    return {"hit_rate": round(hits / len(queries), 3), "cases": cases}


def evaluate_prompt_tests() -> dict[str, Any]:
    rows = list(csv.DictReader((DEMO_DATA / "prompt_tests.csv").open(encoding="utf-8")))
    cases = []
    reductions = []
    for row in rows:
        result = optimize_prompt(
            PromptOptimizeRequest(
                prompt=row["original_prompt"],
                model="claude-sonnet-4-6",
                expected_output_tokens=1000,
                monthly_runs=100,
            )
        )
        reduction = max(0.0, 1 - (result.optimized.input_tokens / result.original.input_tokens))
        reductions.append(reduction)
        cases.append(
            {
                "id": row["id"],
                "module": row["module"],
                "reduction": round(reduction, 3),
                "expected_min_reduction": float(row["expected_min_reduction"]),
                "passes": reduction >= float(row["expected_min_reduction"]),
                "monthly_savings_usd": result.estimated_savings_usd,
            }
        )
    return {"average_reduction": round(_avg(reductions), 3), "cases": cases}


def seed_research_docs() -> None:
    state = store.read()
    existing_titles = {
        chunk.get("metadata", {}).get("doc_title") for chunk in state.get("chunks", [])
    }
    for path in sorted((DEMO_DATA / "research_docs").glob("*.md")):
        if path.name in existing_titles:
            continue
        document_id = f"demo_doc_{path.stem}"
        for index, content in enumerate(chunk_text(path.read_text(encoding="utf-8"))):
            state.setdefault("chunks", []).append(
                {
                    "id": f"{document_id}_chunk_{index}",
                    "document_id": document_id,
                    "chunk_index": index,
                    "content": content,
                    "metadata": {
                        "doc_title": path.name,
                        "source_type": "analyst_note",
                        "security_scope": "internal_demo",
                    },
                }
            )
    store.write(state)


def _contains_score(actual: str, expected: str) -> float:
    actual_norm = _norm(actual)
    expected_norm = _norm(expected)
    return 1.0 if expected_norm in actual_norm or actual_norm in expected_norm else 0.0


def _list_recall(actual_items: list[str], expected_items: list[str]) -> float:
    if not expected_items:
        return 1.0
    hits = 0
    actual_joined = " ".join(_norm(item) for item in actual_items)
    for expected in expected_items:
        expected_terms = [term for term in _norm(expected).split() if len(term) > 2]
        if expected_terms and sum(term in actual_joined for term in expected_terms) >= max(
            1, len(expected_terms) // 2
        ):
            hits += 1
    return round(hits / len(expected_items), 3)


def _field_score(actual: dict[str, Any], expected_fields: dict[str, str]) -> float:
    if not expected_fields:
        return 1.0
    hits = 0
    for key, expected in expected_fields.items():
        if expected and _norm(str(expected)) in _norm(str(actual.get(key, ""))):
            hits += 1
    return round(hits / len(expected_fields), 3)


def _norm(value: str) -> str:
    return " ".join(value.lower().replace("-", " ").replace("_", " ").split())


def _avg(values) -> float:
    values = list(values)
    return round(mean(values), 3) if values else 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate IRIP demo data.")
    parser.add_argument("--output", default="reports/demo_eval_report.json")
    args = parser.parse_args()
    report = asyncio.run(run_evaluation())
    output_path = ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["overall"], indent=2))
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
