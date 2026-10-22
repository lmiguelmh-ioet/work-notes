# OTCM-149147 — AR-I-3018: keep selecting an unapplied exchange credit memo and its open invoice after both creation dates fall behind the last run
- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-149147
- **RICE**: AR-I-3018
- **Repos**: `oracle-integration-cloud` (PR 1: data model only, no OIC change) + `monocle_integrations` (PR 2: zero-balance skip visibility, added 2026-10-20 per user decision 1B)
- **Status** (as of 2026-10-22): **CLOSED — Jira Done 2026-10-22 14:48 ET (QA moved it; resolution Done). This file is now frozen.** Final state: PR 2 [#2795](https://github.com/WarbyParker/monocle_integrations/pull/2795) **MERGED 2026-10-22 08:46 ET**, live on stage as `vstage399` — one consolidated Error-severity Jira ticket per run naming each zero-balance skipped memo. PR 1 [#1143](https://github.com/WarbyParker/oracle-integration-cloud/pull/1143) stays open at head `babdcda1` (balance-row window + `P_LOOKBACK_MINUTES` + first-invoice rule), byte-identical on dev1 and stage, and merges at prod promotion with the #1064 stack. Stage QA complete: all 15 scenario verdicts green (T1–T11, E1–E4; R11 provisional under assumption A1), a SOX 3-seat panel's findings applied, evidence posted as Jira comment 973195. Residuals at close: Tony's Q1–Q5 answers (owner Tony; gate #1143's merge; if the ruling differs from A1, R11 re-opens per the posted evidence); Tony's description/AC update (his call on a Done ticket); the OTCM-149784 gate-wording comment (drafted at `oracle-integration-cloud/tmp/otcm149147_t910/`, posts after Tony's answer); the FSD selection-logic comment (owner Luis); the revival follow-up and the daily sweep (parked pending functional sign-off / evidence).
- **Plan**: `monocle_integrations/.cursor/plans/ar-i-3018_window_schedule_creation_554f4650.plan.md` (verbatim snapshot archived 2026-10-21 at `notes/projects.AR-I-3018.OTCM-149147.plan.md`)

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
- **The zero-balance skip** (found by the adversarial panel, code-verified): when two memos pair with the same invoice in one run, monocle applies the first, sees the invoice balance hit zero, and politely SKIPS the second — reporting success, moving the bookmark, firing no alert. The skipped memo strands invisibly. No date field can fix this; it needs a pairing/ordering decision. Open business question (Q4 in the plan): could that invoice be reused — should the skipped memo re-pair with the next eligible invoice on the same exchange reference, or stay for manual handling? (Answered 2026-10-20 by Tony: never re-pairs — now enforced by the first-invoice rule, decision 10.)

Because of the last two, the ticket's acceptance criterion AC1 ("any pair whose dates fall behind gets applied by a later scheduled run") is re-scoped honestly to the read-lag class, which the fix eliminates structurally.

### One-paragraph summary

The integration remembers where it left off with a bookmark and only looks at records "created since the bookmark". The bug: it checked the birth certificate of the invoice (the header row) but required the balance row to already exist — and the balance row is born minutes to hours later. A pair whose window closed in between vanished forever. The fix checks the balance row's birthday instead — by definition the first moment the pair could possibly be seen — so anything not yet visible simply shows up in a later window. A small lookback covers the seconds-scale commit race. Old records are recovered by manual runs anytime; human un-applies and same-invoice memo collisions are documented as follow-ups, not silently ignored.

## Outcome
- **CLOSED 2026-10-22 (Jira Done).** PR 2 **MERGED 2026-10-22** (skip visibility live on stage as `vstage399`). PR 1 head `babdcda1` (window + lookback parameter + first-invoice rule) is live and byte-verified on dev1 AND stage; it merges at prod promotion with the #1064 stack. Stage QA: 15/15 scenario verdicts green including the pin scenarios T9–T11; the evidence comment (Jira comment 973195) posted after a 3-seat SOX panel with all findings applied.

## What shipped
- PR 1 [#1143](https://github.com/WarbyParker/oracle-integration-cloud/pull/1143) (oracle-integration-cloud, OPEN, stacked on #1064's branch): window on each side's first open balance-row creation + `P_LOOKBACK_MINUTES` lookback parameter (default 5) + the first-invoice rule. Head `babdcda1`. Dev1 and stage both carry the full pinned text, byte-identical to the PR (8865 B; stage pasted 2026-10-22, sanity run passed).
- PR 2 [#2795](https://github.com/WarbyParker/monocle_integrations/pull/2795) (monocle_integrations, **MERGED 2026-10-22 08:46 ET**): one consolidated Error-severity Jira ticket per run naming each zero-balance skipped memo (+ invoice, exchange reference); abort path tickets too. Ticket text aligned with the first-invoice rule (`9926940de`); both review threads answered.

## Decisions

### Functional clarifications (Q&A)
1. Q1 (repeating-failure reporting): per-run error notification acceptable; the team fixes invalid data first (Luis, chat, 2026-10-20).
2. Q2 (unbounded vs lookback): superseded — the window mechanism STAYS ("a proven pattern used by everyone in this repo"); fix stranding inside it (Luis, chat, 2026-10-20).
3. Q3 (monocle contract shape): flat request + one field — moot; the chosen fix needs no monocle change (Luis, chat, 2026-10-20).
4. Q4 (zero-balance skip): answered by Tony ([Jira comment 971887](https://warbyparker.atlassian.net/browse/OTCM-149147?focusedCommentId=971887), 2026-10-20): several memos of one exchange DO share one invoice by design; a skip means the replacement total dropped after the memos were raised; the skipped memo must NEVER re-pair — its remainder belongs to an AR-I-3019 refund; the skip must be visible; unapply-revival stays manual. Follow-up ticket for AR-I-3019 selection handed to Gabriel Viera (2026-10-20), filed as **OTCM-149784** (2026-10-21).
5. Q5 (Tony's comment 972074, 8 items): answered 2026-10-21 with a benchmark- and panel-verified reply — a 500 freezes the last-run date (no OIC change); the pointer records the run start; medians ~1 s on both pods; skip tickets at Error, unassigned, routed to the on-call engineer by triage; stage QA per the acceptance criteria.

### Design decisions (ours)
1. Window the report on the open-balance row's creation date — `MIN(creation_date)` per transaction over `ar_payment_schedules_all`, carried on both sides; the row's creation is the first moment the pair is selectable (Luis, 2026-10-20, after both panels).
2. Add a small lookback (`:P_FROM_DATE - X` minutes) on the window's lower bound to close the stamp-early/commit-late race; X = 5 recommended (Luis, 2026-10-20).
3. No OIC flow change — the flow is shared; the skip-`UpdateLastRunDate` hardening (OI-3 of OTCM-143188) stays deferred (Luis, 2026-10-20).
4. No managed backlog drain — old stranded records are recovered by manual ad hoc runs anytime (Luis, 2026-10-20).
5. Unapply-revival stays manual — auto-reapply would fight a deliberate human unapply; documented on the ticket, automatic variant parked as a follow-up (Luis, 2026-10-20).
6. Solution verified by a 3-seat independent panel (all three converged on the same family: keep the window, fix the date basis, manual backlog recovery, no monocle change) and a 2-seat adversarial panel (both ADOPT WITH CHANGES; changes folded) (Luis, 2026-10-20).
7. Zero-balance skip visibility IN scope as PR 2 (Luis "1B", 2026-10-20): one Error-severity Jira ticket per skipped memo — Warning is auto-rejected by the daily sweep, a 500 would freeze the pointer for every other pair.
8. Lookback value: 5 minutes confirmed (Luis, 2026-10-20) → narrowed to 2 (Luis, 2026-10-20) → restored to 5 AND parameterized as `P_LOOKBACK_MINUTES` (default 5) after Tony's PR review asked for configurability (Luis, 2026-10-21). Day-2 tuning = change the parameter default in the BIP console.
9. Header overclaim conceded to Tony's review: "keeps every pair reachable" → "makes each pair selectable in the window that covers the later side's balance-row creation" (Luis, 2026-10-21).
10. First-invoice rule (Luis, 2026-10-21; hazard raised in johnny-coral-wp's #1143 review): a memo pairs only with the first invoice raised on the exchange reference — the lowest-id transaction with INV-class schedule rows, open or closed — in every run mode. After it closes, the memo never re-pairs; the remainder goes to the AR-I-3019 refund. Alternatives rejected: closed-sibling exclusion (false positive on a closed non-first sibling), sibling-application exclusion (blind when no sibling application exists). Unapply re-qualifies the memo as today and revival stays manual onto the first invoice. Gated on Tony's Q1–Q5 (asked on Slack 2026-10-21).

## Evidence
- Root cause, stage (2026-10-19): invoice 18024 header 19:59:23 vs balance row 20:03:26; memo 31014 applied by hand since.
- Lag distribution, stage: memos <=29s (349/349); invoices median 212s, avg 228s, max 3.6h (810–873 sampled) -> ~35% of new-invoice pairs strand on first pass.
- Stage backlog: 23 eligible pairs (2026-10-20); every examined pair carries the cross-boundary RC1 fingerprint (header :59/:29 -> balance row :02/:32). Zero backdated balance rows in 90 days.
- Pointer fault-gating: `UpdateLastRunDate` never runs on a monocle fault — orchestration-verified in the extracted `.iar` (catch -> rethrow skips it); AC3 already met structurally.
- Falsification probe (2026-10-20): pairs selectable today but dropped under the new basis = 0 (no selection regression).
- Column types: all relevant `creation_date`/`last_update_date` columns are TIMESTAMP(6) on stage AND dev1; the current query already compares TIMESTAMP to `CAST(:P AS DATE)`, so the change adds no type risk.
- Panel reports: `oracle-integration-cloud/tmp/otcm149147_q2/round1/indep_{1,2,3}.md`, `round2/adv_{1,2}.md`.
- Dev1 verification (2026-10-20/21): T1 basis proof, E1 boundary, T7 A/B 23 identical / 0 diffs. Parameterized re-run (2026-10-21): E1 boundary passed with `P_LOOKBACK_MINUTES` unpassed — the report echoed the default 5; from = T+4min selected, from = T+6min zero rows.
- Live parity (2026-10-21): dev1 and stage DM SQL byte-identical to the repo `.sql` (7907 B); parameter `name="P_LOOKBACK_MINUTES" defaultValue="5" dataType="xsd:integer"` on both pods; catalog export parity OK.
- The "separate steps" named (2026-10-21, stage): invoice header by ESS `AutoInvoiceImportEss`; balance row minutes later by `Vertex.Taxuser` (`PopulatePartnerLines` job or inline call) — the Vertex tax completion creates the payment schedule row. Memos: one OAuth API client writes both rows 2–4 s apart.
- Reply verification (2026-10-21): 2 independent seats word-level over both posted replies; 4 conservative edits folded (no "same window", "no materially backdated", dropped unsourced "sub-second", "has not occurred"). Reports: `oracle-integration-cloud/tmp/otcm149147_pr1143_comments/verify_round1/seat_{1,2}.md`.
- Timing benchmark (2026-10-21, independent agent, 30/30 runs): medians 1d 0.8 s / 1m 0.9 s / 1y 0.9 s on dev1, 1d 1.0 s / 1m 1.0 s / 1y 0.9 s on stage; worst 1.7 s (two cold starts). Report: `oracle-integration-cloud/tmp/otcm149147_jira_comment/timing_benchmark_report.md`.
- Comment-972074 verification (2026-10-21, 3 seats): ~25 findings, all ruled on and applied before posting. Caught the stale TPP79X00Z7 claim: the pair was applied on stage 2026-10-19 20:54 UTC (application 377956, 31014 → 18024, 395.00) before the fix reached stage. Reports: `oracle-integration-cloud/tmp/otcm149147_jira_comment/verification/seat_{1,2,3}_report.md`.
- Comment 972074 reply POSTED 2026-10-21 ~09:20 ET (user's final trims recorded in the plan; as-posted text in `tmp/otcm149147_jira_comment/comment_972074_reply.md`).
- Pin panels (2026-10-21, documents only, no live pods): 3 independent seats converged (hazard real, fix in the DM selection query, predicate outside the window OR-block) + 2 adversarial seats (ADOPT WITH CHANGES, 0 blockers). Reports were `oracle-integration-cloud/tmp/otcm149147_repair/round{1,2}/` (deleted 2026-10-22, consolidated here and in the plan). Slack question-set verification: was `tmp/otcm149147_slack_q/verif.md` (deleted 2026-10-22; POSTABLE WITH EDITS, all applied; caught the FSD-overclaim on the two-shipment case and the consolidated-ticket shape).
- Pin dev1 paste (2026-10-21): freshness gate all-pass (live dev1 == stage == `b7b290d0`); live CDATA byte-identical to the pinned `.sql` (8865 B) after `catalog_upload.py`; catalog re-export parity OK (`xdm_catalog_sql.py`).
- T9/T10 dev1 legs (2026-10-22, artifacts `oracle-integration-cloud/tmp/otcm149147_t910/`): A/B 23 identical / 0 old-only / 0 new-only / 0 value diffs (window 2026-07-01 → 10-22, lookback 5). Population probe: 25 never-applied open OMG memos, 2 pinned-out — memo 34039 (invoice 53042 closed by sibling CM application, the skip signature) and memo 35030 (invoice 51293 closed by cash receipt, class 3). Ad hoc `:P_TRX_NUMBER` on 34039/35030/53042 → 0 rows; positive control 32032 pairs with its first invoice. T9's two-invoice case has no dev1 data — stage seeding stays the venue.

## Test data
- Skill: `ar-i-3018-credit-memo-test-data` (seed/revive pairs on stage).
- Existing stage fixtures (from OTCM-143188): `TestTPCOLA01` (contract-test pair — never for ad hoc runs), `TestTPCOLA02`/`03` (burnable, revived, eligible), `04` (left applied), `05` (left partially applied).

## Open items
- Tony's Q1–Q5 answers (owner Tony; merge gate for #1143) — asked on Slack 2026-10-21; Q1 re-asks the FSD-thread question he was cc'd on 2026-10-13 and never answered. R11 ran under the assumed ruling A1 and re-opens if he rules differently (stated in the posted evidence).
- Tony updates the ticket description and acceptance criteria (his commitment once items 1–2 of 972074 were answered; the ticket is Done — his call whether it still happens).
- Gate-wording comment on OTCM-149784 DRAFTED 2026-10-22 (`oracle-integration-cloud/tmp/otcm149147_t910/otcm149784_gate_comment.md`) — post after Tony's Q1 answer; tracked on OTCM-149784.
- FSD comment on the window basis (F8, owner Luis): reply in the existing selection-logic thread ([Drive id AAACIoDQK4A](https://docs.google.com/document/d/18VyR76v5hXvU09rnibpgzxgHljVcZqtR/edit?disco=AAACIoDQK4A)) — draft needs the parameter wording.
- Revival follow-up ticket (automatic re-selection) — parked pending functional sign-off.
- Daily wide-range sweep — follow-up gated on evidence of long transactions (per the posted reply).
- Merge: PR 1 at prod promotion bundled with the #1064 stack (repo convention); PR 2 merged 2026-10-22.
- DONE 2026-10-22 — stage QA scenarios T1–T11/E1–E4 (evidence comment 973195; T2 used the equivalent-pair fallback; T11 ran under assumption A1).
- DROPPED 2026-10-22 — PR-2 Jira comment (the consolidated shape and assignment deferral live in the merged PR body and code).

## Artifacts
- Plan: `monocle_integrations/.cursor/plans/ar-i-3018_window_schedule_creation_554f4650.plan.md`
- Sibling ticket notes: [projects.AR-I-3018.OTCM-143188](projects.AR-I-3018.OTCM-143188.md)
- FSD export + comment sidecar: `integrations/AR-I-3018/docs/` (Drive-synced)
- Skill updated this ticket: `implement-jira-ticket` (Phase 2.5 — two-round solution verification panel, born from this ticket's process)
