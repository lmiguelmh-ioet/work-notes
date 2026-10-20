# OTCM-149147 — AR-I-3018: keep selecting an unapplied exchange credit memo and its open invoice after both creation dates fall behind the last run
- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-149147
- **RICE**: AR-I-3018
- **Repos**: `oracle-integration-cloud` (data model only — no monocle, no OIC change)
- **Status** (as of 2026-10-20, plan pending approval): root cause confirmed on stage (invoice 18024: header created 19:59:23, its open-balance row 20:03:26 — the 20:00 run's window covered the header date but the join found no balance row; every later window starts past the header date). Fix designed and verified by a 3-seat independent panel and a 2-seat adversarial panel: window the report on the open-balance row's creation date plus a small lookback. User dropped the OIC pointer-gate companion (shared flow) and the managed backlog drain (old records run manually anytime). Plan pending approval.
- **Plan**: `monocle_integrations/.cursor/plans/ar-i-3018_window_schedule_creation_554f4650.plan.md` (archive copy lands here at wrap-up)

## The stranding bug and the fix (plain terms, with the real example)

### What the integration does

When a customer exchanges a pair of glasses, the order system (OMG) creates two records in Oracle: a credit memo ("we owe the customer money back") and an invoice ("the customer owes us for the new pair"). Somebody has to cancel one against the other — apply the credit memo to the invoice — or both sit open forever and the books look wrong. AR-I-3018 is the robot that does this automatically: every 10 minutes an OIC flow wakes up, runs a report (a SQL query) that finds pairs of one unapplied credit memo + one still-open invoice on the same exchange order, and sends them to the monocle Lambda, which applies each memo to its invoice.

### The window: a bookmark, not a search

The report does not scan all of history every 10 minutes. OIC keeps a bookmark (a row in the ATP table `WP_INT_GENERIC_REPORT_PARAM`) that stores "the last time I ran". Each run asks the report: "give me pairs created between the bookmark and now", then moves the bookmark forward. The window is a ~10-minute slice of time sliding forward forever. This pattern is used by many integrations in this repo, which is exactly why it stays: the fix works inside the window mechanism, not against it.

### How the report decides if a pair is "in the window" — and where the bug lives

The report's SQL joins two Oracle tables:

- `ra_customer_trx_all` — the header table: one row per invoice or memo, stamped with `creation_date` the moment the record is born.
- `ar_payment_schedules_all` — the balance table: one row per open balance. This row is what tells the report "this invoice still has money owed" or "this memo still has credit left".

The balance row is NOT born at the same instant as the header — a background accounting process creates it later. Measured on stage: credit memos ~1–29 seconds (basically instant); invoices median 3.5 minutes, max 3.6 hours.

Today's query checks the window against the HEADER's `creation_date`, but it also requires the balance row to already exist (an `INNER JOIN` — a missing row silently drops the pair). So a pair is picked only if BOTH happen inside the same 10-minute window: the header date falls inside, AND the balance row already exists at read time.

### The bug, minute by minute (invoice 18024, stage, 2026-10-19 — real timestamps)

```text
19:59:23   Invoice 18024's header row is created (creation_date stamped)
20:00:00   Scheduled run wakes up. Window = [19:50, 20:00].
           -> Header date inside? YES (19:59:23 <= 20:00)
           -> Balance row exists yet? NO
           -> INNER JOIN drops the pair. Silently. No error, no alert.
20:00:00   Run succeeds (applied nothing). Bookmark moves to 20:00.
20:03:26   The balance row finally appears. 3.5 minutes too late.
20:10:00   Next run. Window = [20:00, 20:10].
           -> Header date 19:59:23 inside? NO — behind the bookmark.
           -> Pair never selected. Ever again. Stranded.
```

The pair fell through a crack between two conditions that both use time but measure different events. This is not a freak accident: median invoice lag 212s against a 600s window means roughly 35% of new-invoice pairs hit the crack on their first pass. All 23 pairs in today's stage backlog show this exact fingerprint (header stamped at :59, balance row at :02).

### The fix: point the window at the right clock

One change in the SQL: the window no longer asks "was the HEADER created inside the window?" but "was the BALANCE ROW created inside the window?" Concretely, the subquery that already reads `ar_payment_schedules_all` also computes `MIN(creation_date)` per transaction, and the window predicate compares that date instead — on either side (memo OR invoice), same as today. Everything else stays byte-identical: the OMG-only filter, the due-amount checks, the already-applied check, the ad hoc transaction-number bypass.

### Why this self-heals — the key insight

The balance row's creation date IS the exact moment the pair became selectable, because before that row exists the join cannot see the pair at all. The two conditions that used to race each other — "inside the window" and "visible to the query" — become the same condition. Replay the same night with the fix:

```text
19:59:23   Header created.
20:00:00   Run. Window [19:50, 20:00]. Balance row does not exist -> no date to match -> not selected (fine!).
20:03:26   Balance row created, stamped 20:03:26.
20:10:00   Next run. Window [20:00, 20:10]. Balance-row creation 20:03:26 inside? YES -> pair selected and applied.
```

If the row is not visible yet, it is created later, and its own creation stamp lands inside a future window. There is no crack left to fall through.

### The residual race, and the lookback that closes it

One microscopic race survives: if Oracle stamps the balance row at 19:59:59 but COMMITS it (makes it visible) at 20:00:07, just after the 20:00 run read, the row's creation date sits behind the bookmark even though the row appeared after it. The hole is seconds wide instead of minutes-to-hours, but it exists. The fix adds a small lookback: the window's lower bound reaches back X minutes (`:P_FROM_DATE - X`), so a row committed just after a run's read is still caught by the next runs. Re-reads are harmless — already-applied pairs are excluded by the existing applied check. Recommended X = 5 minutes; no real transaction should take even 1 minute to commit there, so the margin is large.

### What the fix does NOT rescue — and why that is OK

- **Pairs already stranded today** have old balance-row dates too; no future window reaches them. They are recovered by a manual ad hoc run (by transaction number or date range) anytime — no managed drain needed.
- **Unapply-revival**: if a human deliberately unapplies a memo, the pair re-opens with all-old dates and no scheduled window ever selects it again. Automatic re-selection would fight a deliberate human action, so revival stays manual (ad hoc run). Documented on the ticket; the automatic variant is parked as a follow-up pending functional sign-off.
- **The zero-balance skip** (found by the adversarial panel, code-verified): when two memos pair with the same invoice in one run, monocle applies the first, sees the invoice balance hit zero, and politely SKIPS the second — reporting success, moving the bookmark, firing no alert. The skipped memo strands invisibly. No date field can fix this; it needs a pairing/ordering decision. Open business question (Q4 in the plan): could that invoice be reused — should the skipped memo re-pair with the next eligible invoice on the same exchange reference, or stay for manual handling?

Because of the last two, the ticket's acceptance criterion AC1 ("any pair whose dates fall behind gets applied by a later scheduled run") is re-scoped honestly to the read-lag class, which the fix eliminates structurally.

### One-paragraph summary

The integration remembers where it left off with a bookmark and only looks at records "created since the bookmark". The bug: it checked the birth certificate of the invoice (the header row) but required the balance row to already exist — and the balance row is born minutes to hours later. A pair whose window closed in between vanished forever. The fix checks the balance row's birthday instead — by definition the first moment the pair could possibly be seen — so anything not yet visible simply shows up in a later window. A small lookback covers the seconds-scale commit race. Old records are recovered by manual runs anytime; human un-applies and same-invoice memo collisions are documented as follow-ups, not silently ignored.

## Outcome
- In flight — nothing shipped yet; plan pending approval.

## What shipped
- Nothing yet.

## Decisions

### Functional clarifications (Q&A)
1. Q1 (repeating-failure reporting): per-run error notification acceptable; the team fixes invalid data first (Luis, chat, 2026-10-20).
2. Q2 (unbounded vs lookback): superseded — the window mechanism STAYS ("a proven pattern used by everyone in this repo"); fix stranding inside it (Luis, chat, 2026-10-20).
3. Q3 (monocle contract shape): flat request + one field — moot; the chosen fix needs no monocle change (Luis, chat, 2026-10-20).

### Design decisions (ours)
1. Window the report on the open-balance row's creation date — `MIN(creation_date)` per transaction over `ar_payment_schedules_all`, carried on both sides; the row's creation is the first moment the pair is selectable (Luis, 2026-10-20, after both panels).
2. Add a small lookback (`:P_FROM_DATE - X` minutes) on the window's lower bound to close the stamp-early/commit-late race; X = 5 recommended (Luis, 2026-10-20).
3. No OIC flow change — the flow is shared; the skip-`UpdateLastRunDate` hardening (OI-3 of OTCM-143188) stays deferred (Luis, 2026-10-20).
4. No managed backlog drain — old stranded records are recovered by manual ad hoc runs anytime (Luis, 2026-10-20).
5. Unapply-revival stays manual — auto-reapply would fight a deliberate human unapply; documented on the ticket, automatic variant parked as a follow-up (Luis, 2026-10-20).
6. Solution verified by a 3-seat independent panel (all three converged on the same family: keep the window, fix the date basis, manual backlog recovery, no monocle change) and a 2-seat adversarial panel (both ADOPT WITH CHANGES; changes folded) (Luis, 2026-10-20).

## Evidence
- Root cause, stage (2026-10-19): invoice 18024 header 19:59:23 vs balance row 20:03:26; memo 31014 applied by hand since.
- Lag distribution, stage: memos <=29s (349/349); invoices median 212s, avg 228s, max 3.6h (810–873 sampled) -> ~35% of new-invoice pairs strand on first pass.
- Stage backlog: 23 eligible pairs (2026-10-20); every examined pair carries the cross-boundary RC1 fingerprint (header :59/:29 -> balance row :02/:32). Zero backdated balance rows in 90 days.
- Pointer fault-gating: `UpdateLastRunDate` never runs on a monocle fault — orchestration-verified in the extracted `.iar` (catch -> rethrow skips it); AC3 already met structurally.
- Falsification probe (2026-10-20): pairs selectable today but dropped under the new basis = 0 (no selection regression).
- Column types: all relevant `creation_date`/`last_update_date` columns are TIMESTAMP(6) on stage AND dev1; the current query already compares TIMESTAMP to `CAST(:P AS DATE)`, so the change adds no type risk.
- Panel reports: `oracle-integration-cloud/tmp/otcm149147_q2/round1/indep_{1,2,3}.md`, `round2/adv_{1,2}.md`.

## Test data
- Skill: `ar-i-3018-credit-memo-test-data` (seed/revive pairs on stage).
- Existing stage fixtures (from OTCM-143188): `TestTPCOLA01` (contract-test pair — never for ad hoc runs), `TestTPCOLA02`/`03` (burnable, revived, eligible), `04` (left applied), `05` (left partially applied).

## Open items
- Q4 (zero-balance skip, business): could the invoice be reused — should a skipped memo re-pair with the next eligible invoice on the same reference, or stay manual? To post as a Jira comment on OTCM-149147 tagging Tony Huang (draft in the plan).
- Revival follow-up ticket proposal (automatic re-selection via memo-side last-update term) — parked pending functional sign-off; documented in the same ticket comment.
- AC1 re-scope wording (read-lag class vs literal reading) — part of the same comment.
- FSD sync approval: `integrations/sync/sync.sh --refresh --no-commit` (pending since Phase 1); needed for the FSD Testing Strategy comparison at PR time.
- Lookback value X: recommend 5 minutes; confirm at plan approval.
- Panel scratch dir `oracle-integration-cloud/tmp/otcm149147_q2/` — remove after consolidation unless kept for reference.

## Artifacts
- Plan: `monocle_integrations/.cursor/plans/ar-i-3018_window_schedule_creation_554f4650.plan.md`
- Sibling ticket notes: [projects.AR-I-3018.OTCM-143188](projects.AR-I-3018.OTCM-143188.md)
- FSD export + comment sidecar: `integrations/AR-I-3018/docs/` (Drive-synced)
- Skill updated this ticket: `implement-jira-ticket` (Phase 2.5 — two-round solution verification panel, born from this ticket's process)
