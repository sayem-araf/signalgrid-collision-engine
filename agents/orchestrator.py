from typing import List, Optional
from datetime import datetime, timedelta
from schemas import CollisionAnalysis, ActionCard, AuditLogEntry
from core.engine import ACT_MAX as ACT_MAX_WEEKS


def _date_in(days: int) -> str:
    return (datetime.now() + timedelta(days=days)).strftime("%d %b %Y")


def _short(part: str) -> str:
    return part.split("(")[0].strip()


class PrescriptiveOrchestratorAgent:
    """Rule-based recommendations, scaled to severity. A person approves every action."""

    def generate_action_cards(
        self, a: CollisionAnalysis, weekly_capacity: Optional[int] = None
    ) -> List[ActionCard]:
        slug = a.project.lower().replace(" ", "_")
        part = _short(a.critical_part)
        rng = f"{a.gap_best_weeks}–{a.gap_worst_weeks} weeks (likely {a.collision_gap_weeks})"
        cards: List[ActionCard] = []

        # Sales: every new external project is also a sales lead, collision or not
        if a.is_new_project:
            tender = (f"Tender expected around week +{a.tender_expected_week} (estimate). "
                      if a.tender_expected_week is not None else "")
            supply_note = ("Supply risk is flagged below, so coordinate the delivery promise with sourcing."
                           if a.severity in ("Act", "Escalate") else
                           "No supply risk detected, so a standard delivery promise is safe.")
            cards.append(ActionCard(
                role="Account Manager",
                urgency="Opportunity",
                title="Early sales engagement",
                details=f"{tender}Contact the developer or EPC contractor now, while the specification is "
                        f"still open. Estimated scope: about {a.relays_needed} protection relays.",
                evidence=f"Signal detected before any tender or order. {supply_note}",
                assumption="Scope = MW × relays per MW (estimate until bay count is known).",
                decide_by=_date_in(7),
                action_key=f"sales_lead_{slug}",
            ))

        if a.severity == "None":
            return cards

        # Watch tier: no collision in the likely case, but the worst case collides
        if a.severity == "Watch":
            cards.append(ActionCard(
                role="Sourcing Lead",
                urgency="Watch",
                title="Confirm supplier dates",
                details=f"Ask the supplier to confirm delivery dates for {part}. "
                        f"No action needed yet in the likely case.",
                evidence=f"Worst case arrives week +{a.arrival_worst_week}; parts needed by week +{a.component_need_week}.",
                assumption="Worst case = baseline lead time + worst-case supplier delay.",
                decide_by=_date_in(7),
                action_key=f"confirm_{slug}",
            ))
            return cards

        # Act tier (and base of Escalate)
        policy_note = f" Includes +{a.policy_delay_weeks} wk from a trade signal." if a.policy_delay_weeks else ""
        if a.buffer_closes_gap:
            order_by = ("this week" if a.latest_order_week <= 0 else f"by week +{a.latest_order_week}")
            buffer_details = (f"Place a buffer order for {a.components_needed} units of {part} {order_by}, "
                              f"before supplier allocation tightens. This closes the likely gap.")
        else:
            buffer_details = (f"Place a buffer order for {a.components_needed} units of {part} this week. "
                              f"It reduces the likely gap from {a.collision_gap_weeks} to "
                              f"{a.gap_with_buffer_weeks} weeks but does not close it.")
        cards.append(ActionCard(
            role="Sourcing Lead",
            urgency="High",
            title="Secure component buffer",
            details=buffer_details,
            evidence=f"Source: {a.source_citation}. Gap {rng}.{policy_note}",
            assumption=f"Parts = relays × parts per relay. If ordered now, arrival week "
                       f"+{a.arrival_if_buffer_week} (assumption: ordering before allocation tightens "
                       f"avoids the supplier delay; parts needed by week +{a.component_need_week}).",
            decide_by=_date_in(2),
            action_key=f"po_buffer_{slug}",
        ))

        if not a.capacity_feasible:
            cards.append(ActionCard(
                role="Vaasa Plant Manager",
                urgency="Escalate",
                title="Release line capacity",
                details=f"No free assembly capacity: the line is fully committed. Decide which orders to "
                        f"move before {a.relays_needed} relays for this project can be scheduled.",
                evidence="Free capacity = 0 relays/week.",
                assumption="Free capacity = line capacity × (1 − committed share).",
                decide_by=_date_in(3),
                action_key=f"capacity_{slug}",
            ))
        else:
            start_week = max(1, a.component_need_week if a.buffer_closes_gap else a.arrival_if_buffer_week)
            if weekly_capacity:
                share = a.relays_needed / weekly_capacity * 100
                load = (f"{a.relays_needed} relays on {a.free_capacity_per_week}/week free capacity "
                        f"= {a.assembly_weeks} assembly week(s), about {share:.0f}% of one week's total line.")
            else:
                load = f"{a.relays_needed} relays, {a.assembly_weeks} assembly week(s)."
            cards.append(ActionCard(
                role="Vaasa Plant Scheduler",
                urgency="Planning",
                title="Re-sequence assembly start",
                details=f"Reserve {a.relays_needed} assembly slots from week +{start_week}, conditional on the "
                        f"buffer order. Without it, earliest start is week +{a.unmitigated_arrival_week}.",
                evidence=load,
                assumption="Free capacity = line capacity × (1 − committed share). "
                           "Start = when parts can be in the factory.",
                decide_by=_date_in(7),
                action_key=f"smt_reserve_{slug}",
            ))

        # Delivery promise: only advise a standard quote when the mitigation actually works
        if not a.capacity_feasible:
            promise = ("Do not commit a delivery date until line capacity is released. "
                       "Share an indicative window only.")
        elif a.buffer_closes_gap:
            promise = (f"If the buffer is approved and placed in time: quote standard lead time. "
                       f"If not: quote {a.collision_gap_weeks} weeks later for configurations using {part}.")
        else:
            promise = (f"A buffer alone does not close the gap. Quote at least {a.gap_with_buffer_weeks} weeks "
                       f"later with the buffer, or {a.collision_gap_weeks} weeks later without it, until "
                       f"escalation secures supply.")
        cards.append(ActionCard(
            role="Sales Operations",
            urgency="Reliability",
            title="Set the delivery promise",
            details=promise,
            evidence=(f"Without action, likely supply arrives {a.collision_gap_weeks} weeks after parts are needed. "
                      f"With a buffer ordered now: {a.gap_with_buffer_weeks} weeks."),
            assumption="Need date = on-site date − test/delivery buffer − assembly weeks.",
            decide_by=_date_in(7),
            action_key=f"quote_adjust_{slug}",
        ))

        if a.severity == "Escalate" and a.collision_gap_weeks > ACT_MAX_WEEKS:
            cards.append(ActionCard(
                role="Supply Chain Manager",
                urgency="Escalate",
                title="Escalate and start alternate-source qualification",
                details=(f"Likely gap is above {ACT_MAX_WEEKS} weeks. "
                         + ("A buffer alone does not close it. " if not a.buffer_closes_gap else "")
                         + f"Escalate allocation with the supplier and start qualification of an "
                           f"alternate source for {part} as a longer-term action."),
                evidence=f"Likely gap {a.collision_gap_weeks} weeks. Supply concentration: {a.supply_concentration}.",
                assumption=f"Escalate when the likely gap exceeds {ACT_MAX_WEEKS} weeks (editable rule).",
                decide_by=_date_in(3),
                action_key=f"escalate_{slug}",
            ))
        return cards

    def sign_off_action(
        self, card: ActionCard, trigger_event: str, decision: str = "Approved", reason: str = ""
    ) -> AuditLogEntry:
        if decision == "Approved":
            status = ("Approved, owner follows up with customer (CRM)" if card.urgency == "Opportunity"
                      else "Approved, pending execution in SAP by owner")
        else:
            status = f"Rejected{': ' + reason if reason else ''}"
        return AuditLogEntry(owner_role=card.role, action=card.title,
                             trigger_event=trigger_event, status=status)
