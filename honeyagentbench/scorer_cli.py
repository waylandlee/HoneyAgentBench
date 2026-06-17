# CLI-visible Inspect scorer for saved log rescoring.

from inspect_ai.scorer import Score, Scorer, scorer

from honeyagentbench.scorers import _build_honey_deception_score_fn


@scorer(metrics=[])
def honey_deception_scorer_cli() -> Scorer:
    return _build_honey_deception_score_fn(Score)
