# OTCM-149784 — AR-I-3019: refund unapplied exchange credit memos stranded by the zero-balance skip (plan)

- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-149784
- **RICE**: AR-I-3019 — report `WP AP AR Credit Memo Applied Report`, data model `WP_AP_AR_CREDIT_MEMO_APPLIED_DM`
- **Repo**: `oracle-integration-cloud` (single PR, stacked on PR #1147's branch)
- **Status**: **ON HOLD 2026-10-23 13:55** — PR #1151 ready for review (catalog re-export committed, V9 parity byte-identical); new DM text LIVE on stage + dev1; fixture campaign done except A5 (blocked on adjustment approval rights) and the V7 ad-hoc leg (OIC console Run Now with Luis); V7 organic leg PASSED (4 live refunds); V8 PASSED. Evidence durably at `integrations/AR-I-3019/data/OTCM-149784-qa/`; ticket file `notes/projects.AR-I-3019.OTCM-149784.md`
- **Worktree**: `oracle-integration-cloud/tmp/otcm149784-wt`, branch `OTCM-149784-ar-i-3019-unapplied-skip-refund` (base `origin/OTCM-147274-...` @ `7a1beb7e`)

## Read-only verification results (2026-10-23)

Draft = worktree `.sql` (+99/−22 vs #1147 head). A/B normalization: both variants compared with `TRUNC(SYSDATE)` on `apply_date`/`gl_date` so the SYSDATE columns cannot flap between runs (production text keeps raw `SYSDATE`).

**V1 — A/B old (#1147 text) vs new, window 2026-07-01 → 2026-10-23 16:00, key `CREDIT_MEMO_CUSTOMER_TRX_ID`:**

| Pod | identical | old_only | new_only | value_diffs | Verdict |
|---|---|---|---|---|---|
| dev1 | 1 (34038, partly applied — branch 1 preserved) | 0 | 2 (34039, 35030) | 0 | Pass |
| stage | 0 (old text selects nothing on stage today) | 0 | 1 (33070) | 0 | Pass |

new_only classification (expected-gain probes): 34039 (`TP1GPVG0GA`) and 35030 (`TP2T520108`) are never-applied OMG memos (zero application rows ever), attribute7 non-zero, first invoice `CL` at 0 with closure stamps (2026-10-21 18:14:26 / 2026-10-05 00:31:36) inside the window; 33070 is the known 149147 skip fixture. `TP1GPVG0GA` carries both classes on one reference: 34038 partly applied (leftover −15, branch 1) beside 34039 never applied (−40, branch 2); the invoice's `last_update_date` equals the closing application's creation time to the second.

**V2 — ad-hoc probes (stage, trx bypass):** new names 33070 → 1 row (AC1); old names 33070 → 0 (today's exclusion, control); new names 239003 (Manual source) → 0; new names 33072 (zero dues) → 0 (AC3).

**V5 — lookback boundary (stage, closure T = 16:46:30):** window 16:46→16:50 selects (scheduled mode, AC1); old text same window → 0 (control); `from = T+4` (16:50:30) selects; `from = T+6` (16:52:30) does not.

**Race guard (AC2):** three live unapplied OMG memos on OPEN first invoices (29045, 29033, 29047) named ad hoc → 0 rows; the closed-invoice gate holds under the trx bypass.

**Perf signal:** old 1.2 s / new 1.8 s on dev1 over the wide window; stage probes 1–2.5 s each.

Bucket JSONs + probe XMLs preserved under `/tmp/otcm149784/` (`cmp-dev1/`, `stage_new_wide.xml`, `p1`–`p9`).

**Post-review verification (2026-10-23, final text after resolutions 1A–3A):** draft-vs-final A/B — dev1 identical 3, stage identical 1 (33070), zero value diffs (guards + GREATEST excluded nothing intended); dev1 old-vs-final identical 1, old_only 0, new_only 2 (34039, 35030), zero value diffs. Boundary probes re-run with the final text (f1–f10 in `/tmp/otcm149784/`): name 33070 → 1; name 239003 → 0; name 33072 → 0; window 16:46:00–16:50:00 → 1 (33070); from T+4 → 1; from T+6 → 0; race trio 29045/29033/29047 → 0; dev1 ad-hoc 34038 (the unprobed ad-hoc × partly-applied cell, gray 9A) → exactly 1 row, payload unchanged (original −55, remaining −15). Every positive fixture so far (34039, 35030, 33070) is closure-dominant — the memo predates the closure — so the creation-dominant `GREATEST` arm carries no row-level selection evidence until the inverted-ordering leg runs (round-2, 3A).

**Pod paste (2026-10-23 13:15, write authorized by Luis):** `updateObject` on both pods with the PR text (`28b192e6` worktree file). Re-downloads byte-compared identical to the PR text on both; `P_LOOKBACK_MINUTES` (default 5) declared on both (dev1's XML gained it — its live definition predated #1147; the only other structural delta was stage's `enable_sqlid_logging`, left untouched). Live report probes: stage naming 33070 → 1 row (−50/−50, class 2), 239003 → 0; dev1 naming 34039 → 1 row (−40/−40, class 2), 34038 → 1 row (−55/−15, class 1 unchanged). Originals kept at `/tmp/otcm149784/paste/{stage,dev1}/` for rollback. Stage's organic runs select nothing until fixtures exist (33070's anchor is behind all future windows).

**QA fixture results, batch 1 (2026-10-23, live stage DM):**

- **V6 — Pass** (`TestTPCOLA07`): invoice 240001 closed by covering memo 33117 (SOAP apply, 18:15:56); leftovers 33118 (−50, customer-due) and 33119 (−30, insurance-due) unapplied. Live DM ad-hoc naming → 2 rows; scheduled window 18:10–18:20 → 2 rows (both). Note: the reference carried a prior closed pair (239001/33071 from the 149147 QA), so the first invoice is 239001, also closed — the gate held either way.
- **V3 — Pass** (`TestTPCOLA10`): memo 33120 applied (application 381837) then reversed by SOAP unapply; invoice 240002 re-closed by memo 33121. Live DM naming 33120 → 1 row (−100/−100); naming 33121 → 0 rows. D3 in evidence: a reversed memo counts as unapplied; a fully applied one is excluded.
- Report-runner date format: BIP `xsd:date` params take `MM-DD-YYYY HH24:MI:SS` (ISO input misparsed to year 0191, silently).
- Organic-refund race RESOLVED in our favor: the stage schedule refunded all four open eligible fixtures within minutes (see V7 below).

**QA fixture results, batch 2 (2026-10-23, live stage DM):**

- **V4 — Pass** (`TestTPCOLA11`): invoice 240003 ($100) closed by cash receipt `TestRCP149784A` (REST `standardReceipts` + `applyReceipt` action on schedule 244776; `RemittanceBankAccountNumber` mandatory — `REC00000601300257` for the CHASUS-0257 method family). Memo 33122 (−100) created 18:30:01, AFTER the closure (18:29:56) — inverted-ordering fixture. Ad-hoc naming → 1 row; window covering creation selected it; the organic schedule refunded it 13 s after creation. The creation-dominant `GREATEST` arm (3A) now carries row-level selection evidence.
- **Bad-reading-1 — Pass** (`TestTPCOLA12`, race-free negative fixture): invoice 240004 ($100) stays OP; invoice 240005 ($50) zeroed by receipt `TestRCP149784B`; memo 33123 (−100) unapplied. Ad-hoc naming 33123 → **0 rows** — a zero second invoice does NOT free the memo while the first is open. Permanent negative fixture; the schedule can never pick it up.
- **V7 organic scheduled leg — Pass ×4**: the active stage schedule (~10 min cadence) posted refunds as `ACTIVITY` applications by OAuth client `ec0d977d21c6460b9270430dfeee2158`: 33118 +50 @18:20:03, 33119 +30 @18:20:04 (window anchor = 240001's closure 18:15:56), 33120 +100 @18:30:14 (reversed memo — D3 refunded live), 33122 +100 @18:30:14 (V4 memo, anchor = creation 18:30:01). All four memos now CL/0. Refund amounts matched open balances exactly; no row re-selected after refund.
- **V8 perf — Pass**: stage 1-day 2.3 s / 1-month 1.8 s / 1-year 1.6 s (2 rows each — 33070 + 33111, a foreign class-1 fixture); dev1 2.9 / 2.2 / 1.9 s. Flat vs window size on both pods.

**Blocked / with Luis (2026-10-23):**

- **A5 inflated-memo leg**: WP_SCM_INTEGRATION_USER cannot produce an APPROVED adjustment anywhere — stage creates them pending (`W`: adjustments 16001/−10 and 16002/−2 on memo 33125, `TestTPCOLA13`, inert); dev1 denies the service outright (`WSFunctionPermission createAdjustment`). The approved stage adjustments all come from the AR-I-3019 OAuth client. Paths: an AR-rights user approves stage adjustment 16001 (fixture otherwise ready: memo 33125 OP, invoice 240006 OP; then I receipt-close + probe, expecting 0 rows), or posts −2 on dev1 memo 34039 (probe → 0), or skip A5 (guard is a one-line SQL condition).
- **V7 ad-hoc leg (33070)**: OIC REST API unreachable — the only local OAuth client (`.env.prod`, "Prod WMS Oauth Client") gets 401 at the design host (no ServiceInvoker role); Basic auth is dead on Gen 3; instance URL 307-redirects every API call to `design.integration.us-ashburn-1.ocp.oraclecloud.com?integrationInstance=oic-prod-axhxufzsltne-ia`. Integration: `WP_AR_I_3019_CRED_MEMO_REFU|01.00.0000` (PR #1125), params `start_date`/`end_date` (`MM-DD-YYYY HH:MM:SS`) + ad-hoc `credit_memo_trx_numbers`. Luis runs Run Now with `credit_memo_trx_numbers=33070`; I verify the refund in ERP. 33070 stays eligible (its anchor is behind the schedule's rolling window — it only appears in wide windows).
- **V9**: `.xdm.catalog` re-export via BIP UI (Luis), then parity check, commit, un-draft, QA evidence comment.

## Context (verified 2026-10-23, not from the ticket text)

The ticket's freshness premise ("dev1 and stage byte-identical today") is stale. Three-way diff of the live DM text vs `origin/main`:

| Text | Lives where | Notes |
|---|---|---|
| pre-OTCM-114232 (no `IS NOT NULL` guards), 1,866 B | **dev1 live** (untouched since 2026-04-29) | The OTCM-114232 guards on `main` were never deployed to dev1 — the ticket's "undeployed repo guards" relation, confirmed |
| `origin/main`, 2,031 B | repo only | local checkout matches it |
| PR #1147, 2,799 B | **stage live** (pasted 2026-10-22 19:11Z) | byte-identical to stage live |

Related work:

| Item | State | Bearing |
|---|---|---|
| PR #1147 (OTCM-147274, Johnny, **approved**, ticket Done, merges at prod promotion) | stage live | Already added to this DM: application-date window + `P_LOOKBACK_MINUTES`, OMG batch-source gate, ATTRIBUTE7/8 gate, application-table join. Finding 2 and two of the three "missing restrictions" are done there; its explicit out-of-scope ("a memo nothing was applied from") is this ticket's scope |
| PR #1125 (OTCM-142123, Gabriel, open, ticket Done) | OIC schedule | `start_date`/`end_date` `MM-DD-YYYY HH:MM:SS`, ad-hoc `credit_memo_trx_numbers`; sends no lookback param → DM default applies. Order-independent vs this fix |
| PR #1143 (OTCM-149147, Luis, open, QA passed 2026-10-22, stacks on #1064) | defines the pin | Memo pairs only with the first invoice on the reference (lowest-id trx with INV-class schedule rows). This ticket's closed-invoice gate mirrors that definition |
| monocle #2795 (skip visibility) | on stage (vstage399+) | one ticket per skipped memo, naming the trx number → ad-hoc recovery path |

Live skip fixture on stage (from the 149147 QA): memo **33070** (−50, `OP`, no applications, reference `TestTPCOLA06`); first invoice **238001** (`STATUS=CL`, remaining 0, `LAST_UPDATE_DATE=2026-10-22 16:46:30` = the closing application's creation); second invoice **239004** (`OP`, 80). This is the two-invoice case from the ticket comment, ready-made.

## The problem, explained from zero

### The business in one paragraph

A customer buys glasses, returns them, and takes a different pair — an **exchange**. Warby's order system (OMG) creates the exchange; Oracle (the accounting system) must record it. Oracle gets two things: a new **invoice** for the replacement pair ("the customer owes $100"), and one or more **credit memos** ("we owe the customer") — one per payment method the customer originally used, and on insured orders an extra **insurance memo**. Everything carries the same **exchange reference** so we know it belongs together.

### The settling robot (AR-I-3018)

"Applying" a credit memo to an invoice means canceling the customer's debt with the credit. AR-I-3018 is a robot that does this every 10 minutes: it reads a report of unapplied memos, pairs each with the invoice on the same reference, and applies it. A memo is **pinned to the first invoice** raised on the reference — that is the only place it will ever apply.

A normal insured exchange, step by step:

1. Invoice raised: customer owes **$150**.
2. Memo A raised: we owe the customer **$100** (their card payment).
3. Memo B raised: we owe **$50** (the insurance part).
4. Robot applies memo A → invoice $150 − $100 = $50. Robot applies memo B → $0. Books clean.

### The skip

Sometimes the replacement's total **drops after the memos are raised** — say tax is recalculated lower at collection, so the invoice lands at $100 instead of $150:

1. Invoice: **$100**. Memo A: **$100**. Memo B: **$50**.
2. Robot applies memo A → invoice **$0**.
3. Robot looks at memo B: the invoice has nothing left to pay. It **skips** memo B and moves on. By rule, a skipped memo must never pair anywhere else.

Commercially this is fine: money-services already refunded that $50 difference to the customer in real money. But Oracle has no record of it. Memo B sits there forever saying "we still owe $50", with nothing applied. AR-I-3019 is the robot that closes this: it reads a report of memos with leftover credit and records a **refund** of exactly the leftover.

### Problem 1 — the report's door is too narrow

AR-I-3019's report was built for a different case: "a memo was applied, but not fully — refund the leftover". Its gate says: **the balance must have shrunk, but not to zero**. A skipped memo never shrank — its balance is exactly its original amount (−50 == −50). It fails the gate. Even when you name the memo directly, the report returns nothing. So today, no automated flow can ever close a skipped memo.

### Problem 2 — "since last run" needs a date, and the wrong date strands records

AR-I-3019 runs on a schedule. Each run asks the report: "what happened between the last run and now?" — a moving 10-minute **window**. The report must answer using a **date** on the record. The safety rule for any scheduled robot:

> Every record must be selectable in at least one window — the window that covers the moment it became actionable. Miss that window and the record is stranded forever, because the window never comes back.

Today's report checks the memo's **creation date**. But the interesting events in a memo's life can happen weeks after creation — by then the memo is far outside every window.

### The fix — a second door in the report

Add a "skip door" with three locks, so only true skips pass:

- **(a)** the memo is an OMG exchange memo (not a manual one, not another source),
- **(b)** nobody holds a live application on it right now,
- **(c)** the **first invoice** on its exchange reference is **fully closed** (balance zero or less).

Why the first invoice: the memo is pinned there. Only when *that* invoice is closed is the memo truly stuck. A second invoice changes nothing — a zero-balance second invoice does not free the memo (it is not pairable there), and an open second invoice must not block the refund.

### The window question — what date says "this skip just became refundable"?

1. **The memo's creation date.** The skip becomes refundable when the invoice closes — often weeks after the memo exists. The memo's window passed long ago → stranded. Today's bug.
2. **The memo's application date.** Does not exist — a skipped memo has no application. That is the definition of the problem.
3. **The invoice's "closed date" columns** (`ACTUAL_DATE_CLOSED`, `GL_DATE_CLOSED`). Oracle stores them as a bare date: **midnight, no time-of-day** (verified on stage: a closure that happened at 16:46 is stamped `2026-10-22 00:00:00`). A 10-minute window with real times — say 16:40→16:50 — never contains midnight; the only window that does ran hours *before* the closure happened. Every skip would be missed. Same trap PR #1147 documented for `apply_date`.
4. **The first invoice's balance-row `last_update_date`.** The invoice's balance row is the row Oracle updates every time money moves on that invoice. When the last application drained it to $0, Oracle stamped that row with the exact second (verified on stage: `16:46:30` — identical to the closing application's creation time). That *is* the event "the memo became refundable", with a real timestamp. The next scheduled run's window contains it → the memo is selected → refunded.

So the skip door windows on the **first invoice's balance-row last update** (the MAX across its balance rows, so a multi-installment invoice keys on the row that closed last), with the `P_LOOKBACK_MINUTES` lower-bound cushion (default 5) the sister reports use for commit races. Amended 2026-10-23 by round-2 resolution 3A: the anchor is the **later** of that last update and the memo's creation (`GREATEST`), so a memo born after the closure enters the next window instead of stranding behind it — see Design.

### Step by step with the real stage fixture

| Time (UTC) | Event |
|---|---|
| 16:30:10 | Invoice **238001** raised, $100 — first invoice on `TestTPCOLA06` |
| 16:30:34 | Memos **34045** (−$100, customer) and **33070** (−$50, insurance) raised |
| 16:46:30 | AR-I-3018 applies 34045 → 238001 = $0, closes (`CL`, last update `16:46:30`); then **skips 33070** |
| 16:48:54 | Second invoice **239004** ($80) appears on the same reference — irrelevant: 33070 is pinned to the first invoice, which is closed |

- **Today:** the report, even named 33070 directly, returns 0 rows. The $50 floats in Oracle with no record.
- **After the fix:** the 16:50 run's window (16:46→16:50, with lookback) contains the first invoice's closure stamp (16:46:30) → skip door opens → 33070 selected → AR-I-3019 refunds $50 → the memo's balance closes → every later run selects nothing.

### Why it cannot go wrong

- A fresh memo on an **open** invoice fails lock (c) — the fix cannot steal a memo AR-I-3018 is about to apply (the race the ticket forbids).
- Manual and non-OMG memos fail lock (a), even named ad hoc.
- A refunded memo's balance closes — it fails every door on every later run, so no double refunds.
- A skip that **predates** the fix (closure stamp already behind all future windows) never appears organically — recovered by naming the memo ad hoc, which bypasses the window. The visibility ticket monocle opens for each skip carries exactly that number.

## Decisions (locked 2026-10-23, Luis in chat)

- **D1** — Proceed under the stated assumption (the message to Tony, 2026-10-21: a memo pairs only with the first invoice on the exchange reference; leftovers after it closes go to the AR-I-3019 refund; no manual path re-applies a skipped memo). If Tony answers differently, the gate wording follows.
- **D2** — Single PR, **stacked on PR #1147's branch** (`OTCM-147274-ar-i-3019-select-a-credit-memo-once-ar-i-3018-has-applied-it-to-its-exchange-invoice`); base = #1147's branch. Promotes bundled with #1147; order-independent vs #1125.
- **D3** — The check is **"no current application"**, not "never applied": any unapplied memo (never-applied or user-unapplied/reversed) is eligible once the first invoice is closed, because any unapplied memo can be applied again in principle — once the first invoice is closed the refund is the only closure. Terminology in code and PR: "unapplied", not "never-applied". The parked out-of-scope item stays unapply-**reapplication** (AR-I-3018 re-pairing), which this never does.
- **D4** — Skip-branch window basis: **MAX(`last_update_date`) over the first invoice's INV-class balance rows**, with the `P_LOOKBACK_MINUTES` lower-bound cushion. `ACTUAL_DATE_CLOSED` / `GL_DATE_CLOSED` rejected (date-only midnight trap). Validated on stage fixture 238001 (`16:46:30` == closing application's creation). Amended by round-2 resolution 3A (2026-10-23): the anchor is `GREATEST` of that MAX and the memo's creation date — see Design.
- **D5** — The first-invoice-closed gate is mode-independent: scheduled, ad-hoc date-range, and trx-number runs all honor it (mirrors #1143's pin placement).
- **D6** — Base text = PR #1147 head (byte-identical to stage live). dev1 live carries the pre-OTCM-114232 text (guards never deployed) — the PR states this per AC8; the paste brings dev1 straight to the new text.

## Design

Base text: PR #1147 head. One new OR-branch beside the partly-applied branch, which stays byte-identical (AC4). No new parameters; output columns unchanged → no `.xdo`, monocle, or OIC change.

Branch 1 (unchanged): partly applied — `amount_due_remaining > amount_due_original` + #1147's window on the memo's own application.

Branch 2 (new, skip class). Outer gates: `bs.name = 'OMG'`, `ABS(attribute7) > 0 OR ABS(attribute8) > 0`, `ps.amount_due_remaining < 0` (all from #1147), plus the new credit-class guard `ps.amount_due_original < 0` (an overpaid invoice has a negative balance but a positive original amount — it can never be a refund candidate). The strict gate `amount_due_remaining > amount_due_original` moves INTO branch 1. Branch 2 adds:

- `NOT EXISTS` a current application on the memo (`status = 'APP' AND display = 'Y'`) — D3.
- First-invoice-closed gate: correlated `EXISTS` over the reference's first invoice (the #1143 pin: `MIN(customer_trx_id)` among trxs sharing `ct_reference` and `invoice_currency_code` with an INV-class schedule row), `HAVING SUM(amount_due_remaining) <= 0`. Mode-independent (D5).
- Refund cap `ps.amount_due_remaining >= ps.amount_due_original`: an adjustment can push a memo's balance past its face amount (original −50, remaining −60); the refund pays `-remaining`, so the cap keeps the payout at or under the memo's face. Added in panel-review resolution 2A.
- Window in scheduled mode: `GREATEST(MAX(last_update_date) of the first invoice's INV rows, rcta.creation_date)` within `[P_FROM_DATE − P_LOOKBACK_MINUTES, P_TO_DATE]` — the later of the closure proxy and the memo's birth, so a memo created after its invoice closed enters the next window instead of stranding behind it (resolution 3A). The trx-number bypass ignores dates (ad-hoc recovery, AC6). Final form (settled by the A/B and boundary probes): gate and window fused in one `EXISTS ... HAVING`; `MAX()` is only testable in the HAVING.

Header comment, repo convention (final text in the worktree; resolution 7A reworded the class-2 paragraph — "window anchors on the later of the first invoice's last balance update (a proxy for its closure) and the memo's creation"):

```sql
-- Major changes (OTCM-149784):
--   - Class 2 added: an unapplied memo whose first invoice on the
--     exchange reference is fully closed is selected for a full-balance
--     refund, capped at the memo's original amount.
--   - Credit-class guard (amount_due_original < 0) keeps non-memo
--     documents out of both classes.
```

## PR plan

| Field | Value |
|---|---|
| Title | `[OTCM-149784] Select unapplied exchange credit memos stranded by the zero-balance skip for AR-I-3019 refund` |
| Repo / base | `oracle-integration-cloud`, base = #1147's branch (stacked, promotes bundled) |
| Contents | `WP_AP_AR_CREDIT_MEMO_APPLIED_DM.sql` + re-exported `.xdm.catalog` (same PR, AC8) |
| Size | ~80–120 lines (SQL + header comment) — single PR per pr-split-planning |
| PR body must state | the three-way live-vs-repo deltas (dev1 pre-114232 / main / stage = #1147), per AC8; the assumed Tony ruling (D1); the D3 terminology note |

## Verification plan

Read-only legs run on dev1/stage through the fusion-sql arbiter; pod writes (paste, fixture refunds) follow oracle-write-confirmation at execution time.

- **V1 — A/B old-vs-new** (`compare_sql_variants.py`): old = #1147 text, new = proposed; dev1 and stage; same wide window; key `CREDIT_MEMO_CUSTOMER_TRX_ID`. Discipline: identical ⊇; `old_only` = 0; every `new_only` row probe-verifies into the skip class (unapplied + closed first invoice + OMG); `value_diffs` = 0. Keep the bucket JSONs as evidence.
- **V2 — Ad-hoc stage probes on the new text**: 33070 selected (also proves the two-invoice case: first closed + second open selects). Negative probes, none selected even named: manual-source memo (239003), zero-due memo (33072), unapplied memo on an OPEN first invoice (fresh fixture), second-invoice-at-zero while first still open (bad reading 1 from the ticket comment).
- **V3 — Reversed-application leg (D3 in evidence)**: memo applied then reversed, first invoice closed → selected.
- **V4 — Receipt-closed first-invoice leg (Tony Q3)**: first invoice closed by a cash receipt, not a memo application → selected. Validates D4 beyond the memo-application closure shape. The same fixture covers the inverted-ordering leg (round-2, 3A): interface a second memo AFTER the closure — a window covering its creation selects it (1 row), the pre-GREATEST text returns 0 (teeth), and FROM = creation + 6 min returns 0.
- **V5 — Lookback boundary (E1-style)**: closure stamp T; `from = T+4 min` selects; `from = T+6 min` does not.
- **V6 — Multi-memo leg**: two unapplied memos on one closed first invoice (customer + insurance) → both selected, both refunded.
- **V7 — Stage e2e (QA phase, writes confirmed at execution)**: paste new DM on stage → fresh insured-exchange fixture whose second memo skips *after* the paste → organic scheduled run selects and refunds → refund row + closed balance + never re-selected. Ad-hoc leg on 33070 (`credit_memo_trx_numbers=33070` → refund 50 → balance closed → later runs select nothing, AC5). Consumes the 149147 fixture — 149147 already passed QA.
- **V8 — Perf**: median answer times on dev1/stage at 1-day / 1-month / 1-year windows (same tables + one aggregate + correlated MIN — expect the 149147 shape); one read-only prod timing at promotion (Tony's carried-over ask from 149147).
- **V9 — Catalog parity**: re-export `.xdm.catalog` after the paste; `xdm_catalog_sql.py` byte-compare vs repo `.sql`; `P_LOOKBACK_MINUTES` present in the export.
- **V10 — PR deltas stated** (AC8): dev1 (pre-114232) vs main vs stage (#1147).

## Sequencing

```
draft SQL → V1–V6 (read-only, dev1+stage) → stage paste (write confirmation)
→ V7 e2e legs → V8 perf → V9 parity → PR (stacked on #1147) → QA evidence comment
→ promotion bundle: #1143 + #1147 + #1125 + this PR (#1143 first; order-independent vs #1125)
```

Hard predecessor: **PR #1143** (AR-I-3018's first-invoice pin) must promote ahead of this PR (gray 1A). Branch 2 is safe only once every memo is pinned to its first invoice; before the pin ships, a memo can still pair with a later invoice and a skip-class refund could double-pay against that application. #1143's pin commit `babdcda1` is not on main yet, but stage's live 3018 DOES run the pinned text (verified 2026-10-23 12:05: the stage DM, 8,865 B, carries the OTCM-149147 changelog and the `MIN(customer_trx_id)` first-invoice pin, pasted for #1143's QA). V7's pinned-3018 precondition is met; no 3018 paste needed.

Gate: if Tony's answers to Q1–Q5 (sent 2026-10-21) arrive and differ from the assumption, the gate wording is revisited before the stage paste.

## Panel review resolutions (2026-10-23)

12-reviewer panel (4 panels × 3 seats) + 2-seat triage + advocate/skeptic debate over the branch diff; reports and triage files under `oracle-integration-cloud/tmp/pr_otcm149784_review/` (run-id `20261023T1105`). 13 clusters; six gray findings resolved by Luis, all option A:

- **1A — Deploy order**: #1143 becomes a hard predecessor; V7 precondition "pinned 3018 text pasted on stage" (sequencing above + PR body bullet).
- **2A — Uncapped branch 2**: added the `ps.amount_due_remaining >= ps.amount_due_original` cap (overpaid-invoice and adjustment-inflated-memo over-refunds) and the outer `ps.amount_due_original < 0` credit-class guard.
- **3A — Inverted ordering**: window anchor changed to `GREATEST(MAX(last_update_date), rcta.creation_date)` so a memo born after its invoice's closure enters the next window instead of stranding forever.
- **6A — Undocumented placements**: four load-bearing placements got one-line comments in the SQL (strict gate hoisting, `display = 'Y'`, pin mirror, HAVING-only window).
- **7A — Header overstatement**: class-2 header paragraph reworded — "last balance update (a proxy for its closure)".
- **9A — Unprobed cell**: dev1 ad-hoc probe on partly-applied 34038 with the final text → 1 row, payload unchanged (post-review verification above).

Applied without code changes: **_11** PR-body disclosure bullets (D1 assumption, D3 terminology, #1143 ordering — in `tmp/pr_description.md`). Skipped: **_8** (params-CTE dedup — cosmetic), **_10**. Follow-ups, not this PR: **_4** (one-shot window / failed-refund re-selection), **_5** (pin not BU-scoped — Tony Q5), **_12** (no re-verification before the refund POST), **_13**.

## Open items

- Tony's Q1–Q5 unanswered as of 2026-10-23 12:05 (re-checked OTCM-149784 and OTCM-149147 comments: last Tony reply 2026-10-21 10:38, before the questions landed). Assumption A1 in force per D1.
- dev1 live drift (pre-OTCM-114232): noted in the PR per AC8; no separate action — the paste brings dev1 to the new text.
- OIC AR-I-3019 schedule on stage: CONFIRMED active (2026-10-23) — four organic refunds posted at 18:20/18:30 UTC by OAuth client `ec0d977d21c6460b9270430dfeee2158`, ~10 min cadence.
- The V7 QA evidence note must name the one-shot asymmetry (round-2, 10A): a memo born after its invoice's closure anchors on its immutable creation date and is strictly one-shot — a failed refund POST is recoverable only through the monocle failure path. An early-born memo can accidentally re-arm when a later invoice touch moves the closure proxy.

## Reproduction queries (stage, read-only)

```sql
-- Schedule rows for the TestTPCOLA06 fixture
SELECT t.trx_number, t.ct_reference, ps.class, ps.status,
       ps.amount_due_original, ps.amount_due_remaining,
       TO_CHAR(ps.actual_date_closed,'YYYY-MM-DD HH24:MI:SS') AS actual_date_closed,
       TO_CHAR(ps.last_update_date,'YYYY-MM-DD HH24:MI:SS')    AS last_update_date,
       TO_CHAR(ps.creation_date,'YYYY-MM-DD HH24:MI:SS')       AS created
FROM ar_payment_schedules_all ps
JOIN ra_customer_trx_all t ON t.customer_trx_id = ps.customer_trx_id
WHERE t.ct_reference = 'TestTPCOLA06'
ORDER BY t.customer_trx_id;

-- The skip: memo 33070 open with no current application
SELECT (SELECT SUM(ps.amount_due_remaining) FROM ar_payment_schedules_all ps
        WHERE ps.customer_trx_id = 300001007534218) AS memo_balance,
       (SELECT COUNT(*) FROM ar_receivable_applications_all a
        WHERE a.customer_trx_id = 300001007534218
          AND a.status = 'APP' AND a.display = 'Y') AS applications
FROM DUAL;
```
