from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ExtractedEvent:
    """One project signal plus the supply and policy context for its critical part.
    All values in the demo are illustrative."""
    project: str
    mw: float
    need_week: int = 22                       # on-site need, weeks from today
    delay_weeks: int = 0                      # likely supplier delay (weeks)
    critical_part: str = "16-bit multichannel ADC"
    market_tightness: str = "Distributor stock declining (illustrative)"
    source: str = "Illustrative source"
    delay_best_weeks: Optional[int] = None    # best-case delay; defaults to likely
    delay_worst_weeks: Optional[int] = None   # worst-case delay; defaults to likely
    policy_delay_weeks: int = 0               # extra weeks from a trade/policy signal
    supply_concentration: str = "Diversified" # Single region / Few regions / Diversified
    is_new_project: bool = True               # new external project (sales lead) vs routine demand
    tender_expected_week: Optional[int] = None  # illustrative estimate, weeks from today


@dataclass
class BOMConfig:
    """Editable planning assumptions. Illustrative until replaced by BOM/ERP exports."""
    mw_to_relay_ratio: float = 0.5            # relays per MW (proxy for bay/feeder count)
    adcs_per_relay: int = 8                   # critical parts per relay
    vaasa_weekly_smt_capacity: int = 140      # relays per week, whole line
    committed_capacity_share: float = 0.85    # share of capacity already committed
    test_delivery_buffer_weeks: int = 3       # test + delivery after assembly
    baseline_lead_time_weeks: int = 14        # normal component lead time
    erp_detection_week: int = 14              # ASSUMPTION: week a delay normally shows in ERP today
    demand_stress: float = 0.0                # 0.3 = demand 30% above permit estimate


@dataclass
class CollisionAnalysis:
    project: str
    mw: float
    relays_needed: int
    components_needed: int
    need_week: int                            # on-site need week
    unmitigated_arrival_week: int             # likely arrival
    collision_gap_weeks: int                  # likely gap
    has_collision: bool
    early_warning_weeks_gained: int           # equals erp_detection_week (assumed), not measured
    critical_part: str
    market_tightness: str
    source_citation: str
    component_need_week: int = 0
    assembly_weeks: int = 0
    free_capacity_per_week: int = 0
    arrival_best_week: int = 0
    arrival_worst_week: int = 0
    gap_best_weeks: int = 0
    gap_worst_weeks: int = 0
    policy_delay_weeks: int = 0
    supply_concentration: str = "Diversified"
    severity: str = "None"                    # None / Watch / Act / Escalate
    is_new_project: bool = True
    tender_expected_week: Optional[int] = None
    arrival_if_buffer_week: int = 0           # buffer ordered now, before allocation tightens
    latest_order_week: int = 0                # last week to order the buffer and still close the gap
    gap_with_buffer_weeks: int = 0            # gap remaining if the buffer is ordered now
    buffer_closes_gap: bool = True            # False: a buffer alone is not enough
    capacity_feasible: bool = True            # False: no free line capacity, no valid schedule
    severity_reason: str = ""


@dataclass
class ActionCard:
    role: str
    urgency: str
    title: str
    details: str
    evidence: str
    decide_by: str
    action_key: str
    assumption: str = ""


@dataclass
class AuditLogEntry:
    owner_role: str
    action: str
    trigger_event: str
    status: str = "Approved, pending execution in SAP by owner"
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
