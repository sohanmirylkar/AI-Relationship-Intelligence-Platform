import pytest

from scripts.evaluate_demo_data import run_evaluation


@pytest.mark.asyncio
async def test_demo_evaluation_runner_scores_core_flows():
    report = await run_evaluation()

    assert report["meeting_extraction"]["cases"]
    assert report["overall"]["meeting_average_score"] >= 0.6
    assert report["crm_preflight"]["warning_count"] >= 1
    assert report["rag"]["hit_rate"] >= 0.5
    assert report["token_optimizer"]["average_reduction"] > 0
