"""Demo scenarios. All values are illustrative."""

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
