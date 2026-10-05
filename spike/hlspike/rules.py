"""SPIKE_PLAN §5 rules 3 and 6 and the §6 demo plan, written as code BEFORE any results.

The thresholds are copied from the approved plan. Changing them after seeing
results would defeat the point of fixing them in advance.
"""

LIVE_MEDIAN_SEGMENT_S = 20      # 6a: median per-segment IndicF5 time
LIVE_SCENE_OF_3_S = 60          # 6a: a 3-segment scene
LIVE_PEAK_RAM_FRACTION = 0.70   # 6a: peak RAM vs the Docker memory limit
OVERNIGHT_MAX_HOURS = 8         # 6b: whole demo project's cloned segments
TRANSLATION_TIE_POINTS = 5      # 3: MQM points per 100 source words (about one major error)


def rule3(points: dict[str, float], trains_on_data: dict[str, bool],
          hard_check_pass_rate: dict[str, float]) -> dict:
    """Translation choice (ADR 0016) from the AGREED MQM labels.

    Every system within TRANSLATION_TIE_POINTS of the best score ties with it.
    Ties are broken by data terms (no training on our data preferred), then by
    hard-check pass rate. If a tie survives both, nobody is chosen: escalate.
    """
    best = min(points.values())
    remaining = sorted(s for s, p in points.items() if p - best <= TRANSLATION_TIE_POINTS)
    result = {"tied_on_mqm": remaining, "winner": None, "decided_by": None}
    if len(remaining) == 1:
        return result | {"winner": remaining[0], "decided_by": "mqm_points"}

    no_training = [s for s in remaining if not trains_on_data[s]]
    if no_training:
        remaining = no_training
    if len(remaining) == 1:
        return result | {"winner": remaining[0], "decided_by": "data_terms"}

    top = max(hard_check_pass_rate[s] for s in remaining)
    remaining = [s for s in remaining if hard_check_pass_rate[s] == top]
    if len(remaining) == 1:
        return result | {"winner": remaining[0], "decided_by": "hard_check_pass_rate"}
    return result | {"decided_by": "unresolved_tie_escalate", "still_tied": remaining}


def rule6(median_segment_s: float, scene_of_3_s: float, peak_ram_mb: float,
          docker_limit_mb: float, overnight_hours: float, kaggle_available: bool) -> dict:
    live = (median_segment_s <= LIVE_MEDIAN_SEGMENT_S
            and scene_of_3_s <= LIVE_SCENE_OF_3_S
            and peak_ram_mb <= LIVE_PEAK_RAM_FRACTION * docker_limit_mb)
    overnight = overnight_hours <= OVERNIGHT_MAX_HOURS
    if live:
        plan = "A"   # everything live on the laptop
    elif overnight:
        plan = "C"   # cloned previews rendered overnight on CPU; no Kaggle
    elif kaggle_available:
        plan = "B"   # cloned previews pre-rendered on Kaggle
    else:
        plan = "D"   # cloned voice only for the short revocation scene
    return {
        "6a_cpu_live_capable": live,
        "6b_overnight_sufficient": overnight,
        "adopt_kaggle": not live and not overnight,
        "demo_plan": plan,
    }
