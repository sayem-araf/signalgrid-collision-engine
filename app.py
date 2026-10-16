import os
import sys
from dataclasses import asdict
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from schemas import ExtractedEvent, BOMConfig
from core.engine import CollisionEngine
from agents.orchestrator import PrescriptiveOrchestratorAgent

st.set_page_config(
    page_title="SignalGrid",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ----------------- COLOURS -----------------
NAVY = "#0f1b2d"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#8a8985"
BORDER = "#e6e4df"
SURFACE = "#fcfcfb"
BLUE = "#2a78d6"        # series 1: site need
ORANGE = "#eb6834"      # series 2: delayed supply
GOOD = "#0ca30c"
WARN = "#c98500"
CRIT = "#d03b3b"

# ----------------- STYLE -----------------
st.markdown(
    f"""
<style>
  #MainMenu, footer, header [data-testid="stToolbar"] {{ visibility: hidden; }}
  .block-container {{ padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1500px; }}
  html, body, [class*="css"] {{ font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }}

  .sg-header {{
    background: {NAVY}; color: #fff; border-radius: 14px; padding: 18px 24px;
    display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;
  }}
  .sg-header h1 {{ font-size: 1.6rem; margin: 0; color: #fff; font-weight: 700; letter-spacing: .2px; }}
  .sg-header p {{ margin: 2px 0 0; color: #b9c3d3; font-size: .95rem; }}
  .sg-badges {{ display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }}
  .sg-badge {{ border: 1px solid #33445e; color: #dbe3ee; border-radius: 999px; padding: 4px 12px; font-size: .78rem; white-space: nowrap; }}

  .sg-kpi {{
    background: #fff; border: 1px solid {BORDER}; border-radius: 12px; padding: 14px 16px;
    border-left: 5px solid var(--accent); height: 100%;
  }}
  .sg-kpi .lbl {{ color: {INK_2}; font-size: .82rem; font-weight: 600; text-transform: uppercase; letter-spacing: .4px; }}
  .sg-kpi .val {{ color: {INK}; font-size: 2rem; font-weight: 750; line-height: 1.15; margin-top: 4px; }}
  .sg-kpi .sub {{ color: {INK_2}; font-size: .82rem; margin-top: 2px; }}

  .sg-section {{ font-size: 1.05rem; font-weight: 700; color: {INK}; margin: 18px 0 8px; }}
  .sg-section span {{ color: {MUTED}; font-weight: 500; font-size: .85rem; margin-left: 6px; }}

  .sg-signal {{ background: #fff; border: 1px solid {BORDER}; border-radius: 12px; padding: 12px 14px; margin-bottom: 10px; }}
  .sg-signal .top {{ display: flex; gap: 6px; align-items: center; margin-bottom: 6px; flex-wrap: wrap; }}
  .sg-signal .title {{ font-weight: 650; color: {INK}; font-size: .95rem; }}
  .sg-signal .body {{ color: {INK_2}; font-size: .86rem; margin-top: 4px; line-height: 1.4; }}
  .sg-signal .src {{ color: {MUTED}; font-size: .75rem; margin-top: 6px; }}

  .pill {{ display: inline-block; border-radius: 999px; padding: 2px 10px; font-size: .72rem; font-weight: 700; letter-spacing: .3px; }}
  .pill-demand {{ background: #e6f0fb; color: #1c5cab; }}
  .pill-supply {{ background: #fdeee6; color: #a8431c; }}
  .pill-policy {{ background: #ece9f8; color: #4a3aa7; }}
  .pill-watch {{ background: #fdf3dc; color: #8a5a00; }}
  .pill-esc {{ background: #fbe7e7; color: #a32727; }}
  .pill-sales {{ background: #e3f4ee; color: #0f6b4c; }}
  .pill-high {{ background: #fbe7e7; color: #a32727; }}
  .pill-med {{ background: #fdf3dc; color: #8a5a00; }}
  .pill-low {{ background: #e5f5e5; color: #0a6e0a; }}
  .pill-role {{ background: #eef1f6; color: #2b3a52; }}
  .pill-ok {{ background: #e5f5e5; color: #0a6e0a; }}
  .pill-rej {{ background: #f1f0ed; color: #52514e; }}

  .sg-card-title {{ font-size: 1.05rem; font-weight: 700; color: {INK}; margin: 8px 0 4px; }}
  .sg-card-body {{ color: {INK}; font-size: .9rem; line-height: 1.45; }}
  .sg-card-meta {{ color: {INK_2}; font-size: .8rem; margin-top: 8px; line-height: 1.4; }}
  .sg-card-meta b {{ color: {INK}; }}

  .sg-banner {{ border-radius: 10px; padding: 10px 14px; font-size: .9rem; margin-top: 4px; }}
  .sg-banner.crit {{ background: #fbe7e7; color: #7d1d1d; border: 1px solid #f2c6c6; }}
  .sg-banner.watch {{ background: #fdf3dc; color: #6b4600; border: 1px solid #f3dfae; }}
  .sg-banner.ok {{ background: #e9f6e9; color: #0a5a0a; border: 1px solid #c5e7c5; }}

  .sg-formula {{ background: #fff; border: 1px solid {BORDER}; border-radius: 12px; padding: 12px 16px; font-size: .86rem; color: {INK_2}; line-height: 1.7; }}
  .sg-formula code {{ color: {INK}; background: #f4f3f0; padding: 1px 6px; border-radius: 4px; }}
</style>
""",
    unsafe_allow_html=True,
)

# ----------------- STATE -----------------
if "audit_log" not in st.session_state:
    st.session_state.audit_log = []
if "decisions" not in st.session_state:
    st.session_state.decisions = {}

# ----------------- SCENARIOS (all illustrative) -----------------
SCENARIOS = {
    "A · Hyperscale data center": {
        "signals": [
            {"type": "Demand", "severity": "High", "age": "1 day ago",
             "title": "Grid connection permit for 60 MW data center (Phase 1)",
             "body": "Zoning and high-voltage connection approved in an industrial area near the plant. "
                     "Energisation expected in about 6 months.",
             "source": "Municipal planning notice (illustrative)"},
            {"type": "Supply", "severity": "High", "age": "3 days ago",
             "title": "Packaging lead times extend 8–16 weeks for precision ADCs",
             "body": "Semiconductor packaging capacity tight for high-reliability multichannel ADCs. "
                     "Likely extension 12 weeks.",
             "source": "OSAT lead-time bulletin (illustrative)"},
            {"type": "Policy", "severity": "Medium", "age": "5 days ago",
             "title": "Tariff on imported semiconductor raw materials",
             "body": "Adds about 2 weeks for parts packaged in a single region (customs and re-routing).",
             "source": "Trade notice (illustrative)"},
        ],
        "event": dict(project="Hyperscale data center, Phase 1 (illustrative)", mw=60.0, need_week=26,
                      delay_weeks=12, delay_best_weeks=8, delay_worst_weeks=16, policy_delay_weeks=2,
                      critical_part="16-bit multichannel ADC",
                      market_tightness="Distributor stock declining (illustrative)",
                      source="Planning notice + OSAT bulletin + trade notice (illustrative)",
                      supply_concentration="Single region", is_new_project=True, tender_expected_week=6),
    },
    "B · Offshore wind substation": {
        "signals": [
            {"type": "Demand", "severity": "High", "age": "5 days ago",
             "title": "180 MW offshore wind connection enters TSO queue",
             "body": "Environmental permit finalised. Substation equipment needed in about 5.5 months.",
             "source": "TSO connection queue (illustrative)"},
            {"type": "Supply", "severity": "High", "age": "1 week ago",
             "title": "Optical transceiver lead times extend 10–18 weeks",
             "body": "Supplier factory maintenance reduces output of optical Ethernet transceivers. "
                     "Likely extension 14 weeks.",
             "source": "Component market report (illustrative)"},
        ],
        "event": dict(project="Offshore wind substation (illustrative)", mw=180.0, need_week=24,
                      delay_weeks=14, delay_best_weeks=10, delay_worst_weeks=18, policy_delay_weeks=0,
                      critical_part="Optical Ethernet transceiver",
                      market_tightness="Franchised channel stock declining (illustrative)",
                      source="TSO queue entry + market report (illustrative)",
                      supply_concentration="Few regions", is_new_project=True, tender_expected_week=4),
    },
    "C · Routine demand, no disruption": {
        "signals": [
            {"type": "Demand", "severity": "Low", "age": "Planned",
             "title": "Routine substation maintenance programme",
             "body": "Regular feeder and breaker maintenance across the region. Covered by the current plan.",
             "source": "Internal planning schedule (illustrative)"},
            {"type": "Supply", "severity": "Low", "age": "Today",
             "title": "Standard lead times on approved vendor list",
             "body": "No unusual movement in lead times or distributor stock.",
             "source": "Supplier confirmations (illustrative)"},
        ],
        "event": dict(project="Routine substation maintenance (illustrative)", mw=20.0, need_week=34,
                      delay_weeks=0, delay_best_weeks=0, delay_worst_weeks=2, policy_delay_weeks=0,
                      critical_part="Standard logic ICs", market_tightness="Normal replenishment",
                      source="Internal planning schedule (illustrative)", supply_concentration="Diversified",
                      is_new_project=False),
    },
}

SEV_PILL = {"High": "pill-high", "Medium": "pill-med", "Low": "pill-low"}
TYPE_PILL = {"Demand": "pill-demand", "Supply": "pill-supply", "Policy": "pill-policy"}

# ----------------- SIDEBAR: ASSUMPTIONS -----------------
with st.sidebar:
    st.markdown("### Assumptions")
    st.caption("Illustrative values. In a pilot these come from a weekly read-only BOM and ERP export.")
    relays_per_mw = st.slider("Relays per MW (proxy for bay count)", 0.2, 1.0, 0.5, 0.05,
                              help="Demo proxy. In a pilot, relay count comes from bay/feeder count in tender documents.")
    parts_per_relay = st.slider("Critical parts per relay", 1, 16, 8, 1)
    weekly_capacity = st.slider("Assembly line capacity (relays/week)", 50, 300, 140, 10)
    committed_pct = st.slider("Capacity already committed (%)", 50, 95, 85, 5)
    buffer_wk = st.slider("Test + delivery after assembly (weeks)", 1, 8, 3, 1)
    baseline_lt = st.slider("Normal component lead time (weeks)", 6, 26, 14, 1)
    erp_detection_week = st.slider("Week a delay normally shows in ERP", 6, 24, 14, 1,
                                   help="When a purchase order misses its confirmed date.")
    st.divider()
    if st.button("Reset demo", use_container_width=True):
        st.session_state.audit_log = []
        st.session_state.decisions = {}
        st.rerun()

# ----------------- HEADER -----------------
st.markdown(
    """
<div class="sg-header">
  <div>
    <h1>📡 SignalGrid</h1>
    <p>Early warning for component lead-time collisions</p>
    <p style="font-size:.85rem;color:#8fa0b8">Concept prototype · Built for the ABB Distribution Solutions challenge</p>
  </div>
  <div class="sg-badges">
    <span class="sg-badge">Context: protection relay planning, Vaasa</span>
    <span class="sg-badge">Demo data · illustrative</span>
    <span class="sg-badge">Read-only · human approval</span>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ----------------- SCENARIO PICKER + STRESS -----------------
labels = list(SCENARIOS.keys())
c_pick, c_stress = st.columns([3, 2], gap="large")
with c_pick:
    try:
        choice = st.segmented_control("Signal scenario", labels, default=labels[0], label_visibility="collapsed")
    except AttributeError:
        choice = st.radio("Signal scenario", labels, horizontal=True, label_visibility="collapsed")
choice = choice or labels[0]
with c_stress:
    stress_pct = st.slider("Demand stress test: demand above permit estimate (%)", 0, 50, 0, 10)
sc = SCENARIOS[choice]

# ----------------- ENGINE -----------------
config = BOMConfig(
    mw_to_relay_ratio=relays_per_mw, adcs_per_relay=parts_per_relay,
    vaasa_weekly_smt_capacity=weekly_capacity, committed_capacity_share=committed_pct / 100,
    test_delivery_buffer_weeks=buffer_wk, baseline_lead_time_weeks=baseline_lt,
    erp_detection_week=erp_detection_week, demand_stress=stress_pct / 100,
)
engine = CollisionEngine(config=config)
event = ExtractedEvent(**sc["event"])
a = engine.evaluate_collision(event)
collides = a.severity in ("Act", "Escalate")

# ----------------- KPI ROW -----------------
def kpi(col, label, value, sub, accent):
    col.markdown(
        f'<div class="sg-kpi" style="--accent:{accent}"><div class="lbl">{label}</div>'
        f'<div class="val">{value}</div><div class="sub">{sub}</div></div>',
        unsafe_allow_html=True,
    )

k1, k2, k3, k4 = st.columns(4)
if collides:
    kpi(k1, "Collision gap (likely)", f"{a.collision_gap_weeks} weeks",
        f"Range {a.gap_best_weeks}–{a.gap_worst_weeks} wk (best–worst) · {a.severity}", CRIT)
elif a.severity == "Watch":
    kpi(k1, "Collision gap (likely)", "0 weeks", f"Worst case {a.gap_worst_weeks} wk · Watch", WARN)
else:
    kpi(k1, "Collision gap", "None", "Supply arrives in time, even in the worst case", GOOD)
latest_order_week = a.latest_order_week   # last week to order the buffer and still close the gap
stress_note = f" · +{stress_pct}% stress" if stress_pct else ""
if collides:
    if latest_order_week == 0:
        kpi(k2, "Time left to act", "This week",
            f"Order now to close the gap · flagged {erp_detection_week} wk before ERP", CRIT)
    elif latest_order_week > 0:
        kpi(k2, "Time left to act", f"{latest_order_week} weeks",
            f"Order by week +{latest_order_week} to close the gap · flagged {erp_detection_week} wk before ERP",
            CRIT if latest_order_week <= 2 else WARN)
    else:
        kpi(k2, "Time left to act", "Overdue",
            f"A buffer alone can't close the gap · flagged {erp_detection_week} wk before ERP", CRIT)
else:
    kpi(k2, "Time left to act", "n/a", "No delay to act on", MUTED)
if a.is_new_project:
    tender = f" · tender ~wk +{a.tender_expected_week}" if a.tender_expected_week is not None else ""
    kpi(k3, "Sales opportunity", f"~{a.relays_needed} relays",
        f"New project before tender{tender}{stress_note}", "#0f6b4c")
else:
    kpi(k3, "Sales opportunity", "None new", f"Routine demand · {a.relays_needed} relays{stress_note}", MUTED)
kpi(k4, "Critical parts at risk" if collides else "Critical parts required", f"{a.components_needed:,}",
    f"{a.critical_part} · {a.supply_concentration.lower()} · {a.assembly_weeks} assembly wk",
    ORANGE if collides else MUTED)

# ----------------- SIGNALS + TIMELINE -----------------
left, right = st.columns([2, 3], gap="large")

with left:
    st.markdown('<div class="sg-section">Incoming signals<span>demand · supply · policy</span></div>',
                unsafe_allow_html=True)
    for s in sc["signals"]:
        st.markdown(
            f'<div class="sg-signal"><div class="top">'
            f'<span class="pill {TYPE_PILL[s["type"]]}">{s["type"].upper()}</span>'
            f'<span class="pill {SEV_PILL[s["severity"]]}">{s["severity"]}</span>'
            f'<span style="color:{MUTED};font-size:.75rem;margin-left:auto">{s["age"]}</span></div>'
            f'<div class="title">{s["title"]}</div><div class="body">{s["body"]}</div>'
            f'<div class="src">Source: {s["source"]}</div></div>',
            unsafe_allow_html=True,
        )
    with st.expander("Structured event (cached extraction)"):
        st.markdown(
            f"- **Project:** {a.project}\n"
            f"- **Capacity:** {a.mw:.0f} MW\n"
            f"- **Needed on site:** week +{a.need_week}\n"
            f"- **Critical part:** {a.critical_part} ({a.supply_concentration.lower()})\n"
            f"- **Supplier delay:** {event.delay_best_weeks}–{event.delay_worst_weeks} wk, likely {event.delay_weeks}\n"
            f"- **Policy delay:** +{a.policy_delay_weeks} wk\n"
            f"- **Market:** {a.market_tightness}"
        )
        st.caption("Language model output structured into a fixed schema. Cached for the demo.")

with right:
    st.markdown('<div class="sg-section">Collision timeline<span>weeks from today</span></div>',
                unsafe_allow_html=True)

    horizon = max(40, a.arrival_worst_week + 4, a.need_week + 6)
    weeks = list(range(0, horizon + 1))

    def ramp(end_week, ramp_len, total):
        out = []
        for w in weeks:
            if w >= end_week:
                out.append(total)
            elif w >= end_week - ramp_len:
                out.append(round(total * (w - (end_week - ramp_len)) / ramp_len))
            else:
                out.append(0)
        return out

    total = a.relays_needed
    need = ramp(a.component_need_week, 3, total)          # parts needed in factory
    supply_likely = ramp(a.unmitigated_arrival_week, 3, total)
    supply_normal = ramp(baseline_lt, 3, total)

    fig = go.Figure()
    ymax = max(1, total) * 1.3

    if collides:
        fig.add_vrect(x0=0, x1=erp_detection_week, fillcolor="rgba(12,163,12,0.07)", line_width=0, layer="below")
        fig.add_annotation(x=erp_detection_week / 2, y=ymax * 0.96, text=f"Early-warning window · {erp_detection_week} wk",
                           showarrow=False, font=dict(color="#0a6e0a", size=12))
    # best-likely-worst arrival range, drawn as a bracket near the top
    if a.arrival_worst_week > a.arrival_best_week:
        yb = ymax * 0.84
        fig.add_shape(type="line", x0=a.arrival_best_week, x1=a.arrival_worst_week, y0=yb, y1=yb,
                      line=dict(color=ORANGE, width=2))
        for xe in (a.arrival_best_week, a.arrival_worst_week):
            fig.add_shape(type="line", x0=xe, x1=xe, y0=yb - ymax * 0.025, y1=yb + ymax * 0.025,
                          line=dict(color=ORANGE, width=2))
        fig.add_trace(go.Scatter(x=[a.unmitigated_arrival_week], y=[yb], mode="markers", showlegend=False,
                                 marker=dict(color=ORANGE, size=9, line=dict(color=SURFACE, width=2)),
                                 hovertemplate="Likely arrival wk %{x}<extra></extra>"))
        fig.add_annotation(x=(a.arrival_best_week + a.arrival_worst_week) / 2, y=yb + ymax * 0.05,
                           text=f"Arrival range wk {a.arrival_best_week}–{a.arrival_worst_week}",
                           showarrow=False, font=dict(color="#a8431c", size=11), bgcolor="rgba(252,252,251,0.9)")
    if a.collision_gap_weeks > 0:
        fig.add_vrect(x0=a.component_need_week, x1=a.unmitigated_arrival_week, fillcolor="rgba(208,59,59,0.16)",
                      line_width=0, layer="below")
        fig.add_annotation(x=(a.component_need_week + a.unmitigated_arrival_week) / 2, y=ymax * 0.96,
                           text=f"Gap · {a.collision_gap_weeks} wk", showarrow=False,
                           font=dict(color="#a32727", size=12), bgcolor="rgba(251,231,231,0.95)")

    fig.add_trace(go.Scatter(x=weeks, y=supply_normal, name="Supply at normal lead time", mode="lines",
                             line=dict(color=MUTED, width=2, dash="dot"),
                             hovertemplate="%{y} relays' parts<extra>Normal supply</extra>"))
    fig.add_trace(go.Scatter(x=weeks, y=need, name="Parts needed in factory", mode="lines",
                             line=dict(color=BLUE, width=2.5), fill="tozeroy", fillcolor="rgba(42,120,214,0.10)",
                             hovertemplate="%{y} relays' parts<extra>Needed</extra>"))
    if collides:
        fig.add_trace(go.Scatter(x=weeks, y=ramp(a.arrival_if_buffer_week, 3, total),
                                 name="Supply if buffer ordered now", mode="lines",
                                 line=dict(color="#0ca30c", width=2.5, dash="dash"),
                                 hovertemplate="%{y} relays' parts<extra>With action</extra>"))
    fig.add_trace(go.Scatter(x=weeks, y=supply_likely, name="Supply, likely delay", mode="lines",
                             line=dict(color=ORANGE, width=2.5),
                             hovertemplate="%{y} relays' parts<extra>Likely supply</extra>"))

    markers = [(0, "Today")]
    if collides:
        markers.append((erp_detection_week, "ERP would flag"))
    markers.append((a.need_week, "On site"))
    for x, label in markers:
        fig.add_vline(x=x, line=dict(color=INK_2, width=1, dash="dash"))
        fig.add_annotation(x=x, y=ymax * 0.06, text=label, showarrow=False, xanchor="left", xshift=4,
                           font=dict(color=INK_2, size=11), bgcolor="rgba(252,252,251,0.85)")

    fig.update_layout(
        height=380, margin=dict(l=10, r=10, t=10, b=20),
        plot_bgcolor=SURFACE, paper_bgcolor="rgba(0,0,0,0)", font=dict(color=INK_2, size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="left", x=0, font=dict(size=12)),
        hovermode="x unified",
        xaxis=dict(range=[-0.5, horizon], showgrid=False, zeroline=False, ticksuffix=" wk", linecolor=BORDER),
        yaxis=dict(range=[0, ymax], title="Relays' worth of parts", gridcolor="#efeee9", zeroline=False),
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    if collides:
        st.markdown(
            f'<div class="sg-banner crit"><b>Collision detected ({a.severity.lower()}).</b> {a.critical_part} likely arrives '
            f'at week +{a.unmitigated_arrival_week} (range {a.arrival_best_week}–{a.arrival_worst_week}), but parts are '
            f'needed in the factory by week +{a.component_need_week} to reach site at week +{a.need_week}. '
            f'Today\'s process would surface this around week +{erp_detection_week}. '
            + (f'If the buffer is ordered now, parts arrive by week +{a.arrival_if_buffer_week} and the gap closes.</div>'
              if a.latest_order_week >= 0 else
              f'Even a buffer ordered now arrives at week +{a.arrival_if_buffer_week}, after the need date: escalate.</div>'),
            unsafe_allow_html=True)
    elif a.severity == "Watch":
        st.markdown(
            f'<div class="sg-banner watch"><b>Watch.</b> Likely supply is on time, but the worst case '
            f'(week +{a.arrival_worst_week}) misses the factory need date (week +{a.component_need_week}).</div>',
            unsafe_allow_html=True)
    else:
        st.markdown(
            f'<div class="sg-banner ok"><b>No collision.</b> Even the worst case (week +{a.arrival_worst_week}) arrives '
            f'before parts are needed (week +{a.component_need_week}). No action needed.</div>',
            unsafe_allow_html=True)

# ----------------- DECISIONS -----------------
st.markdown('<div class="sg-section">Recommended decisions<span>sales · sourcing · production · a person approves every action</span></div>',
            unsafe_allow_html=True)

orch = PrescriptiveOrchestratorAgent()
cards = orch.generate_action_cards(a, weekly_capacity=weekly_capacity)

if not cards:
    st.markdown('<div class="sg-banner ok">No decisions required. Cards appear for new projects (sales) '
                'and when a supply risk is detected.</div>', unsafe_allow_html=True)
else:
    slots = []
    for i in range(0, len(cards), 3):
        slots += st.columns(3, gap="medium")
    for col, card in zip(slots, cards):
        key = card.action_key
        decision = st.session_state.decisions.get(key)
        role_cls = {"Escalate": "pill-esc", "Watch": "pill-watch", "Opportunity": "pill-sales"}.get(card.urgency, "pill-role")
        with col:
            with st.container(border=True):
                status_pill = ""
                if decision == "Approved":
                    status_pill = '<span class="pill pill-ok" style="float:right">✓ Approved</span>'
                elif decision == "Rejected":
                    status_pill = '<span class="pill pill-rej" style="float:right">Rejected</span>'
                st.markdown(
                    f'<span class="pill {role_cls}">{card.role.upper()}</span>{status_pill}'
                    f'<div class="sg-card-title">{card.title}</div>'
                    f'<div class="sg-card-body">{card.details}</div>'
                    f'<div class="sg-card-meta"><b>Why:</b> {card.evidence}<br>'
                    f'<b>Rule:</b> {card.assumption}<br>'
                    f'<b>Decide by:</b> {card.decide_by}</div>',
                    unsafe_allow_html=True,
                )
                if decision is None:
                    b1, b2 = st.columns(2)
                    if b1.button("Approve", key=f"ok_{key}", type="primary", use_container_width=True):
                        st.session_state.decisions[key] = "Approved"
                        st.session_state.audit_log.append(asdict(orch.sign_off_action(card, a.project)))
                        st.toast(f"Approved and logged for {card.role}.", icon="✅")
                        st.rerun()
                    with b2.popover("Reject", use_container_width=True):
                        reason = st.text_input("Reason", key=f"reason_{key}", placeholder="e.g. buffer already covered")
                        if st.button("Confirm reject", key=f"rej_{key}"):
                            st.session_state.decisions[key] = "Rejected"
                            st.session_state.audit_log.append(
                                asdict(orch.sign_off_action(card, a.project, "Rejected", reason)))
                            st.rerun()

# ----------------- AUDIT + METHOD -----------------
c_log, c_method = st.columns([3, 2], gap="large")

with c_log:
    st.markdown('<div class="sg-section">Decision log<span>nothing is written to ERP</span></div>',
                unsafe_allow_html=True)
    if not st.session_state.audit_log:
        st.caption("No decisions recorded yet.")
    else:
        df = pd.DataFrame(st.session_state.audit_log)[["timestamp", "owner_role", "action", "status"]]
        df.columns = ["Time", "Owner", "Action", "Status"]
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Export log (CSV)", df.to_csv(index=False).encode("utf-8"),
                           file_name=f"signalgrid_log_{datetime.now():%Y%m%d_%H%M}.csv", mime="text/csv")

with c_method:
    st.markdown('<div class="sg-section">How the numbers are calculated<span>deterministic</span></div>',
                unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="sg-formula">
Relays = <code>{a.mw:.0f} MW × {relays_per_mw} × (1 + {stress_pct}%)</code> = <b>{a.relays_needed}</b><br>
Parts = <code>{a.relays_needed} × {parts_per_relay}</code> = <b>{a.components_needed:,}</b><br>
Assembly = <code>{a.relays_needed} ÷ {a.free_capacity_per_week} free/wk</code> = <b>{a.assembly_weeks} wk</b><br>
Parts needed by = <code>{a.need_week} − {buffer_wk} − {a.assembly_weeks}</code> = week <b>+{a.component_need_week}</b><br>
Arrival = <code>{baseline_lt} + delay ({event.delay_best_weeks}/{event.delay_weeks}/{event.delay_worst_weeks}) + {a.policy_delay_weeks} policy</code> = week <b>+{a.arrival_best_week}/{a.unmitigated_arrival_week}/{a.arrival_worst_week}</b><br>
Gap (best/likely/worst) = <b>{a.gap_best_weeks}/{a.collision_gap_weeks}/{a.gap_worst_weeks} wk</b><br>
Time left to act = <code>{a.component_need_week} − ({baseline_lt} + {a.policy_delay_weeks})</code> = <b>{a.latest_order_week} wk</b><br>
<span style="color:{MUTED}">The language model only structures signal text. All quantities and dates come from these rules.</span>
</div>
""",
        unsafe_allow_html=True,
    )

st.caption("Policy signals, uncertainty ranges and the demand stress test are adapted from Ardeshir Zohrabi's "
           "conceptual market model. All data illustrative, including tender timing estimates. "
           "A production version would connect to ERP, BOM, procurement and supplier data.")
