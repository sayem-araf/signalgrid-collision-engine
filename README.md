# SignalGrid

Early warning for component lead-time collisions in protection relay planning. A read-only decision-support prototype: public signals in, recommended decisions out, a person approves every action. All demo data is illustrative.

## Pipeline

1. **Signal extraction** (`agents/extractor.py`). The only language-model step. Structures demand, supply and policy signals into a fixed schema. Without `ANTHROPIC_API_KEY`, or if the call fails, it loads a cached fixture and says so. Model is set with `ANTHROPIC_MODEL`.
2. **Collision engine** (`core/engine.py`). Deterministic rules:
   - Relays = MW × relays per MW (demo proxy for bay/feeder count) × (1 + demand stress)
   - Parts = relays × parts per relay
   - Assembly weeks = relays ÷ free line capacity, where free capacity = capacity × (1 − committed share)
   - Parts needed by = on-site week − test/delivery buffer − assembly weeks
   - Arrival (best/likely/worst) = baseline lead time + supplier delay range + policy delay
   - Gap = arrival − parts-needed week; severity None / Watch / Act / Escalate
3. **Recommended decisions** (`agents/orchestrator.py`). Rule-based cards scaled to severity: confirm dates (Watch); buffer order, assembly re-sequencing, quote adjustment (Act); plus escalation and alternate-source qualification (Escalate).
4. **Decision log**. Approvals and rejections are recorded in the session and exported as CSV. Nothing is written to ERP.

Policy signals, uncertainty ranges and the demand stress test are adapted from Ardeshir Zohrabi's conceptual market model.

## Run

```bash
pip install -r requirement.txt
streamlit run app.py      # dashboard
python3 rundemo.py        # command-line check, standard library only
```
