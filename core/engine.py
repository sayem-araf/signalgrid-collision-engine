import math
from schemas import ExtractedEvent, BOMConfig, CollisionAnalysis

# Severity rules (editable, not learned):
#   None     : arrives in time even in the worst case
#   Watch    : likely on time (likely gap 0), worst case late
#   Act      : likely gap 1..ACT_MAX weeks
#   Escalate : likely gap above ACT_MAX, or no free line capacity at all
ACT_MAX = 8


class CollisionEngine:
    """Deterministic lead-time collision check. Every output is a closed-form rule."""

    def __init__(self, config: BOMConfig = None):
        self.config = config or BOMConfig()

    @property
    def baseline_lead_time_weeks(self) -> int:
        return self.config.baseline_lead_time_weeks

    def evaluate_collision(self, event: ExtractedEvent) -> CollisionAnalysis:
        c = self.config

        # 1. Demand: MW (proxy) -> relays -> critical parts, with optional stress
        relays = max(0, round(event.mw * c.mw_to_relay_ratio * (1 + c.demand_stress)))
        parts = relays * c.adcs_per_relay

        # 2. Capacity: assembly weeks on the free share of line capacity
        free_cap = max(0, round(c.vaasa_weekly_smt_capacity * (1 - c.committed_capacity_share)))
        capacity_feasible = free_cap > 0 or relays == 0
        # With no free capacity there is no valid assembly schedule. Assembly time is then
        # left out of the need date, and the result is escalated as a capacity problem.
        assembly_weeks = math.ceil(relays / free_cap) if (relays and free_cap) else 0

        # 3. When components must be in the factory
        component_need_week = event.need_week - c.test_delivery_buffer_weeks - assembly_weeks

        # 4. Supply: lead time + supplier delay range + policy delay
        likely = event.delay_weeks
        best = event.delay_best_weeks if event.delay_best_weeks is not None else likely
        worst = event.delay_worst_weeks if event.delay_worst_weeks is not None else likely
        if not 0 <= best <= likely <= worst:
            raise ValueError(f"Supplier delay must satisfy 0 <= best <= likely <= worst, got {best}/{likely}/{worst}")
        if event.mw < 0 or event.policy_delay_weeks < 0:
            raise ValueError("MW and policy delay must not be negative")
        base = c.baseline_lead_time_weeks + event.policy_delay_weeks
        arr_best, arr_likely, arr_worst = base + best, base + likely, base + worst

        # 5. Gaps
        gap = lambda arr: max(0, arr - component_need_week)
        g_best, g_likely, g_worst = gap(arr_best), gap(arr_likely), gap(arr_worst)

        # 6. Mitigation check: does a buffer ordered now arrive in time?
        arrival_if_buffer = base   # assumption: ordering now avoids the supplier allocation delay
        gap_with_buffer = max(0, arrival_if_buffer - component_need_week)

        if not capacity_feasible:
            severity, reason = "Escalate", "No free line capacity"
        elif g_likely > ACT_MAX:
            severity, reason = "Escalate", f"Likely gap above {ACT_MAX} weeks"
        elif g_likely > 0:
            severity, reason = "Act", "Likely arrival after parts are needed"
        elif g_worst > 0:
            severity, reason = "Watch", "Likely on time, worst case late"
        else:
            severity, reason = "None", "On time even in the worst case"

        return CollisionAnalysis(
            project=event.project,
            mw=event.mw,
            relays_needed=relays,
            components_needed=parts,
            need_week=event.need_week,
            unmitigated_arrival_week=arr_likely,
            collision_gap_weeks=g_likely,
            has_collision=g_likely > 0,
            early_warning_weeks_gained=c.erp_detection_week,   # input assumption, not a measured result
            critical_part=event.critical_part,
            market_tightness=event.market_tightness,
            source_citation=event.source,
            component_need_week=component_need_week,
            assembly_weeks=assembly_weeks,
            free_capacity_per_week=free_cap,
            arrival_best_week=arr_best,
            arrival_worst_week=arr_worst,
            gap_best_weeks=g_best,
            gap_worst_weeks=g_worst,
            policy_delay_weeks=event.policy_delay_weeks,
            supply_concentration=event.supply_concentration,
            severity=severity,
            is_new_project=event.is_new_project,
            tender_expected_week=event.tender_expected_week,
            arrival_if_buffer_week=arrival_if_buffer,
            latest_order_week=component_need_week - base,
            gap_with_buffer_weeks=gap_with_buffer,
            buffer_closes_gap=gap_with_buffer == 0,
            capacity_feasible=capacity_feasible,
            severity_reason=reason,
        )


# Backwards-compatible name
CausalCollisionEngine = CollisionEngine
