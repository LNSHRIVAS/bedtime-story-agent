import yaml

from .judges import JudgeResult
from .models import StorySpec


QUALITY_DIMENSIONS = ["age_level", "narrative", "bedtime_tone", "spec_match"]


def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)


CONFIG = load_config()
QUALITY_THRESHOLD = CONFIG["quality_threshold"]
WEIGHTS = CONFIG.get("weights", {})


class Verdict:
    def __init__(
        self,
        passed: bool,
        safety_gate: str,
        weighted_score: float,
        per_dimension: dict[str, int],
        revision_feedback: list[str],
    ):
        self.passed = passed
        self.safety_gate = safety_gate
        self.weighted_score = weighted_score
        self.per_dimension = per_dimension
        self.revision_feedback = revision_feedback


def aggregate(results: list[JudgeResult], spec: StorySpec) -> Verdict:
    scores = {r.dimension: r.score for r in results}
    issues = {r.dimension: r.issues for r in results}
    suggestions = {r.dimension: r.suggestions for r in results}

    safety_result = next((r for r in results if r.dimension == "safety"), None)
    safety_gate = "fail" if (safety_result is None or not safety_result.passed) else "pass"
    safety_failed = safety_gate == "fail"

    quality_scores = [scores.get(d, 1) for d in QUALITY_DIMENSIONS]
    total_w = sum(WEIGHTS.get(d, 1.0) for d in QUALITY_DIMENSIONS) or 1.0
    weighted_score = sum(scores.get(d, 1) * WEIGHTS.get(d, 1.0) for d in QUALITY_DIMENSIONS) / total_w
    passed = not safety_failed and weighted_score >= QUALITY_THRESHOLD

    feedback = []
    if safety_failed:
        for issue in issues.get("safety", []):
            feedback.append(f"Safety: {issue}")
        for s in suggestions.get("safety", []):
            feedback.append(f"Safety suggestion: {s}")
            
    for dim in QUALITY_DIMENSIONS:
        score = scores.get(dim, 1)
        if score < QUALITY_THRESHOLD:
            for issue in issues.get(dim, []):
                feedback.append(f"{dim}: {issue}")
            for s in suggestions.get(dim, []):
                feedback.append(f"{dim} suggestion: {s}")

    return Verdict(
        passed=passed,
        safety_gate=safety_gate,
        weighted_score=weighted_score,
        per_dimension=scores,
        revision_feedback=feedback,
    )

