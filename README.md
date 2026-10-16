# SignalGrid Collision Engine

Decision support for component lead time risk in protection relay production planning.

SignalGrid estimates when the critical components for a new electrification project must be in the factory, compares that date with expected supplier arrival, and recommends actions for sales, sourcing and production. Every figure is produced by explicit rules, and every action requires human approval.

> **Demonstration data only.** All projects, quantities, capacities and lead times in this repository are illustrative.

## Overview

| Stage | Module | Description |
|---|---|---|
| Signal extraction | `agents/extractor.py` | Converts demand, supply and policy notices into a structured event. Uses a language model when an API key is configured, otherwise loads cached fixtures. |
| Collision engine | `core/engine.py` | Deterministic calculation of demand, assembly capacity, need date, arrival range, gap and severity. |
| Recommendations | `agents/orchestrator.py` | Role based action cards, scaled to severity. |
| Dashboard | `app.py` | Streamlit interface with scenarios, editable assumptions, timeline and decision log. |

The system is read only. Decisions are recorded in the session and can be exported as CSV; nothing is written to ERP or CRM systems.

## Calculation

```
relays             = MW × relays_per_MW × (1 + demand_stress)
parts              = relays × parts_per_relay
free_capacity      = line_capacity × (1 − committed_share)
assembly_weeks     = ceil(relays / free_capacity)
parts_needed_week  = on_site_week − test_and_delivery_weeks − assembly_weeks
arrival_week       = lead_time + supplier_delay + policy_delay        (best, likely, worst)
gap                = max(0, arrival_week − parts_needed_week)
buffer_arrival     = lead_time + policy_delay
latest_order_week  = parts_needed_week − buffer_arrival
```

| Severity | Condition |
|---|---|
| None | Parts arrive in time, including the worst case |
| Watch | Likely gap is 0, worst case is late |
| Act | Likely gap of 1 to 8 weeks |
| Escalate | Likely gap above 8 weeks, or no free line capacity |

A standard delivery quote is recommended only when a buffer ordered now arrives by the parts needed week.

## Getting started

Requires Python 3.10 or later.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
streamlit run app.py
```

`python rundemo.py` runs the full pipeline from the command line using only the standard library.

Optional environment variables:

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Enables live signal extraction |
| `ANTHROPIC_MODEL` | Overrides the default extraction model |

## Testing

```bash
python -m pytest
```

The suite covers:

- reference values for the three demonstration scenarios
- severity boundaries at gaps of 0, 1, 2, 3, 8 and 9 weeks
- zero free line capacity and a buffer that arrives too late
- rejection of inconsistent inputs
- a parameter sweep confirming that no recommendation contradicts the engine
- a Streamlit AppTest run confirming that the dashboard shows the engine's values

## Project structure

```
agents/
  extractor.py          signal extraction
  orchestrator.py       recommendations and decision log entries
core/
  engine.py             collision engine
fixtures/               cached extraction output
tests/                  pytest suite
app.py                  Streamlit dashboard
scenarios.py            demonstration scenarios
schemas.py              data structures
rundemo.py              command line run
LOVABLE_PROMPT.md       specification for the web demo
LOVABLE_UPDATE.md       change specification for the existing web demo
```

## Assumptions and limitations

- Relays per MW is a proxy. In practice the relay count comes from bay and feeder numbers in tender documents.
- The buffer rule assumes that ordering early avoids the supplier allocation delay. This requires validation against supplier delivery history.
- Projects are evaluated individually. Several projects drawing on the same line capacity are not yet assessed together.
- The ERP detection week is an input assumption used for comparison, not a measured result.
- There is no live connection to ERP, procurement or supplier data.

## Changelog

**1.1.0**

- Watch is limited to a likely gap of 0; any positive likely gap is classed as Act or Escalate, and the dashboard always shows the calculated gap.
- Zero free line capacity is reported as infeasible and escalated, instead of being treated as one relay per week.
- Delivery recommendations check whether a buffer closes the gap before advising a standard quote.
- The ERP detection week is labelled as an assumption.
- Input validation for supplier delay ranges and negative values.
- Test suite added.

**1.0.0**

Initial prototype, built at the Junction x Vaasa Hackathon 2026 for the ABB Distribution Solutions challenge. The original submission is available at [signalgrid-ai-agent](https://github.com/sayem-araf/signalgrid-ai-agent).

## Acknowledgements

Policy signals, uncertainty ranges and the demand stress test are adapted from a conceptual market model by Ardeshir Zohrabi.

## License

Released under the MIT License. See [LICENSE](LICENSE).
