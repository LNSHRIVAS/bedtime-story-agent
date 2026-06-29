from enum import Enum

from pydantic import BaseModel, Field, model_validator


SAFETY_BASELINE_MUST_AVOID = [
    "violence",
    "death",
    "scary imagery",
    "cliffhangers",
]


class StoryCategory(str, Enum):
    CALMING = "calming"
    ADVENTURE = "adventure"
    FRIENDSHIP = "friendship"
    OVERCOMING_FEAR = "overcoming_fear"
    GENTLE_EDUCATIONAL = "gentle_educational"


class AgeBand(str, Enum):
    AGE_5_7 = "5-7"
    AGE_8_10 = "8-10"


class Tone(str, Enum):
    SOOTHING = "soothing"
    WARM = "warm"
    PLAYFUL = "playful"
    REASSURING = "reassuring"


class EndingStyle(str, Enum):
    CALM_RESOLVED = "calm_resolved"


class StorySpec(BaseModel):
    request: str
    category: StoryCategory = StoryCategory.CALMING
    age_band: AgeBand = AgeBand.AGE_5_7
    tone: Tone = Tone.SOOTHING
    setting: str = "a cozy place at dusk"
    characters: list[str] = Field(default_factory=list)
    theme: str = "friendship and bedtime"
    must_include: list[str] = Field(default_factory=list)
    must_avoid: list[str] = Field(default_factory=lambda: SAFETY_BASELINE_MUST_AVOID.copy())
    target_length_words: int = 350
    ending_style: EndingStyle = EndingStyle.CALM_RESOLVED

    @model_validator(mode="after")
    def ensure_safety_baseline(self) -> "StorySpec":
        for item in SAFETY_BASELINE_MUST_AVOID:
            if item not in self.must_avoid:
                self.must_avoid.append(item)
        return self

    @classmethod
    def from_intake_result(cls, data: dict, request: str, age_band: AgeBand | None = None) -> "StorySpec":
        try:
            category = StoryCategory(data.get("category", "calming"))
        except ValueError:
            category = StoryCategory.CALMING
        try:
            tone = Tone(data.get("tone", "soothing"))
        except ValueError:
            tone = Tone.SOOTHING
        return cls(
            request=request,
            category=category,
            tone=tone,
            age_band=age_band or AgeBand.AGE_5_7,
            setting=data.get("setting", "a cozy place at dusk"),
            characters=data.get("characters", []),
            theme=data.get("theme", "friendship and bedtime"),
            must_include=data.get("must_include", []),
        )

    @classmethod
    def from_request(cls, request: str, age_band: AgeBand | None = None) -> "StorySpec":
        text = request.lower()

        if any(word in text for word in ["scary", "monster", "fear", "wolf"]):
            category = StoryCategory.OVERCOMING_FEAR
            tone = Tone.REASSURING
        elif any(word in text for word in ["friend", "cat", "dog", "buddy"]):
            category = StoryCategory.FRIENDSHIP
            tone = Tone.WARM
        elif any(word in text for word in ["learn", "teach", "moon", "stars", "numbers"]):
            category = StoryCategory.GENTLE_EDUCATIONAL
            tone = Tone.SOOTHING
        elif any(word in text for word in ["adventure", "journey", "quest", "explore"]):
            category = StoryCategory.ADVENTURE
            tone = Tone.PLAYFUL
        else:
            category = StoryCategory.CALMING
            tone = Tone.SOOTHING

        detected_age = None
        import re
        age_match = re.search(r"\b(\d+)[\s-]?(year[\s-]?old|yo)\b", text)
        if age_match:
            age = int(age_match.group(1))
            detected_age = AgeBand.AGE_5_7 if age <= 7 else AgeBand.AGE_8_10

        return cls(
            request=request,
            category=category,
            tone=tone,
            age_band=age_band or detected_age or AgeBand.AGE_5_7,
        )


def build_story_spec(request: str, age_band: AgeBand | None = None) -> StorySpec:
    return StorySpec.from_request(request, age_band)
