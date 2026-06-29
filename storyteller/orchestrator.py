import json
import yaml

from .aggregator import Verdict, aggregate
from .judges import run_judges_concurrent
from .llm import call_model
from .models import AgeBand, StorySpec
from .prompts import intake as intake_prompt
from .prompts import storyteller as storyteller_prompt



def load_config():
    with open("config.yaml") as f:
        return yaml.safe_load(f)


CONFIG = load_config()
MAX_REVISIONS = CONFIG["max_revisions"]
STORY_TEMP = CONFIG["temperature"]["storyteller"]


def _extract_json(raw: str) -> dict:
    try:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
            cleaned = cleaned.rsplit("```", 1)[0]
        start = cleaned.index("{")
        end = cleaned.rindex("}") + 1
        return json.loads(cleaned[start:end])
    except Exception:
        return {}


def tell_story(request: str, age_band: AgeBand | None = None, quiet=False) -> tuple[str, StorySpec, Verdict, list[dict]]:
    def log(msg):
        if not quiet:
            print(msg)

    log("  >> Making sure this will be a gentle story...")
    raw = call_model(intake_prompt(request), max_tokens=300, temperature=0)
    intake_data = _extract_json(raw)

    if not intake_data.get("safe", False):
        spec = StorySpec.from_request(request, age_band)
        redirect = "I'd love to tell you a story, but let's pick something gentle and calming instead. What do you think?"
        return redirect, spec, Verdict(passed=False, safety_gate="input_blocked", weighted_score=0.0, per_dimension={}, revision_feedback=[]), []

    spec = StorySpec.from_intake_result(intake_data, request, age_band)
    best_story = ""
    best_score = -1.0
    best_verdict = None
    trace = []

    for attempt in range(MAX_REVISIONS + 1):
        feedback = trace[-1]["verdict"].revision_feedback if trace else None
        prompt = storyteller_prompt(spec, feedback)

        log("  >> Once upon a time...")
        story = call_model(prompt, temperature=STORY_TEMP)

        log("  >> The story council is checking everything...")
        results = run_judges_concurrent(story, spec, quiet)

        verdict = aggregate(results, spec)

        trace.append({
            "attempt": attempt,
            "story": story,
            "results": [r.model_dump() for r in results],
            "verdict": verdict,
        })

        safe = verdict.safety_gate == "pass"
        score = verdict.weighted_score if safe else -1.0
        if score > best_score:
            best_story = story
            best_score = score
            best_verdict = verdict

        if verdict.passed:
            log(f"  >> The story is ready! (score: {verdict.weighted_score:.1f}/5.0)")
            break
        elif attempt < MAX_REVISIONS:
            log(f"  >> A little polishing... (score: {verdict.weighted_score:.1f}/5.0)")

    if not trace[-1]["verdict"].passed:
        log(f"  >> Here's the coziest version we found (score: {best_score:.1f}/5.0)")

    return best_story or trace[-1]["story"], spec, best_verdict or trace[-1]["verdict"], trace


