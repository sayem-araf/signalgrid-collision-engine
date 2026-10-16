# SignalGrid collision engine

Early warning for component lead time collisions in protection relay planning. Project signals go in; a deterministic engine checks whether critical parts will arrive before they are needed, and turns the result into recommended decisions that a person approves.

This repository is the maintained version of the prototype first built at the Junction x Vaasa Hackathon for the ABB Distribution Solutions challenge. The hackathon submission is kept unchanged at [signalgrid-ai-agent](https://github.com/sayem-araf/signalgrid-ai-agent). All data is illustrative.

## What it does

1. **Signal extraction** (`agents/extractor.py`). The only language model step. It turns demand, supply and policy text into fixed fields. Without `ANTHROPIC_API_KEY` it loads a cached fixture and says so.
2. **Collision engine** (`core/engine.py`). Closed form rules, no learning:
   - Relays = MW × relays per MW × (1 + demand stress)
   - Parts = relays × parts per relay
   - Free capacity = line capacity × (1 − committed share); assembly weeks = relays ÷ free capacity
   - Parts needed by = on site week − test and delivery − assembly weeks
   - Arrival (best, likely, worst) = lead time + supplier delay range + policy delay
   - Gap = arrival − parts needed week
   - Buffer check: does a buffer ordered now (lead time + policy) arrive by the parts needed week?
3. **Decisions** (`agents/orchestrator.py`). Cards for sales, sourcing, production and sales operations. A card only recommends a standard delivery quote when the engine confirms the buffer closes the gap.
4. **Decision log**. Approvals and rejections are recorded in the session and exported as CSV. Nothing is written to ERP.

### Severity rules

| Severity | Rule |
|---|---|
| None | On time even in the worst case |
| Watch | Likely on time (gap 0), worst case late |
| Act | Likely gap 1 to 8 weeks |
| Escalate | Likely gap above 8 weeks, or no free line capacity |

## Run

```bash
pip install -r requirements-dev.txt
streamlit run app.py        # dashboard
python3 rundemo.py          # command line run, standard library only
python3 -m pytest           # tests
```

## Tests

`tests/` covers the scenario values shared with the Lovable demo, severity boundaries (gaps of 0, 1, 2, 3, 8 and 9 weeks), zero free capacity, a buffer that arrives too late, and a sweep of about 570 parameter combinations checking that no decision card contradicts the engine. A Streamlit AppTest run checks that the KPI row shows the engine's numbers.

## Changes since the hackathon

An independent code review found four issues. All are fixed and covered by tests.

| Issue | Fix |
|---|---|
| A likely gap of 1 to 2 weeks was classed as Watch and shown as 0 weeks | Watch now means likely gap 0. Any positive likely gap is Act or Escalate, and the KPI always shows the engine's number |
| Zero free capacity was treated as one relay per week | No free capacity is reported as infeasible and escalated to the plant; no assembly slots are proposed |
| The delivery card advised a standard quote even when a buffer would arrive too late | The engine checks whether the buffer closes the gap; cards and the KPI say so when it does not |
| The ERP comparison week read like a measured result | Labelled as an assumption throughout |

The engine also rejects inconsistent inputs (a supplier delay range where best > likely or likely > worst, negative MW or policy delay). Scenarios now live in `scenarios.py`, shared by the dashboard and tests. `LOVABLE_UPDATE.md` carries the same fixes to the Lovable demo.

## Limitations

This prototype demonstrates a method, not verified business impact.

- All signals and planning values are illustrative. There is no ERP connection, automated signal collection or SQL reporting layer.
- Relays per MW is a proxy. In practice the count comes from bay and feeder numbers in tender documents.
- The buffer rule assumes that ordering now avoids the supplier allocation delay. This needs validation against supplier history.
- Each project is evaluated on its own. Several projects sharing the same line capacity could overload it together.
- The ERP detection week is an input assumption used for comparison, not a measured early warning gain.

## Credits

Policy signals, uncertainty ranges and the demand stress test are adapted from Ardeshir Zohrabi's conceptual market model.
