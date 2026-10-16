import json
import os
import sys
from dataclasses import is_dataclass, asdict

# Ensure backend root directory is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schemas import ExtractedEvent, BOMConfig
from core.engine import CollisionEngine
from agents.orchestrator import PrescriptiveOrchestratorAgent

FALLBACK_SCENARIO_A = {
    "project": "Hyperscale data center, Phase 1 (illustrative)",
    "mw": 60.0,
    "need_week": 26,
    "delay_weeks": 12,
    "delay_best_weeks": 8,
    "delay_worst_weeks": 16,
    "policy_delay_weeks": 2,
    "critical_part": "16-bit multichannel ADC",
    "market_tightness": "Distributor stock declining (illustrative)",
    "source": "Municipal planning notice + OSAT bulletin + trade notice (illustrative)",
    "supply_concentration": "Single region"
}

def load_scenario():
    fixtures_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
    fixture_path = os.path.join(fixtures_dir, "scenario_a.json")
    
    if os.path.exists(fixture_path):
        with open(fixture_path, "r") as f:
            return json.load(f)
    else:
        try:
            os.makedirs(fixtures_dir, exist_ok=True)
            with open(fixture_path, "w") as f:
                json.dump(FALLBACK_SCENARIO_A, f, indent=2)
            print("[INFO] Auto-generated missing fixtures/scenario_a.json")
        except Exception:
            pass
        return FALLBACK_SCENARIO_A

def serialize_entry(entry):
    """Safely serializes Pydantic models, custom dataclasses, or plain objects."""
    if hasattr(entry, "to_dict"):
        return entry.to_dict()
    elif hasattr(entry, "model_dump"):
        return entry.model_dump()
    elif hasattr(entry, "dict"):
        return entry.dict()
    elif is_dataclass(entry):
        return asdict(entry)
    elif hasattr(entry, "__dict__"):
        return vars(entry)
    return str(entry)

def run():
    print("=" * 70)
    print("  SIGNALGRID DETERMINISTIC BACKEND PIPELINE VERIFICATION")
    print("  Protection relay planning (illustrative data)")
    print("=" * 70)

    # 1. Load Fixture
    data = load_scenario()
    event = ExtractedEvent(**data)
    print(f"\n[1. Structured Event Ingested]:")
    print(f"   Project:        {event.project}")
    print(f"   Substation MW:  {event.mw} MW")
    print(f"   Target Week:    Week {event.need_week}")
    print(f"   Supplier Delay: +{event.delay_weeks} Weeks on {event.critical_part}")

    # 2. Run Deterministic Engine
    config = BOMConfig()  # illustrative defaults, see schemas.py
    engine = CollisionEngine(config)
    analysis = engine.evaluate_collision(event)

    print(f"\n[2. Deterministic BOM & Collision Evaluation]:")
    print(f"   Relays Required:     {analysis.relays_needed} Units")
    print(f"   Critical Components: {analysis.components_needed} x {analysis.critical_part}")
    print(f"   Parts Needed By:     Week +{analysis.component_need_week} ({analysis.assembly_weeks} assembly wk + {config.test_delivery_buffer_weeks} test/delivery wk before site)")
    print(f"   Unmitigated Arrival: Week {analysis.unmitigated_arrival_week}")
    print(f"   Collision Gap:       {analysis.collision_gap_weeks} weeks likely (range {analysis.gap_best_weeks}-{analysis.gap_worst_weeks})")
    print(f"   Severity:            {analysis.severity}")
    if not analysis.capacity_feasible:
        print("   Time Left to Act:    Blocked (no free line capacity)")
    elif not analysis.buffer_closes_gap:
        print(f"   Time Left to Act:    Too late for buffer (still {analysis.gap_with_buffer_weeks} wk late)")
    else:
        print(f"   Time Left to Act:    {max(0, analysis.latest_order_week)} weeks")
    print(f"   Has Collision:       {analysis.has_collision}")

    # 3. Generate Prescriptive Action Cards
    orchestrator = PrescriptiveOrchestratorAgent()
    cards = orchestrator.generate_action_cards(analysis)

    print(f"\n[3. Generated Prescriptive Action Cards]:")
    for i, card in enumerate(cards, 1):
        print(f"   Card {i} [{card.role} | {card.urgency}]: {card.title}")
        print(f"          Directive: {card.details}")
        print(f"          Decide By: {card.decide_by}\n")

    # 4. Human-in-the-Loop Sign-Off
    print("[4. Human-in-the-Loop Sign-off]:")
    audit_entry = orchestrator.sign_off_action(cards[0], event.project)
    print(f"   Audit Log Appended: {serialize_entry(audit_entry)}")
    print("\nAll quantities and dates computed by deterministic rules.\n")

if __name__ == "__main__":
    run()
