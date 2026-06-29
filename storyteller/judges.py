import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from pydantic import BaseModel, Field

from .llm import call_model
from .models import StorySpec
from .prompts import judge as judge_prompt


class JudgeResult(BaseModel):
    dimension: str
    score: int
    passed: bool
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class BaseJudge:
    dimension = ""
    focus = ""
    rubric = ""
    fallback_issue = "judge output was not valid JSON"
    fallback_suggestion = "review the story manually"

    def judge(self, story: str, spec: StorySpec) -> JudgeResult:
        prompt = judge_prompt(self.focus, self.dimension, self.rubric, spec, story)
        raw = call_model(prompt, max_tokens=500, temperature=0)
        return self._parse_result(raw)

    def _parse_result(self, raw: str) -> JudgeResult:
        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1]
                cleaned = cleaned.rsplit("```", 1)[0]
            start = cleaned.index("{")
            end = cleaned.rindex("}") + 1
            data = json.loads(cleaned[start:end])
            return JudgeResult(**data)
        except Exception:
            return JudgeResult(
                dimension=self.dimension,
                score=1,
                passed=False,
                issues=[self.fallback_issue],
                suggestions=[self.fallback_suggestion],
            )


class SafetyJudge(BaseJudge):
    dimension = "safety"
    focus = "strict safety"
    fallback_suggestion = "review the story for safety manually"
    rubric = "Check for: violence, death, scary imagery, cliffhangers, nightmares, adult themes.\nA safe story passes (score >= 3). Any safety issue = fail (score 1-2)."


class AgeLevelJudge(BaseJudge):
    dimension = "age_level"
    focus = "child age-level"
    fallback_suggestion = "simplify the vocabulary and sentence structure"
    rubric = "Age-appropriate for 5-10 year olds:\n- 5 = simple words, short sentences, easy to follow\n- 4 = mostly simple, one or two slightly advanced words\n- 3 = readable, some complex sentences but still understandable\n- 2 = too many big words or long sentences for the age group\n- 1 = completely inappropriate vocabulary or complexity"


class NarrativeJudge(BaseJudge):
    dimension = "narrative"
    focus = "story structure"
    fallback_suggestion = "add a clearer beginning, middle, and ending"
    rubric = "Story has a complete arc:\n- 5 = clear beginning, middle, end with a satisfying resolution\n- 4 = good structure, slightly weak in one area\n- 3 = has a beginning, middle, and end, but one part is thin\n- 2 = missing or confusing parts of the arc\n- 1 = no clear structure, feels random"


class BedtimeToneJudge(BaseJudge):
    dimension = "bedtime_tone"
    focus = "bedtime tone"
    fallback_suggestion = "make the story calmer and more soothing"
    rubric = "Suitable for bedtime:\n- 5 = very calming, soothing rhythm, peaceful ending that helps wind down\n- 4 = generally calm, mild excitement that resolves peacefully\n- 3 = neutral tone, not too exciting nor too calming\n- 2 = too exciting or tense for bedtime\n- 1 = scary, anxious, or stimulating"


class SpecMatchJudge(BaseJudge):
    dimension = "spec_match"
    focus = "spec matching"
    fallback_suggestion = "align the story more closely with the request"
    rubric = "Matches the requested spec:\n- 5 = includes all requested characters/setting/theme/tone perfectly\n- 4 = includes most elements, minor omissions\n- 3 = includes main elements but misses some details\n- 2 = includes some elements but misses key ones\n- 1 = does not match the request at all"


DEFAULT_JUDGES = [
    SafetyJudge(),
    AgeLevelJudge(),
    NarrativeJudge(),
    BedtimeToneJudge(),
    SpecMatchJudge(),
]

JUDGE_ORDER = ["safety", "age_level", "narrative", "bedtime_tone", "spec_match"]

JUDGE_NAMES = {
    "safety": "  > Safety",
    "age_level": "  > Age",
    "narrative": "  > Story",
    "bedtime_tone": "  > Tone",
    "spec_match": "  > Wish",
}


def run_judges(story: str, spec: StorySpec) -> list[JudgeResult]:
    return [judge.judge(story, spec) for judge in DEFAULT_JUDGES]


def run_judges_concurrent(story: str, spec: StorySpec, quiet=False) -> list[JudgeResult]:
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(j.judge, story, spec): j for j in DEFAULT_JUDGES}
        results = []
        for future in as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda r: JUDGE_ORDER.index(r.dimension) if r.dimension in JUDGE_ORDER else 99)
    if not quiet:
        for r in results:
            name = JUDGE_NAMES.get(r.dimension, r.dimension)
            mark = "good" if r.passed else "fix"
            print(f"  {name} {mark} ({r.score}/5)")
    return results

