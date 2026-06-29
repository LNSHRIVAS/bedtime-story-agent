import sys

from storyteller import AgeBand, tell_story


"""
Before submitting the assignment, describe here in a few sentences what you would have built next if you spent 2 more hours on this project:

- Interactive mode: let the child make one gentle choice mid-story ("should the rabbit go left toward the moon or right toward the fireflies?"), then resolve from their pick.
- TTS + streaming narration: this is a voice product at heart; hooking in a text-to-speech layer with streaming would mirror the actual latency-sensitive voice experience.
- Multi-session memory: remember the child's name, favorite characters, and past story settings across sessions — Hippocratic has published research on exactly this kind of persistent context.
- Judge calibration: run the LLM critics against a small hand-rated set to measure how well the scoring matches human judgment, then tune prompts accordingly.
"""


def main():
    verbose = "--verbose" in sys.argv

    user_input = input("What kind of story do you want to hear? ")
    age_input = input("How old is the child? ").strip()
    try:
        age = int(age_input)
        age_band = AgeBand("5-7") if age <= 7 else AgeBand("8-10")
    except ValueError:
        age_band = AgeBand("5-7")

    print("\nCrafting your story...\n")
    story, spec, verdict, trace = tell_story(user_input, age_band)

    print()
    print("=" * 50)
    print("  THE STORY")
    print("=" * 50)
    print()
    print(story)
    print()
    print("-" * 50)
    if verdict.safety_gate == "pass":
        print(f"  Safe bedtime story for ages {spec.age_band}")
    else:
        print(f"  Story needs review")
    print(f"  Quality score: {verdict.weighted_score:.1f}/5.0  |  {spec.category}  |  {len(trace)} attempt(s)")
    print()

    for dim, score in verdict.per_dimension.items():
        mark = "good" if score >= 3 else "needs work"
        print(f"    {dim}: {score}/5 ({mark})")

    if verdict.revision_feedback:
        print(f"\n  Feedback: {'; '.join(verdict.revision_feedback)}")

    if verbose:
        print()
        print("─" * 50)
        print("  SPEC (debug)")
        print("─" * 50)
        print(spec.model_dump_json(indent=2))


if __name__ == "__main__":
    main()