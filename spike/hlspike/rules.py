"""SPIKE_PLAN §5 rule 6 and the §6 demo plan, written as code BEFORE any results.

The thresholds are copied from the approved plan. Changing them after seeing
results would defeat the point of fixing them in advance.
"""

LIVE_MEDIAN_SEGMENT_S = 20      # 6a: median per-segment IndicF5 time
LIVE_SCENE_OF_3_S = 60          # 6a: a 3-segment scene
LIVE_PEAK_RAM_FRACTION = 0.70   # 6a: peak RAM vs the Docker memory limit
OVERNIGHT_MAX_HOURS = 8         # 6b: whole demo project's cloned segments


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
