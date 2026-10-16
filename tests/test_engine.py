"""Engine rules: scenario acceptance values and the edge cases found in review."""
import pytest

from core.engine import ACT_MAX, CollisionEngine
from scenarios import SCENARIOS
from schemas import BOMConfig, ExtractedEvent

A, B, C = (SCENARIOS[k]["event"] for k in SCENARIOS)


def run(event, **cfg):
    return CollisionEngine(BOMConfig(**cfg)).evaluate_collision(ExtractedEvent(**event))


# Values shared with the Lovable acceptance tests (LOVABLE_PROMPT.md)
@pytest.mark.parametrize("event,stress,relays,parts,assembly,need,gaps,severity,order_by", [
    (A, 0.0, 30, 240, 2, 21, (3, 7, 11), "Act", 5),
    (A, 0.5, 45, 360, 3, 20, (4, 8, 12), "Act", 4),
    (B, 0.0, 90, 720, 5, 16, (8, 12, 16), "Escalate", 2),
    (B, 0.5, 135, 1080, 7, 14, (10, 14, 18), "Escalate", 0),
    (C, 0.0, 10, 80, 1, 30, (0, 0, 0), "None", 16),
])
def test_scenario_acceptance(event, stress, relays, parts, assembly, need, gaps, severity, order_by):
    a = run(event, demand_stress=stress)
    assert (a.relays_needed, a.components_needed, a.assembly_weeks) == (relays, parts, assembly)
    assert a.component_need_week == need
    assert (a.gap_best_weeks, a.collision_gap_weeks, a.gap_worst_weeks) == gaps
    assert a.severity == severity
    assert a.latest_order_week == order_by


# Scenario A needs parts by week 21 and the base lead time is 16 weeks,
# so the likely gap equals (likely delay - 5).
def a_with_delay(likely, worst_extra=4):
    return dict(A, delay_weeks=likely, delay_best_weeks=max(0, likely - 2),
                delay_worst_weeks=likely + worst_extra)


@pytest.mark.parametrize("likely_delay,gap,severity", [
    (4, 0, "Watch"),       # worst case late, likely on time
    (5, 0, "Watch"),       # arrives exactly in the need week
    (6, 1, "Act"),         # review finding: previously shown as Watch / 0 weeks
    (7, 2, "Act"),         # review finding: previously shown as Watch / 0 weeks
    (8, 3, "Act"),
    (5 + ACT_MAX, ACT_MAX, "Act"),
    (6 + ACT_MAX, ACT_MAX + 1, "Escalate"),
])
def test_severity_boundaries(likely_delay, gap, severity):
    a = run(a_with_delay(likely_delay))
    assert a.collision_gap_weeks == gap
    assert a.severity == severity


def test_none_when_worst_case_on_time():
    a = run(a_with_delay(0, worst_extra=0))
    assert a.gap_worst_weeks == 0 and a.severity == "None"


def test_any_positive_likely_gap_requires_action():
    for d in range(0, 30):
        a = run(a_with_delay(d))
        if a.collision_gap_weeks > 0:
            assert a.severity in ("Act", "Escalate"), d
        if a.severity == "Watch":
            assert a.collision_gap_weeks == 0, d


@pytest.mark.parametrize("committed", [1.0, 0.999])
def test_zero_free_capacity_is_not_a_schedule(committed):
    a = run(A, committed_capacity_share=committed)
    assert a.free_capacity_per_week == 0
    assert a.capacity_feasible is False
    assert a.severity == "Escalate"
    assert a.severity_reason == "No free line capacity"


def test_small_free_capacity_still_schedules():
    a = run(A, vaasa_weekly_smt_capacity=100, committed_capacity_share=0.98)  # 2 relays per week
    assert a.capacity_feasible and a.free_capacity_per_week == 2
    assert a.assembly_weeks == 15


def test_buffer_too_late_is_flagged():
    # Policy delay pushes the buffer arrival (lead time + policy) past the need week
    ev = dict(B, policy_delay_weeks=2)
    a = run(ev, demand_stress=0.5)
    assert a.arrival_if_buffer_week == 16 and a.component_need_week == 14
    assert a.buffer_closes_gap is False
    assert a.gap_with_buffer_weeks == 2
    assert a.latest_order_week < 0


def test_buffer_exactly_in_time_closes_gap():
    a = run(B, demand_stress=0.5)   # buffer arrives week 14, needed week 14
    assert a.buffer_closes_gap and a.gap_with_buffer_weeks == 0 and a.latest_order_week == 0


def test_erp_week_is_passed_through_as_assumption():
    for w in (6, 14, 24):
        assert run(A, erp_detection_week=w).early_warning_weeks_gained == w


@pytest.mark.parametrize("best,likely,worst", [(8, 6, 10), (2, 6, 5), (-1, 0, 2)])
def test_inconsistent_delay_range_is_rejected(best, likely, worst):
    with pytest.raises(ValueError):
        run(dict(A, delay_best_weeks=best, delay_weeks=likely, delay_worst_weeks=worst))


def test_negative_inputs_are_rejected():
    with pytest.raises(ValueError):
        run(dict(A, mw=-5))
