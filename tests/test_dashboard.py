"""Smoke test the Streamlit dashboard and check the KPI row agrees with the engine."""
import os

import pytest

st_testing = pytest.importorskip("streamlit.testing.v1")
from core.engine import CollisionEngine  # noqa: E402
from scenarios import SCENARIOS  # noqa: E402
from schemas import BOMConfig, ExtractedEvent  # noqa: E402

APP = os.path.join(os.path.dirname(__file__), "..", "app.py")
LABELS = list(SCENARIOS)


def render(scenario=0, stress=0, committed=None):
    at = st_testing.AppTest.from_file(APP, default_timeout=30).run()
    if scenario:
        picker = at.button_group[0] if len(at.button_group) else at.radio[0]
        picker.set_value(LABELS[scenario]).run()
    sliders = {s.label: s for s in at.slider}
    if stress:
        sliders["Demand stress test: demand above permit estimate (%)"].set_value(stress).run()
    if committed is not None:
        {s.label: s for s in at.slider}["Capacity already committed (%)"].set_value(committed).run()
    assert not at.exception, at.exception
    return at, " ".join(m.value for m in at.markdown)


@pytest.mark.parametrize("scenario", [0, 1, 2])
@pytest.mark.parametrize("stress", [0, 50])
def test_kpi_matches_engine(scenario, stress):
    at, html = render(scenario, stress)
    a = CollisionEngine(BOMConfig(demand_stress=stress / 100)).evaluate_collision(
        ExtractedEvent(**SCENARIOS[LABELS[scenario]]["event"]))
    if a.severity == "None":
        assert ">None<" in html
    else:
        assert f">{a.collision_gap_weeks} weeks<" in html
    if a.collision_gap_weeks > 0:
        assert "No action needed" not in html


def test_zero_capacity_renders_escalation():
    at, html = render(0, 0, committed=100)
    assert "No free line capacity" in html
    assert "Release line capacity" in html
    assert "Re-sequence assembly start" not in html
