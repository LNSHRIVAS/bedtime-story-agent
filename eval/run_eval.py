import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from storyteller import tell_story


def _quiet_tell(request):
    story, spec, verdict, trace = tell_story(request, quiet=True)
    first_score = trace[0]["verdict"].weighted_score if trace else 0.0
    final_score = verdict.weighted_score
    return verdict, first_score, final_score


def main():
    with open(os.path.join(os.path.dirname(__file__), "cases.json")) as f:
        cases = json.load(f)

    results = []
    for c in cases:
        print(f"  Testing: {c['id']}...")
        verdict, first, final = _quiet_tell(c["request"])
        results.append({**c, "verdict": verdict, "first_score": first, "final_score": final})

    safe_caught = sum(
        1 for r in results if not r["expect_safe"] and r["verdict"].safety_gate != "pass"
    )
    safe_total = sum(1 for r in results if not r["expect_safe"])
    safety_rate = safe_caught / safe_total * 100 if safe_total else 0

    generated = [r for r in results if r["verdict"].safety_gate != "input_blocked"]
    denom = len(generated) or 1
    passed = sum(1 for r in generated if r["verdict"].passed)
    avg_first = sum(r["first_score"] for r in generated) / denom
    avg_final = sum(r["final_score"] for r in generated) / denom
    avg_lift = avg_final - avg_first

    print()
    print("=" * 50)
    print("  Eval Results")
    print("=" * 50)
    print(f"  Safety catch rate:  {safe_caught}/{safe_total} ({safety_rate:.0f}%)")
    print(f"  Stories passed:     {passed}/{len(results)}")
    print(f"  Avg first draft:    {avg_first:.2f}/5.0")
    print(f"  Avg final score:    {avg_final:.2f}/5.0")
    print(f"  Avg revision lift:  +{avg_lift:.2f}")
    print()
    for r in results:
        safe = "BLOCKED" if r["verdict"].safety_gate != "pass" else "OK"
        print(f"  {r['id']:20s}  {safe:8s}  {r['first_score']:.1f}→{r['final_score']:.1f}")


if __name__ == "__main__":
    main()

