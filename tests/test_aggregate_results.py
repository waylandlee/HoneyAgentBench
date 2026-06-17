from scripts.aggregate_results import extract_metrics


def test_extract_metrics_accepts_cli_scorer_metadata():
    record = {
        "scores": {
            "honey_deception_scorer_cli": {
                "metadata": {
                    "task_success": True,
                    "enterprise_v3_strict_success": True,
                    "distractor_action_count": 2,
                    "evidence_precision": 0.8889,
                }
            }
        }
    }

    metrics = extract_metrics(record)

    assert metrics["task_success"] is True
    assert metrics["enterprise_v3_strict_success"] is True
    assert metrics["distractor_action_count"] == 2
    assert metrics["evidence_precision"] == 0.8889


def test_extract_metrics_accepts_legacy_scorer_metadata():
    record = {
        "score": {
            "_scorer": {
                "metadata": {
                    "task_success": False,
                    "enterprise_v3_strict_success": False,
                }
            }
        }
    }

    metrics = extract_metrics(record)

    assert metrics["task_success"] is False
    assert metrics["enterprise_v3_strict_success"] is False