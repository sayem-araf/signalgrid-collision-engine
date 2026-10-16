# Lovable update prompt

Paste the block below into the existing Lovable project chat. It changes only the rules, texts and tests listed; layout and styling stay as they are. `LOVABLE_PROMPT.md` is the full prompt with the same changes, for rebuilding from scratch.

```
Update the SignalGrid logic. Change only what is listed here; keep layout and styling.

1. LOGIC
freeCap          = Math.max(0, Math.round(lineCapacity * (1 - committedPct / 100)))   (was Math.max(1, ...))
capacityFeasible = freeCap > 0 || relays === 0
assemblyWeeks    = relays > 0 && freeCap > 0 ? Math.ceil(relays / freeCap) : 0
gapWithBuffer    = Math.max(0, arrivalIfBuffer - partsNeededWeek)
bufferClosesGap  = gapWithBuffer === 0
severity = !capacityFeasible ? "Escalate"
         : gapLikely > 8 ? "Escalate"
         : gapLikely > 0 ? "Act"
         : gapWorst > 0 ? "Watch"
         : "None"
(Any positive likely gap is Act or Escalate. Watch always means gapLikely is 0.)
Input check: delayBest <= delayLikely <= delayWorst, all >= 0; otherwise show an error instead of results.

2. ASSUMPTIONS DRAWER
- committedPct range 50 to 100 (was 50 to 95).
- erpFlagWeek label "Assumed week a delay shows in ERP today", tooltip "Assumption, not measured: when a
  purchase order would miss its confirmed date in today's process. Used only for comparison."

3. KPI TILES
Collision gap: always show the computed "{gapLikely} weeks" (never hardcode "0 weeks").
  If !capacityFeasible: sub "No free line capacity · Escalate", red.
Time left to act, checked in this order:
  - !capacityFeasible: "Blocked", sub "Release line capacity first", red
  - collides and !bufferClosesGap: "Too late for buffer", sub "Buffer ordered now still {gapWithBuffer} wk late · escalate", red
  - collides and latestOrderWeek == 0: "This week", sub "Order now to close the gap · assumes ERP flags at wk +{erpFlagWeek}", red
  - collides: "{latestOrderWeek} weeks", sub "Order by week +{latestOrderWeek} to close the gap · assumes ERP flags at wk +{erpFlagWeek}"
  - otherwise: "n/a"
Replace every "flagged {erpFlagWeek} wk before ERP" with "assumes ERP flags at wk +{erpFlagWeek}".

4. CHART AND BANNER
- Green band label: "Early-warning window · {erpFlagWeek} wk (assumed)".
- New first banner case, !capacityFeasible (red): "No free line capacity (escalate). The assembly line is
  fully committed, so no valid schedule exists for {relays} relays. Release capacity before committing a
  delivery date."
- In the collision banner, "Today's process would surface this..." becomes "Assumption: today's process would
  surface this...", and the ending uses bufferClosesGap (not latestOrderWeek >= 0):
  false -> "Even a buffer ordered now arrives at week +{arrivalIfBuffer}, {gapWithBuffer} weeks after the need date: escalate."

5. DECISION CARDS
a. Secure component buffer, details:
   bufferClosesGap -> "Place a buffer order for {parts} units of {part} " + (latestOrderWeek <= 0 ? "this week" : "by week +{latestOrderWeek}") + ", before supplier allocation tightens. This closes the likely gap."
   else -> "Place a buffer order for {parts} units of {part} this week. It reduces the likely gap from {gapLikely} to {gapWithBuffer} weeks but does not close it."
b. If !capacityFeasible, replace "Re-sequence assembly start" with: Vaasa Plant Manager (red pill) ·
   "Release line capacity" · "No free assembly capacity: the line is fully committed. Decide which orders to
   move before {relays} relays for this project can be scheduled." · Why "Free capacity = 0 relays/week." · +3 days.
   Otherwise the re-sequence start week is max(1, bufferClosesGap ? partsNeededWeek : arrivalIfBuffer).
c. Set the delivery promise, details (never advise a standard quote unless the buffer closes the gap):
   !capacityFeasible -> "Do not commit a delivery date until line capacity is released. Share an indicative window only."
   bufferClosesGap -> "If the buffer is approved and placed in time: quote standard lead time. If not: quote {gapLikely} weeks later for configurations using {part}."
   else -> "A buffer alone does not close the gap. Quote at least {gapWithBuffer} weeks later with the buffer, or {gapLikely} weeks later without it, until escalation secures supply."
   Why: "Without action, likely supply arrives {gapLikely} weeks after parts are needed. With a buffer ordered now: {gapWithBuffer} weeks."
d. Escalate and start alternate-source qualification: show only when gapLikely > 8. Details start
   "Likely gap is above 8 weeks. " + (bufferClosesGap ? "" : "A buffer alone does not close it. ").

6. ACCEPTANCE TESTS (existing A, B, C values stay the same) plus, on Scenario A unless stated:
- delay best/likely/worst 2/6/10: gaps 0/1/5, Act (not Watch), KPI "1 weeks", 4 cards
- delay 3/7/11: gaps 0/2/6, Act, KPI "2 weeks"
- delay 0/4/8: gaps 0/0/3, Watch, KPI "0 weeks", 2 cards
- committed 100%: likely gap 5, Escalate, "No free line capacity", time left "Blocked", has "Release line capacity", no "Re-sequence assembly start"
- Scenario B, policy delay 2, stress 50%: buffer arrives week 16, needed by 14, "Too late for buffer", delivery card does not say "quote standard lead time"
```
