import json
import os
import re

from .models import StorySpec


def _load(path: str) -> str:
    with open(os.path.join(os.path.dirname(__file__), "..", path)) as f:
        text = f.read()
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    return text.strip()


def storyteller(spec: StorySpec, feedback: list[str] | None = None) -> str:
    template = _load("prompts/storyteller.md")
    prompt = template.replace("{{spec_json}}", json.dumps(spec.model_dump(), indent=2))
    if feedback:
        prompt += "\n\nPrevious feedback to address:\n" + "\n".join(feedback)
    return prompt


def judge(focus: str, dimension: str, rubric: str, spec: StorySpec, story: str) -> str:
    template = _load("prompts/judge_base.md")
    return (
        template.replace("{{focus}}", focus)
        .replace("{{dimension}}", dimension)
        .replace("{{rubric}}", rubric)
        .replace("{{spec_json}}", json.dumps(spec.model_dump(), indent=2))
        .replace("{{story}}", story)
    )


def intake(request: str) -> str:
    template = _load("prompts/intake.md")
    return template.replace("{{request}}", request)



