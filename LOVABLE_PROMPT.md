# SignalGrid: final Lovable prompt (paste everything inside the code block)

```
Build a single-page web app called "SignalGrid".

PURPOSE
Decision-support dashboard for planners at a protection relay factory. It turns public early signals
(project permits, supplier lead-time changes, trade/policy notices) into a lead-time collision check,
a sales opportunity, and recommended decisions that a person approves or rejects. Read-only prototype:
all data is illustrative, nothing is written to any ERP or CRM system.

TECH CONSTRAINTS
- React + TypeScript + Tailwind (shadcn/ui allowed), Recharts for the chart.
- Everything runs client-side. No backend, no database, no login, no live AI or API calls.
- All calculations are deterministic and must follow the LOGIC section exactly. Do NOT hardcode results.
- No company logos, no trademark symbols, no real supplier or vendor names, no money figures.

VISUAL STYLE
- Light theme, readable on a projector. Page background #f6f5f2; cards white, 1px border #e6e4df, radius 12px.
- Text #0b0b0b primary, #52514e secondary, #8a8985 muted. System font stack.
- Colours: navy header #0f1b2d; blue #2a78d6 (need line); orange #eb6834 (supply line); green #0ca30c
  (with-action line, good); amber #c98500 (warning); red #d03b3b (critical); violet #4a3aa7 (policy);
  sales green #0f6b4c.
- Calm, factual tone. No marketing language. Simple transitions only.

LAYOUT (top to bottom)
1. Header band (navy, rounded): title "SignalGrid" with a small antenna icon.
   Line 1: "Early warning for component lead-time collisions".
   Line 2 (smaller, muted): "Concept prototype · Built for the ABB Distribution Solutions challenge".
   Right: three outline badges "Context: protection relay planning, Vaasa", "Demo data · illustrative",
   "Read-only · human approval". A small "Assumptions" button opens the assumptions drawer.
2. Row: scenario tabs (segmented control) left; right a slider
   "Demand stress test: demand above permit estimate (%)", 0–50, step 10, default 0.
3. KPI row: four tiles with coloured left border (see KPI TILES).
4. Two columns (40/60). Left: "Incoming signals" (subtitle "demand · supply · policy") signal cards, then a
   collapsible "Structured event (cached extraction)". Right: "Collision timeline" (subtitle
   "weeks from today") chart and a status banner below.
5. "Recommended decisions" (subtitle "sales · sourcing · production · a person approves every action"):
   decision cards, three per row.
6. Two columns (60/40). Left: "Decision log" (subtitle "nothing is written to ERP") table + "Export log (CSV)".
   Right: "How the numbers are calculated" (subtitle "deterministic").
7. Footer caption: "Policy signals, uncertainty ranges and the demand stress test are adapted from
   Ardeshir Zohrabi's conceptual market model. All data illustrative, including tender timing estimates.
   A production version would connect to ERP, BOM, procurement and supplier data."

ASSUMPTIONS DRAWER (sliders; caption "Illustrative values. In a pilot these come from a weekly read-only
BOM and ERP export."; plus a "Reset demo" button that clears all decisions and the log)
- relaysPerMW 0.5 (0.2–1.0, step 0.05) "Relays per MW (proxy for bay count)",
  tooltip "Demo proxy. In a pilot, relay count comes from bay/feeder count in tender documents."
- partsPerRelay 8 (1–16) "Critical parts per relay"
- lineCapacity 140 (50–300, step 10) "Assembly line capacity (relays/week)"
- committedPct 85 (50–95, step 5) "Capacity already committed (%)"
- testDeliveryWeeks 3 (1–8) "Test + delivery after assembly (weeks)"
- baseLeadTime 14 (6–26) "Normal component lead time (weeks)"
- erpFlagWeek 14 (6–24) "Week a delay normally shows in ERP", tooltip "When a purchase order misses its
  confirmed date."

LOGIC (implement exactly; all weeks are "weeks from today")
relays           = Math.max(0, Math.round(mw * relaysPerMW * (1 + stressPct / 100)))
parts            = relays * partsPerRelay
freeCap          = Math.max(1, Math.round(lineCapacity * (1 - committedPct / 100)))
assemblyWeeks    = relays > 0 ? Math.ceil(relays / freeCap) : 0
partsNeededWeek  = needWeek - testDeliveryWeeks - assemblyWeeks
base             = baseLeadTime + policyDelay
arrivalBest      = base + delayBest
arrivalLikely    = base + delayLikely
arrivalWorst     = base + delayWorst
gapX             = Math.max(0, arrivalX - partsNeededWeek)        (for Best, Likely, Worst)
arrivalIfBuffer  = base          (assumption, illustrative: ordering the buffer now, before allocation
                                  tightens, avoids the supplier delay)
latestOrderWeek  = partsNeededWeek - arrivalIfBuffer   (last week to order and still close the gap)
severity = gapLikely > 8 ? "Escalate" : gapLikely > 2 ? "Act" : gapWorst > 0 ? "Watch" : "None"
collides = severity is "Act" or "Escalate"

SCENARIOS (tabs; all values illustrative)
A, tab "A · Hyperscale data center":
  project "Hyperscale data center, Phase 1 (illustrative)", mw 60, needWeek 26, delayBest 8,
  delayLikely 12, delayWorst 16, policyDelay 2, part "16-bit multichannel ADC",
  concentration "Single region", market "Distributor stock declining (illustrative)",
  source "Planning notice + OSAT bulletin + trade notice (illustrative)",
  isNewProject true, tenderExpectedWeek 6.
  Signals:
  - DEMAND · High · "1 day ago" · "Grid connection permit for 60 MW data center (Phase 1)" ·
    "Zoning and high-voltage connection approved in an industrial area near the plant. Energisation
    expected in about 6 months." · Source: Municipal planning notice (illustrative)
  - SUPPLY · High · "3 days ago" · "Packaging lead times extend 8–16 weeks for precision ADCs" ·
    "Semiconductor packaging capacity tight for high-reliability multichannel ADCs. Likely extension
    12 weeks." · Source: OSAT lead-time bulletin (illustrative)
  - POLICY · Medium · "5 days ago" · "Tariff on imported semiconductor raw materials" ·
    "Adds about 2 weeks for parts packaged in a single region (customs and re-routing)." ·
    Source: Trade notice (illustrative)
B, tab "B · Offshore wind substation":
  project "Offshore wind substation (illustrative)", mw 180, needWeek 24, delayBest 10,
  delayLikely 14, delayWorst 18, policyDelay 0, part "Optical Ethernet transceiver",
  concentration "Few regions", market "Franchised channel stock declining (illustrative)",
  source "TSO queue entry + market report (illustrative)", isNewProject true, tenderExpectedWeek 4.
  Signals:
  - DEMAND · High · "5 days ago" · "180 MW offshore wind connection enters TSO queue" ·
    "Environmental permit finalised. Substation equipment needed in about 5.5 months." ·
    Source: TSO connection queue (illustrative)
  - SUPPLY · High · "1 week ago" · "Optical transceiver lead times extend 10–18 weeks" ·
    "Supplier factory maintenance reduces output of optical Ethernet transceivers. Likely extension
    14 weeks." · Source: Component market report (illustrative)
C, tab "C · Routine demand, no disruption":
  project "Routine substation maintenance (illustrative)", mw 20, needWeek 34, delayBest 0,
  delayLikely 0, delayWorst 2, policyDelay 0, part "Standard logic ICs", concentration "Diversified",
  market "Normal replenishment", source "Internal planning schedule (illustrative)",
  isNewProject false, tenderExpectedWeek none.
  Signals:
  - DEMAND · Low · "Planned" · "Routine substation maintenance programme" ·
    "Regular feeder and breaker maintenance across the region. Covered by the current plan." ·
    Source: Internal planning schedule (illustrative)
  - SUPPLY · Low · "Today" · "Standard lead times on approved vendor list" ·
    "No unusual movement in lead times or distributor stock." · Source: Supplier confirmations (illustrative)

SIGNAL CARDS
Type pill (DEMAND light blue/blue text, SUPPLY light orange/orange text, POLICY light violet/violet text),
severity pill (High red, Medium amber, Low green), age right-aligned muted, bold title, body, muted source.
Structured event (collapsible): project; capacity MW; needed on site week +needWeek; critical part
(concentration lowercase); supplier delay "{best}–{worst} wk, likely {likely}"; policy delay "+{policyDelay} wk";
market. Caption: "Language model output structured into a fixed schema. Cached for the demo."

KPI TILES
stressNote = stressPct > 0 ? " · +{stressPct}% stress" : ""
1. Collision gap
   - collides: label "Collision gap (likely)", value "{gapLikely} weeks",
     sub "Range {gapBest}–{gapWorst} wk (best–worst) · {severity}", red border.
   - Watch: value "0 weeks", sub "Worst case {gapWorst} wk · Watch", amber border.
   - None: label "Collision gap", value "None", sub "Supply arrives in time, even in the worst case", green.
2. Time left to act
   - collides and latestOrderWeek > 0: value "{latestOrderWeek} weeks",
     sub "Order by week +{latestOrderWeek} to close the gap · flagged {erpFlagWeek} wk before ERP",
     border red if latestOrderWeek <= 2 else amber.
   - collides and latestOrderWeek == 0: value "This week",
     sub "Order now to close the gap · flagged {erpFlagWeek} wk before ERP", red.
   - collides and latestOrderWeek < 0: value "Overdue",
     sub "A buffer alone can't close the gap · flagged {erpFlagWeek} wk before ERP", red.
   - otherwise: value "n/a", sub "No delay to act on", grey.
3. Sales opportunity
   - isNewProject: value "~{relays} relays", sub "New project before tender · tender ~wk +{tenderExpectedWeek}"
     + stressNote, sales-green border.
   - else: value "None new", sub "Routine demand · {relays} relays" + stressNote, grey.
4. Critical parts: label collides ? "Critical parts at risk" : "Critical parts required",
   value parts (thousands separator), sub "{part} · {concentration lowercase} · {assemblyWeeks} assembly wk",
   orange border if collides else grey.

TIMELINE CHART (Recharts, ~380px)
- x: weeks 0..horizon, horizon = max(40, arrivalWorst + 4, needWeek + 6); tick suffix " wk".
- y: 0..relays*1.3, title "Relays' worth of parts", light grid.
- ramp(endWeek, len=3, total=relays)[w] = w >= endWeek ? total
     : w >= endWeek - len ? Math.round(total * (w - (endWeek - len)) / len) : 0
- Lines: "Parts needed in factory" = ramp(partsNeededWeek), blue 2.5px with light blue area fill;
  "Supply, likely delay" = ramp(arrivalLikely), orange 2.5px;
  "Supply at normal lead time" = ramp(baseLeadTime), grey dotted 2px;
  only if collides: "Supply if buffer ordered now" = ramp(arrivalIfBuffer), green dashed 2.5px.
  Legend on top, tooltip on hover.
- Shading: if collides, light green band 0..erpFlagWeek labelled "Early-warning window · {erpFlagWeek} wk";
  if gapLikely > 0, light red band partsNeededWeek..arrivalLikely labelled "Gap · {gapLikely} wk".
- Arrival range: if arrivalWorst > arrivalBest, an orange horizontal bracket at ~84% height from
  arrivalBest to arrivalWorst with a dot at arrivalLikely, label "Arrival range wk {best}–{worst}".
- Dashed vertical markers with small labels near the bottom: "Today" (0), "ERP would flag"
  (erpFlagWeek, only if collides), "On site" (needWeek).
STATUS BANNER
- collides (red): "Collision detected ({severity lowercase}). {part} likely arrives at week +{arrivalLikely}
  (range {arrivalBest}–{arrivalWorst}), but parts are needed in the factory by week +{partsNeededWeek} to reach
  site at week +{needWeek}. Today's process would surface this around week +{erpFlagWeek}. " +
  (latestOrderWeek >= 0
    ? "If the buffer is ordered now, parts arrive by week +{arrivalIfBuffer} and the gap closes."
    : "Even a buffer ordered now arrives at week +{arrivalIfBuffer}, after the need date: escalate.")
- Watch (amber): "Watch. Likely supply is on time, but the worst case (week +{arrivalWorst}) misses the
  factory need date (week +{partsNeededWeek})."
- None (green): "No collision. Even the worst case (week +{arrivalWorst}) arrives before parts are needed
  (week +{partsNeededWeek}). No action needed."

DECISION CARDS (rule-generated, in this order; each shows role pill, title, action text, "Why:",
"Rule:", "Decide by:" as a real date "DD Mon YYYY" = today + N days, then Approve and Reject buttons)
1. If isNewProject (any severity): Account Manager (sales-green pill) · "Early sales engagement" ·
   "Tender expected around week +{tenderExpectedWeek} (estimate). Contact the developer or EPC contractor
   now, while the specification is still open. Estimated scope: about {relays} protection relays." ·
   Why "Signal detected before any tender or order. " + (collides
     ? "Supply risk is flagged below, so coordinate the delivery promise with sourcing."
     : "No supply risk detected, so a standard delivery promise is safe.") ·
   Rule "Scope = MW × relays per MW (estimate until bay count is known)." · +7 days.
2. If severity Watch: Sourcing Lead (amber pill) · "Confirm supplier dates" · "Ask the supplier to confirm
   delivery dates for {part}. No action needed yet in the likely case." · Why "Worst case arrives week
   +{arrivalWorst}; parts needed by week +{partsNeededWeek}." · Rule "Worst case = baseline lead time +
   worst-case supplier delay." · +7 days. (No further cards.)
3. If collides:
   a. Sourcing Lead · "Secure component buffer" · "Place a buffer order for {parts} units of {part} before
      supplier allocation tightens." · Why "Source: {source}. Gap {gapBest}–{gapWorst} weeks (likely
      {gapLikely})." + (policyDelay > 0 ? " Includes +{policyDelay} wk from a trade signal." : "") ·
      Rule "Parts = relays × parts per relay. If ordered now, arrival week +{arrivalIfBuffer} (illustrative:
      ordering before allocation tightens avoids the supplier delay)." · +2 days.
   b. Vaasa Plant Scheduler · "Re-sequence assembly start" · "Reserve {relays} assembly slots from week
      +{max(1, partsNeededWeek)}, conditional on the buffer order. Without it, earliest start is week
      +{arrivalLikely}." · Why "{relays} relays on {freeCap}/week free capacity = {assemblyWeeks} assembly
      week(s), about {round(relays / lineCapacity * 100)}% of one week's total line." · Rule "Free capacity =
      line capacity × (1 − committed share)." · +7 days.
   c. Sales Operations · "Set the delivery promise" · "If the buffer is approved: quote standard lead time
      and use delivery reliability as a differentiator in the tender. If not: quote {gapLikely} weeks later
      for configurations using {part}." · Why "Without action, likely supply arrives {gapLikely} weeks after
      parts are needed." · Rule "Need date = on-site date − test/delivery buffer − assembly weeks." · +7 days.
   d. Only if Escalate: Supply Chain Manager (red pill) · "Escalate and start alternate-source qualification" ·
      "Gap exceeds a buffer-only fix. Escalate allocation with the supplier and start qualification of an
      alternate source for {part} as a longer-term action." · Why "Likely gap {gapLikely} weeks. Supply
      concentration: {concentration}." · Rule "Escalate when the likely gap exceeds 8 weeks (editable rule)."
      · +3 days.
If no cards: green panel "No decisions required. Cards appear for new projects (sales) and when a supply
risk is detected."
Behaviour:
- Approve: card shows "✓ Approved" (green pill), buttons hidden, log row added, toast
  "Approved and logged for {role}."
- Reject: popover with "Reason" input and "Confirm reject"; card shows "Rejected" (grey pill), log row added.
- Decisions are stored per scenario + card, so switching tabs keeps them.

DECISION LOG
Columns: Time (YYYY-MM-DD HH:MM:SS), Owner, Action, Status.
Status: Account Manager approvals "Approved, owner follows up with customer (CRM)"; other approvals
"Approved, pending execution in SAP by owner"; rejections "Rejected: {reason}" (or "Rejected").
Empty state "No decisions recorded yet." CSV export.

FORMULA PANEL (monospace chips with live values)
Relays = {mw} MW × {relaysPerMW} × (1 + {stressPct}%) = {relays}
Parts = {relays} × {partsPerRelay} = {parts}
Assembly = {relays} ÷ {freeCap} free/wk = {assemblyWeeks} wk
Parts needed by = {needWeek} − {testDeliveryWeeks} − {assemblyWeeks} = week +{partsNeededWeek}
Arrival = {baseLeadTime} + delay ({best}/{likely}/{worst}) + {policyDelay} policy = week +{aB}/{aL}/{aW}
Gap (best/likely/worst) = {gB}/{gL}/{gW} wk
Time left to act = {partsNeededWeek} − ({baseLeadTime} + {policyDelay}) = {latestOrderWeek} wk
Muted note: "The language model only structures signal text. All quantities and dates come from these rules."

ACCEPTANCE TESTS (default assumptions; the app must show exactly these values)
A 0%:  relays 30, parts 240, assembly 2, needed by 21, gap 3/7/11, Act, time left 5 weeks, 4 cards
A 50%: relays 45, parts 360, assembly 3, needed by 20, gap 4/8/12, Act, time left 4 weeks, 4 cards
B 0%:  relays 90, parts 720, assembly 5, needed by 16, gap 8/12/16, Escalate, time left 2 weeks, 5 cards
B 50%: relays 135, parts 1080, assembly 7, needed by 14, gap 10/14/18, Escalate, time left "This week", 5 cards
C 0%:  relays 10, parts 80, assembly 1, needed by 30, gap 0/0/0, None, time left n/a, 0 cards
```
