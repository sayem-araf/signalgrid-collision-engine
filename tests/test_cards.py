"""Decision cards must never contradict the engine."""
import itertools

import pytest

from agents.orchestrator import PrescriptiveOrchestratorAgent
from core.engine import CollisionEngine
from scenarios import SCENARIOS
from schemas import BOMConfig, ExtractedEvent

ORCH = PrescriptiveOrchestratorAgent()


def analyse(event, **cfg):
    a = CollisionEngine(BOMConfig(**cfg)).evaluate_collision(ExtractedEvent(**event))
    return a, ORCH.generate_action_cards(a, weekly_capacity=BOMConfig(**cfg).vaasa_weekly_smt_capacity)


def text(cards):
    return " ".join(f"{c.title} {c.details} {c.evidence}" for c in cards).lower()


def grid():
    """Sweep scenarios against delays, policy, stress and capacity commitment."""
    for (name, sc), delay, policy, stress, committed in itertools.product(
            SCENARIOS.items(), [0, 3, 6, 7, 10, 14, 20], [0, 2, 4], [0.0, 0.3, 0.5], [0.5, 0.85, 1.0]):
        ev = dict(sc["event"], delay_weeks=delay, delay_best_weeks=max(0, delay - 3),
                  delay_worst_weeks=delay + 4, policy_delay_weeks=policy)
        yield name, ev, dict(demand_stress=stress, committed_capacity_share=committed)


CASES = list(grid())


@pytest.mark.parametrize("name,ev,cfg", CASES)
def test_cards_consistent_with_engine(name, ev, cfg):
    a, cards = analyse(ev, **cfg)
    t = text(cards)
    titles = [c.title for c in cards]

    if a.collision_gap_weeks > 0:
        assert "no action needed" not in t
    if "standard lead time" in t:
        assert a.buffer_closes_gap and a.capacity_feasible
        assert "quote standard lead time" in t and "if the buffer is approved" in t
    if a.severity in ("Act", "Escalate"):
        buffer = next(c for c in cards if c.title == "Secure component buffer")
        assert ("does not close it" in buffer.details) == (not a.buffer_closes_gap)
    if not a.capacity_feasible:
        assert "Release line capacity" in titles
        assert "Re-sequence assembly start" not in titles
        assert "do not commit a delivery date" in t
    if a.severity == "Watch":
        assert titles[-1] == "Confirm supplier dates"
    if a.severity == "None":
        assert all(c.urgency == "Opportunity" for c in cards)
    if a.collision_gap_weeks > 8:
        assert "Escalate and start alternate-source qualification" in titles


def test_grid_covers_every_state():
    states = set()
    for _, ev, cfg in CASES:
        a, _ = analyse(ev, **cfg)
        states.add((a.severity, a.buffer_closes_gap, a.capacity_feasible))
    for needed in [("None", True, True), ("Watch", True, True), ("Act", True, True),
                   ("Act", False, True), ("Escalate", True, True), ("Escalate", False, True),
                   ("Escalate", True, False)]:
        assert needed in states, needed


def test_scenario_card_counts():
    counts = [len(analyse(sc["event"])[1]) for sc in SCENARIOS.values()]
    assert counts == [4, 5, 0]
