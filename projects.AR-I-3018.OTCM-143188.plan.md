# OTCM-143188 — AR-I-3018: select an exchange credit memo and its invoice while the invoice still has a balance

- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-143188 (To Do, assignee Luis)
- **RICE**: AR-I-3018 — Apply Credit Memo to AR Invoice (API Approach) for B2C exchanges
- **Repos**: `oracle-integration-cloud` (data model), `monocle_integrations` (apply logic)
- **FSD**: `integrations/AR-I-3018/docs/drive/AR-I-3018 - Apply Credit memo to AR Invoice (API Approach) for B2C exchanges.md` (refreshed 2026-10-12, current; Data Selection updated 2026-10-02)
- **Status**: PR 1 implemented 2026-10-13 (best-of-2 agents; winner B + A cherry-picks: partial-warning wording, truthful cap-test name, 4-param unparseable-`invoice_amount` matrix), restructured per Luis's review (A+C: deduplicator + row-processor steps, `duplicates` naming, decrement-on-success kept — rationale in PR table), then merged `ApplyAmountResolver` into `_InvoiceBalanceTracker` (one private class in the processor module; merge and name DECIDED 2026-10-13 (Luis), details in PR table). Fast checks all green 2026-10-13 post-merge: 85 tests (package + facade factory), 100% package coverage, black/isort/flake8/mypy-strict clean. Pre-opening review panel (12/12 seats, run 20261013T1612, zero BLOCKERs) applied 2026-10-13 per Luis's picks: `is_finite` parse guard (NaN/Infinity), quantize once at resolution so the wire amount and the ledger decrement are the same value, memo remainder ≤ 0 fails the row, per-run-reset orchestrator test, `CreditMemoBalanceTrackingError` for the consume-misuse guards, row exceptions moved into the step module (out of the shared `_exceptions`), frozen `CreditMemoRowProcessingResult` + `@log_on_exception` + `__call__` docstring on the processor, dedup built per run in the orchestrator (factory back to ports-only, mirrors AR-I-3019), dedup docstring corrected and the `PENDING CONFIRMATION` marker moved onto the dedup (Q1 lives there, not on report order), `TestParseMonetaryAmount` dropped (coverage holds via the public API), test-name/typo/typing NITs. Fast checks green post-round: 92 tests, 100% coverage, black/isort/flake8/mypy-strict clean. Deploy order REVERSED 2026-10-13 (Luis, panel finding): code PRs merge/promote FIRST. PR SPLIT 2026-10-13 (Luis, split-to-prs): #2729 superseded by the 3-PR stacked series [#2730](https://github.com/WarbyParker/monocle_integrations/pull/2730) (deduplicator, +120) → [#2731](https://github.com/WarbyParker/monocle_integrations/pull/2731) (row processor, +952, stacked on #2730's branch) → [#2732](https://github.com/WarbyParker/monocle_integrations/pull/2732) (activation, +292/−317, stacked on #2731's branch); all open with `enhancement`; every branch passed fast gates + 100% coverage gate + API/streams/events before push; #2732's tree verified byte-identical to #2729's branch; #2729 close pending Luis (backup branch `OTCM-143188-apply-amount-invoice-balance` kept). Merge order: #2730 → #2731 → #2732. DM PR OPENED 2026-10-14: [#1130](https://github.com/WarbyParker/oracle-integration-cloud/pull/1130), stacked on #1064's branch, `enhancement`, commit `dacd2a2e`. DM pre-opening panel run 20261014T1005 (12/12 seats): 18 findings — 12 applied (`ps.class='CM'` memo-side, memo-level NOT EXISTS hoisted into `credit_memos`, bounded `pay_sched` scan, dead projections dropped, redundant aliases cleaned, same-currency pairing guard, header + major-changes rewrite); 2 ignored per Luis (no scoping filters on the NOT EXISTS — "a failed report over untrue data"; no display-only tweak); 1 impossible (`ra_batch_sources_all` carries no `org_id` — SET_ID-striped reference data); refund-row collision FALSIFIED on both pods (refund apps carry `status='ACTIVITY'`, never `'APP'`); 0 non-numeric DFF garbage on both pods. Every applied edit proven a no-op: committed vs edited 23/23 identical on dev1; live vs edited buckets unchanged (16/2/7/0). Luis re-pasted the query on the pods and re-exported the `.xdm.catalog`; embedded query verified byte-equal to the repo `.sql` before the amend. SOAP apply API gains two trx-id fields for ad hoc selection (SOAP API doc comment threads, Vijay 2026-10-12; confirmed for AR-I-3018 and reassigned to Luis 2026-10-14): `cred:CreditMemoTrxId` + `cred:InvoiceCustomerTrxId` pin the exact memo and invoice during transaction-number (ad hoc) selection to eliminate duplicates — handled as a NEW PR (Luis 2026-10-14), PR 5 in the split table, tracked as OI-10.

## Scope

Two workstreams, one release (per ticket):

1. **Data model** `WP_AP_AR_CREDIT_MEMO_UNAPPLIED_DM` (oracle-integration-cloud) — selection fixes:
   - (1) Drop `AND aps.amount_due_remaining = aps.amount_due_original`; keep `> 0` (invoice still has a balance).
   - (2) `NOT EXISTS` becomes memo-level: no current application at all (`app.status = 'APP' AND app.display = 'Y'`).
   - (3) `credit_memos` restricted to OMG exchange memos: join `ra_batch_sources_all bs ON bs.batch_source_seq_id = cm.batch_source_seq_id`, `bs.name = 'OMG'`, `(ABS(cm.attribute7) > 0 OR ABS(cm.attribute8) > 0)`.
   - (4) Date window matches the invoice's OR the memo's creation date (`cm.creation_date` added to the CTE).
   - (5) Accepted optional edits (Q5): `amount_applied` from `ABS(cm.amount_due_remaining)` (drops `ext_amount` CTE); `pay_sched` grouped by `class`, `'INV'` required on the invoice side.
   - (6) Deterministic `ORDER BY` (Q4): invoice trx id, memo creation date, memo trx id.
   - Repo hygiene: committed `.sql` is behind live (lacks `customer_due_amount`/`insurance_due_amount`); PR exports `.sql` + `.xdm.catalog` together.
2. **monocle** `_wp_ar_i_3018_credit_memo_application` — apply `min(due, memo remaining, invoice remaining)` (FSD error table: credit > invoice balance → apply balance, leave rest for refund) and keep a running balance per invoice within one run (one invoice can meet several memos; every report row shows the balance before any of them is applied).

Explicitly out of scope: OIC flow changes (see Open item OI-3), AR-I-3019's zero-due whole-refund (OI-5).

## Verified assumptions (2026-10-12, dev1 pod `USAHFQKJ_F` via fusion-sql)

- **A1 (edit 2 predicate)** — CONFIRMED. SOAP-applied memos (QA 15003/204001) carry `status=APP, display=Y, type=CM`; reversals flip to `display=N`; `UNAPP/N` history exists. Nuance: OMG memos also carry `ACTIVITY/Y` rows, all with `applied_customer_trx_id = NULL` — refund/activity applications, not invoice applications; they correctly do NOT block selection, and optional edit (a) keeps amounts safe in that case.
- **A2 (batch source)** — CONFIRMED. Exactly one source named `OMG` (`batch_source_seq_id` 300000876754234); join column valid both sides (174 OMG trx on dev1).
- **A3 (no OIC contract change)** — CONFIRMED. Proposed query returns the same column list the monocle reader already maps; only selection changes.
- **A4 (memo remaining == total under edit 2)** — holds by construction (no current application; OMG memos get no manual adjustments).
- **A5 (deploy order)** — monocle's new `min()` is safe against the current DM (`invoice_amount` already in the payload): untouched invoices carry their full balance, so the cap never bites — a no-op. The new DM against current monocle avoids corruption (Oracle rejects over-applications) but every such run FAILS until monocle ships. REVERSED 2026-10-13 (Luis, review-panel finding): PR 1 merges/promotes FIRST.
- **O4 (.iar freshness)** — VERIFIED 2026-10-12: repo pulled, already up to date; the Sep 11 `.iar` is the latest export. Live-flow check moves to OI-4.
- **Within-run pairing** — CONFIRMED 2026-10-13 by query shape: the reference join pairs one memo with EVERY balanced same-reference invoice, so one memo can appear on several rows in a single run (two-shipment exchange). This is a **pre-existing latent defect on our side**: the live query + orchestrator have the same exposure today (a memo paired with two untouched same-reference invoices is attempted twice; Oracle rejects the over-application and the run fails). DECIDED 2026-10-13 (Luis): the **primary fix is report-level** — PR 2's DM keeps one row per memo (`ROW_NUMBER() OVER (PARTITION BY cm.customer_trx_id ORDER BY inv.customer_trx_id) = 1`, first invoice in report order wins). PR 1 keeps a code-side pre-loop dedup as a safety net for ad hoc reruns against older report versions (comment in code says so; no ticket refs).

## Decisions — proceeding on assumption, flagged PENDING CONFIRMATION in code

| ID | Decision | Code flag |
|----|----------|-----------|
| Q1 | Strict memo-level exclusion: a memo with any current application is never selected (one memo → one invoice). | `PENDING CONFIRMATION` on the `NOT EXISTS` |
| Q3 | Non-zero ATTR7/8 selects exchange memos *with an amount to apply*; zero-due exchange memos (money-services RET-5a / FIN-7087) are excluded by design — AR-I-3019 owns them. | Design-note comment on the ATTR7/8 filter |
| Q4 | `ORDER BY` invoice trx id, memo creation date, memo trx id; monocle applies in report order, later memos absorb any shortfall. | `PENDING CONFIRMATION` on the `ORDER BY` + orchestrator note |
| Q5 | Both optional edits taken. | `PENDING CONFIRMATION` on `amount_applied` / `pay_sched` |

## Questions — exact texts and response history

Every stakeholder question for this ticket, verbatim, with where it was asked and the
dated history of responses. The Decisions table above is the summary index; this section
is the audit trail. Format follows the `rmcs-i-3001_warranty_pod_support` plan.

### Open

#### Q1 — One memo applies to one invoice (strict memo-level exclusion)

- **Context:** the reference join pairs one memo with EVERY balanced same-reference
  invoice (Within-run pairing, Verified assumptions). Round 2 question 2 (Deloitte)
  states "one memo applies to one invoice"; the strict reading excludes a memo with ANY
  current application from ever being selected again, while the alternative lets a memo
  split across several same-reference invoices. The answer decides the selection
  predicate's shape (memo-level `NOT EXISTS` vs per-invoice). = ticket open question OQ1.
- **Posted 2026-10-13** as an FSD comment on §2.2 "Data Selection and Sorting" to
  **Vijay Bellurkar + Aruna Bhairapuneni**, cc **Daniela Palacios**. Verbatim as posted
  (transcript-recovered — confirm against the Drive comment at the next FSD sync):

  > "One memo applies to one invoice" means: if one exchange order is invoiced in two shipments (two invoices, one reference), a memo already applied to the first invoice is not selected for the second. The alternative is that a memo must be splittable across several same-reference invoices. We will follow "one memo applies to one invoice": it is what prevents a memo from being applied twice when a failed memo is retried while its sibling memo succeeded (round 2 Q2(a)). This answer also decides the shape of the selection predicate (memo-level vs per-invoice). Please let us know otherwise.

- **Draft history:** the assistant's first draft ("Implementing OTCM-143188 with the
  memo-level reading of round 2 question 2: **one memo applies to one invoice**.
  Concretely: a credit memo that already has any current application (to any invoice) is
  never selected again...") was superseded by this shorter corrected version in the
  user's voice, which is what was posted, as-is.
- **Code flag:** `PENDING CONFIRMATION` on the `NOT EXISTS` (DM edit 2, PR 2).
- **Status:** awaiting functional reply.

#### Q2 — Ad hoc reruns move the scheduled window (OIC flow)

- **Deferred** out of this ticket — see OI-3. An ad hoc OIC rerun advances the
  last-successful-run watermark, so the next scheduled window can silently skip memos
  created between the two runs; belongs to the OIC flow's run-control design.

### Resolved

#### Q6a — Which flow refunds partial remainders → AR-I-3019 (resolved 2026-10-13)

- **Raised 2026-10-13 by Daniela Palacios** (Money Services, Slack), verbatim:

  > Entonces, si está en 0 se tiene que crear el credit memo pero no aplicarlo, ese credito se debe devolver mediante un payment. La lógica para detectar el pago esta en la integración de refunds. Igual, desde MS no tenemos mucho contexto de como se realiza la aplicación en Oracle, así que podría haber algún escenario que estamos omitiendo.

- Her first point matches the locked design (due = 0 → create, don't apply, refund via
  the payment flow — Q3/OI-5). Her caveat ("no context on how the application happens in
  Oracle") opened the partial-application edge case, illustrated with a Cursor-generated
  example: invoice 500 with 300 already applied (balance 200), memo due 300 → Oracle
  applies 200 and leaves 100 open on the memo; MS sees the memo's original 300 and could
  refund 300 → 200 over-refund.
- **Response log 2026-10-13:** Luis replied (1) "OK, exacto como estaba planeado" on the
  zero-due flow; (2) remainder ownership looked undefined in the FSD → planned an FSD
  comment; (3) the Deloitte Q&A documents then arrived and answered it (below).
  Daniela's follow-up cases — the exchanged item may cost more or less, and shipping can
  be pricier — split by direction: the pricier direction closes with the top-up payment;
  the cheaper direction is this question (now answered). The gross-basis sub-question
  survives as Q6c.
- **ANSWERED 2026-10-13** by the Deloitte Q&A documents (`integrations/tmp/`):
  - Round 2, header readings — Deloitte: "Your understanding is correct": "AR-I-3019
    refunds the remaining balance of a partly applied memo with an on-account credit
    memo refund, payment method `AR Refund`."
  - Round 2, Q3 — Deloitte: "Agreed. select by the FSD's rule. Memos applied to a
    same-reference invoice since the last run." AR-I-3019's FSD selection is memos
    applied to a same-reference invoice since the last run, and it "refunds the amount
    remaining after that application".
  - Round 1, Q4(c): "AR-I-3019 creates refund on the credit memo remaining balance."
- **Condition:** `WP_AP_AR_CREDIT_MEMO_APPLIED_DM` still selects by memo creation-date
  range; the round-2 Q3 fix (select by applied-since-last-run) is agreed but pending on
  the AR-I-3019 side. Until it lands, a remainder created days or weeks after the memo
  can fall outside every run's range and never be refunded.
- **Related note:** Deloitte's round-1 Q4(a) formula "Applied Amount = Min(Credit Memo
  Amount, Attribute7)" omits the invoice-balance term. The FSD "Partial Application"
  row supplies it, and Oracle never over-applies an invoice; PR 1's min-of-three is
  consistent with both.
- **Doc provenance:** 2026-10-12 Luis asked Daniela on OTCM-143188 (Jira comment id
  960259) for these documents; received 2026-10-13.

#### Q6b — Refund amount = the memo's remaining balance at refund time (resolved 2026-10-13)

- The over-refund risk from Daniela's example (refund 300 after Oracle applied 200) is
  closed by the same answers: the refund amount is "the amount remaining after that
  application" (round 2, Q3 — agreed) and "the remaining balance of a partly applied
  memo" (round 2, header — confirmed), never the original credit amount.
- **Mechanics close the gap:** AR-I-3019 creates the refund payment request in Oracle
  with that amount; AP-I-3006 announces the request; Money Services pays and
  acknowledges. MS never infers an amount from its own data, so the example's
  double-credit path does not exist in the designed flow.

#### Q6c — Due DFF amounts are gross of tax; freight excluded by design (resolved 2026-10-13)

- **Origin:** the Money Services thread under Q6a. Daniela's follow-up cases (the
  exchanged item may cost more or less, and shipping can be pricier) raised this
  sub-question: if the due DFFs exclude tax or freight, the apply amount is mis-capped
  by that delta on every exchange with tax or freight charges. The Deloitte Q&A docs do
  not state the basis ("carries its amount to apply in ATTRIBUTE7 or ATTRIBUTE8,
  whatever the direction of the exchange" — direction-neutral, basis-silent).
- **ANSWERED 2026-10-13 by implementation review — no stakeholder question needed.**
  Evidence (money-services Return and Exchange Architecture Flow,
  `integrations/tmp/return-and-exchange-architecture-flow.md`):
  - Worked example, frame B → E (even exchange): due on exchange $108.00 = $100.00
    goods + $8.00 tax (line 461). Gross.
  - Worked example, frame A → C (cheaper): due $81.00 = $75.00 goods + $6.00 tax,
    residual $27.00 (line 464). After the tax commits at $5.50: "Oracle's application
    stops at the $80.50 invoice and it refunds $27.50" — the invoice is gross, the
    application caps at its balance (line 467).
  - Rule 7: "Oracle's application is capped by the invoice's balance (AR-I-3018)" —
    the invoice-balance cap is designed behavior (line 450).
  - Tax committing differently after the memo is raised moves in money, never in the
    due: a higher commit is charged as a top-up, a lower one frees residual (rule 5,
    rule 7a; worked examples, lines 465–469). The memo's due is never revised.
  - Freight: rule 1 funds replacement lines only; shipping lines price and settle
    through the exchange order's payment methods (lines 454, 459). The due excludes
    freight by design — a freight charge on the invoice is covered by the methods'
    receipts, not by the memo.
  - Consistent with dev1: 143 DFF memos, all goods-only test data (zero taxed or
    freighted exchange invoices). The one junk row (memo 11003, ATTR8=200 against
    goods 180 + tax 15.98, NULL reference, hand-made) is synthetic, not evidence.
- **Consequence for PR 1:** the min-of-three compares gross amounts on both sides; no
  code change, no FSD comment.

### Answered / awaiting objections

Posted 2026-10-13 as ONE Jira comment on OTCM-143188 (id 960756), tagging **Daniela
Palacios**, cc **Vijay Bellurkar, Aruna Bhairapuneni, Gabriel Viera**. Framing:
"We are continuing with the following decisions ... Please let us know if something is
wrong or should be updated." No objections as of 2026-10-13.

#### Q3 — Zero-due exchange memos are excluded (AR-I-3019 owns them)

- Verbatim as posted:

  > Zero-due exchange memos are excluded by design. An exchange memo can be raised with due = 0, and those memos belong to AR-I-3019 (whole refund), never to AR-I-3018 (nothing to apply) — decided by money-services' Return and Exchange Architecture Flow (RET-5a / FIN-7087, 2026-10-02). So non-zero ATTRIBUTE7/8 is the right marker for this integration: it selects exactly the exchange memos that still owe an application.

- **Trimmed from the draft, kept for the record:** the framing line said the decisions
  were "each flagged as pending confirmation in the code", and this bullet carried a
  closing parenthetical "(AR-I-3019's \"refund a memo nothing was applied from, whole\"
  is already tracked as open Oracle-team work in the money-services doc.)". Both dropped
  by the user before posting.
- **Code flag:** the single-populated-DFF rule stays `PENDING CONFIRMATION` in the code.
- **Status:** posted as a decision; no objections as of 2026-10-13.

#### Q4 — Deterministic ORDER BY; report-order application, later memos absorb the shortfall

- Verbatim as posted:

  > ORDER BY usage. The query gets a deterministic ORDER BY (invoice trx id, memo creation date, memo trx id) and monocle applies in report order. When receipts landed first and the invoice balance cannot cover every memo's due, the later memos absorb the shortfall and the remainder stays on them for AR-I-3019 to refund. The FSD error table ("If credit > invoice balance, apply balance and leave remaining credit for Refund") does not specify which memo carries the remainder, so we apply in report order to keep runs reproducible.

- **Code flag:** the row-order comment stays `PENDING CONFIRMATION` in the code.
- **Status:** posted as a decision; no objections as of 2026-10-13. (The "remainder for
  AR-I-3019 to refund" half is now confirmed by the Deloitte docs — Q6a.)

#### Q5 — Both optional edits accepted

- Verbatim as posted:

  > Both optional edits accepted. amount_applied becomes the memo's remaining balance — equal to its total for an untouched memo, and correctly lower for a memo that was partially refunded (a selected memo has no current invoice application). And pay_sched is grouped by class, with 'INV' required on the invoice side.

- **Status:** posted as a decision; no objections as of 2026-10-13. Both edits are part
  of PR 2's DM change.

## PR split

Split executed 2026-10-13 (Luis, split-to-prs): the single code PR (#2729, superseded) became a 3-PR stacked series; the DM PR is unchanged and still last.

| PR | Repo | Contents | Lines | Depends on |
|----|------|----------|-------|------------|
| 1. [#2730](https://github.com/WarbyParker/monocle_integrations/pull/2730) `[OTCM-143188] Add AR-I-3018 credit memo row deduplicator` (base `main`) | `monocle_integrations` | `CreditMemoRowDeduplicator` + test + `_steps` export. Inert (not wired). Carries the `PENDING CONFIRMATION` marker for OI-1. MERGED 2026-10-14 (squash `d3c523c53` on `main`). | +120 | none |
| 2. [#2731](https://github.com/WarbyParker/monocle_integrations/pull/2731) `[OTCM-143188] Add AR-I-3018 credit memo row processor` (base #2730's branch) | `monocle_integrations` | `CreditMemoRowProcessor` + `_InvoiceBalanceTracker` + step-local exceptions + frozen `CreditMemoRowProcessingResult` + test. Inert (not wired). OPEN 2026-10-13, `enhancement`; base auto-retargeted to `main` after #2730 merged. Updated 2026-10-14: main merged (conflict `_steps/__init__.py` → branch version) + hardening commit `c3f9dc748` answering all 10 review threads (7 applied / 2 declined / 1 reply-only); 10/10 replies posted; gates green (7,131 unit / 100% / 335 API + 2 skips + 1 parallel flake). | +952 | #2730 |
| 3. [#2732](https://github.com/WarbyParker/monocle_integrations/pull/2732) `[OTCM-143188] Apply AR-I-3018 credit memos only while the invoice has a balance` (base #2731's branch) | `monocle_integrations` | Activation: orchestrator rewires to reader → dedup → per-run processor loop with exception routing; `_resolve_apply_amount` dropped; `get_wp_ar_i_3018_credit_memo_application` factory (mirrors AR-I-3019); facade via factory. The behavior-change PR. OPEN 2026-10-13, `enhancement`; gates green (6,973 unit / 100% / 333 API); tree byte-identical to #2729's branch. Restacked 2026-10-14 onto #2731 head `c3f9dc748` → `59e2b94bf` (one modify/delete conflict: `_resolve_apply_amount_unit_test.py`, deleted as designed); gates green (7,110 unit / 100% / 336 API + 2 skips). | +292/−317 | #2730, #2731 |
| 4. [#1130](https://github.com/WarbyParker/oracle-integration-cloud/pull/1130) `[OTCM-143188] AR-I-3018: Select unapplied credit memos for invoices with a balance` (base #1064's branch) | `oracle-integration-cloud` | Edits (1)–(7) + panel hardening: `ps.class='CM'` memo-side, memo-level NOT EXISTS hoisted into `credit_memos`, `pay_sched` bounded (`class IN ('INV','CM') AND amount_due_remaining <> 0`), dead projections dropped (`SUM(amount_due_original)`, `cm.org_id`), same-currency pairing guard, header + major-changes comment block. (7): one row per memo via `ROW_NUMBER() OVER (PARTITION BY cm.customer_trx_id ORDER BY inv.customer_trx_id) = 1` — primary fix for Within-run pairing. OPEN 2026-10-14, `enhancement`, commit `dacd2a2e` (`.sql` + re-exported `.xdm.catalog` together; catalog embeds the exact query, verified). | +127/−59 SQL + binary | #1064; #2730–#2732 promoted; merges at PROD promotion (repo rule) |
| 5. TBD `[OTCM-143188] ...` | `monocle_integrations` (TBD) | Support the new SOAP apply API trx-id fields (`cred:CreditMemoTrxId`, `cred:InvoiceCustomerTrxId`) on the ad hoc `Transaction_Number` path — pin the memo and invoice by id so duplicate transaction-number selection cannot double-apply. NEW PR decided 2026-10-14 (Luis); scope TBD pending code read of the ad hoc path (OI-10). | TBD | TBD (likely #2732's activation) |

Sequencing: DECIDED 2026-10-13 (Luis; reversed same day after the review panel, see A5): the code PRs merge/promote FIRST — old DM + new monocle is a safe no-op, while new DM + old monocle fails every run that selects a partly-paid invoice until the code ships. Code merge order: #2730 → #2731 → #2732 (stacked; GitHub retargets each child as parents merge). Until the DM PR lands, the code dedup is the primary guard for Within-run pairing; after it, the safety net for old-DM reruns. The DM PR carries the live BIP editor change (re-pasted on the pods by Luis 2026-10-14) and the re-exported catalog. Stage QA needs BOTH on stage: monocle stage deploy (vstage tag) + DM updated on the stage pod.

## Verification plan

1. **Pre-BIP query validation (dev1)** — DONE 2026-10-14 (draft `/tmp/ar_i_3018_dm/new_query_draft.sql`, via fusion-sql on `fa-evdi-dev1` / `USAHFQKJ_F`):
   - Syntax + shape: 23 rows = 23 distinct memos (`ROW_NUMBER() = 1` holds); ~2 s runtime.
   - OMG-only: 0 non-OMG memos; zero-due: 0 rows with `invoice_amount <= 0`; applied: 0 memos with `APP/Y` application rows.
   - OR-window proven with pair invoice 53051 (created 10-04) / memo 34043 (created 10-03): window covering only the memo day → row appears; only the invoice day → appears; neither → gone.
   - Delta vs old predicates, same window: old set 18 rows / 18 memos → new 23 / 23 (+5, the partly-paid-invoice class; sample 51272: invoice balance 42.4 vs memo 100.7).
   - `ROW_NUMBER` dedup not data-exercised (no multi-invoice memo on dev1 now); the guarantee is structural.
   - Schema re-verified: single `OMG` batch source, same id as stage (300000876754234); all referenced columns queryable.
   - Note: `<= CAST(:P_TO_DATE AS DATE)` excludes rows created after midnight on the to-date — the live DM has the identical predicate, so parity is exact (not a regression; a same-day from/to run returns nothing, today and after the change).
   - Reconciliation 2026-10-14 (three-way, per the new freshness gate in the `oic-integration-lookup` rule): dev1 live (lastModified 2026-08-17) == stage live (2026-09-21), byte-identical; repo `.sql` (Sep 11) is stale vs BOTH pods by exactly 5 lines — live adds `ABS(cm.attribute7/attribute8)` as `customer_due_amount`/`insurance_due_amount` in the CTE, re-selected by alias in the main SELECT; live KEEPS `trx_reference` (output fieldOrder 12); no live `ORDER BY`; date params `xsd:date` (`MM-dd-yyyy HH:mm:ss`). Final query = live text verbatim + edits (1)–(7) at `/tmp/ar_i_3018_dm/new_query_final.sql`; repo `.sql` write REVERTED 2026-10-14 pending Luis's explicit authorization (new gate). Gate run 2026-10-14: origin/main fetched — repo file == origin/main (last touch 524ef754, #974); **open PR [#1064](https://github.com/WarbyParker/oracle-integration-cloud/pull/1064) `[OTCM-136241] AR-I-3018: Add credit memo DFF amounts to unapplied DM` carries exactly the repo↔live delta** (+5/−1 on the `.sql` + the `.xdm.catalog` + the report `.xdo.catalog`) — the live pods got the DFF columns under that ticket (dev1 lastModified 2026-08-17 == PR's last update; stage 2026-09-21) and it awaits PROD promotion. #1125 (AR-I-3019) confirmed no overlap. PR-strategy decision for Luis: our DM PR absorbs #1064 (close it as superseded) or stacks after it.
   - A/B old-vs-new (`compare_sql_variants.py`, fusion-sql skill; OLD = live stage text, NEW = repo `.sql`; key = memo+invoice trx id). dev1, window 2026-09-01→10-14: old 18 rows, new 23; **16 identical, 0 value diffs** (incl. `amount_applied` parity lines-sum ↔ schedule); losses 2/2 classified (OMG memos with `attribute7=0`/NULL dues — the AR-I-3019 class; one case shows the dues filter picking the dues-bearing sibling memo 34039 over zero-dues 34038 on reference TP1GPVG0GA); gains 7/7 classified (partly-paid invoices, original 100.7–195 → remaining 95/57.31; zero APP rows on their memos). Stage, same + wide window: old 1 (Manual-source seed `ARI3018-SEED`, NULL dues — correctly lost), new 2 (TP-class, partly-paid 195→95 and 95→57.31 — correctly gained); no identical rows in current stage data. No unexplained diff anywhere.
   - Post-panel re-validation 2026-10-14 (the 12 applied edits must be no-ops): committed vs edited — dev1 **23 identical / 0 / 0 / 0**. Live vs edited — dev1 16/2/7/0 (regression buckets unchanged). Stage compare now vacuous: a test run applied the only 2 eligible stage memos (5001/4002; invoices 7027/7024 closed at $0) within the hour after the morning A/B — the morning stage buckets (0/1/2, classified) stand as the stage evidence. Dedup exercise probe (dev1): 25 of 26 OMG-memo references with open invoices have exactly one; one reference has two.
2. **monocle unit**: step min-of-three, memo cap, invoice cap, parse errors, both/neither dues; orchestrator running balance across several memos on one invoice, decrement only on success, failure leaves balance, report-order processing.
3. **Stage QA** (ACs, evidence via `jira-qa-evidence` skill): TP46T5G015 scheduled + ad hoc (`Transaction_Number=3002`); pricier exchange with top-up applied first; cheaper exchange; memo exceeding the balance of an invoice with prior partial payments → partial apply, remainder stays open for AR-I-3019 (the Q6a flow); two memos one failing; non-OMG / zero-due never selected; unapplied-by-hand re-selected; FSD Testing Strategy cases 1–5 and 13.

## Open items

- **OI-1 (Q1) — pending functional confirmation.** POSTED 2026-10-13 as-is: FSD comment on §2.2 "Data Selection and Sorting" to **Vijay Bellurkar + Aruna Bhairapuneni** (cc **Daniela Palacios**). Daniela replied 2026-10-13 cc'ing **Tony Huang**; no substantive answer yet. Awaiting functional reply; the code keeps the `PENDING CONFIRMATION` marker (on `CreditMemoRowDeduplicator`, the unit the answer would change) until answered. Verbatim text + draft history: Questions → Q1.
- **OI-2 (Q3+Q4+Q5) — inform decisions.** POSTED 2026-10-13 on OTCM-143188 (comment id 960756; tagging **Daniela Palacios**, cc **Vijay Bellurkar, Aruna Bhairapuneni, Gabriel Viera**), closing with "Please let us know if something is wrong or should be updated." Verbatim text + trimmed bits: Questions → Q3–Q5.
- **OI-3 (Q2) — DEFERRED, out of this ticket.** Sep 11 `.iar` shows a linear OIC flow (`GetLastRunDate` → REST → `UpdateLastRunDate`, no `Transaction_Number` branch): an ad hoc rerun can move the scheduled window and skip a slice. Propose a follow-up ticket: verify the live flow branches or not, and if not, skip the last-run update when `Transaction_Number` is present. Owner: Oracle tech team / Daniela to triage.
- **OI-4 — Stage pod credentials.** RESOLVED 2026-10-14: `.env.stage` (refreshed) returns HTTP 200 from `fa-evdi-test` (`receivablesInvoices` probe); BIP v2 CatalogService also works (folder listing + `downloadObject`). Was: HTTP 401 on 2026-10-12.
- **OI-5 — AR-I-3019 zero-due whole-refund.** Money-services doc flags "AR-I-3019 must refund a memo nothing was applied from, whole" as open Oracle-team work; not this ticket, but prod go-live of the exchange flow waits on it — surface to the team. Round-2 follow-up #10 (2026-10-09, `integrations/tmp/Money-services refund_return_exchange round 2.md`) asks the same ("Does AR-I-3017 accept ATTRIBUTE7 = 0? Should we refund it in full ourselves, as in Q7?") — still unanswered in the received docs.
- **OI-6 — integrations repo sync leftovers.** Unstaged from the 2026-10-12 refresh: `catalog.yml` (`comments: true` for AR-I-3018), `manifest.json`, FSD image renames, 6 comment sidecars. Commit per house routine (not part of any PR).
- **OI-7 — Daniela's caveat: refund-side ownership of partial remainders.** RESOLVED 2026-10-13: AR-I-3019 refunds a partly applied memo's remaining balance (Q6a), the refund amount is the remaining balance after application (Q6b) — pending the round-2 Q3 fix on `WP_AP_AR_CREDIT_MEMO_APPLIED_DM` (AR-I-3019 side) — and the due DFFs are gross of tax, with freight excluded by design (Q6c, money-services architecture-flow worked examples; implementation review, no stakeholder question needed). Verbatim answers + evidence: Questions → Q6a/Q6b/Q6c.
- **OI-8 (DM review, 2026-10-14) — dedup survivor rule: "which invoice gets the money".** POSTED 2026-10-14 by Luis on OTCM-143188 — the only one of the three review assumptions that needed a new ticket comment. A memo matching several open same-reference invoices applies to the lowest-id invoice (in practice the oldest); if the intent is earliest-created, the selection order changes to creation date, then id. Awaiting money-services. The other two assumptions already had their own threads: memo-level exclusion = OI-1 (FSD comment), apply order = report order = OI-2 (comment 960756); the DM keeps both `PENDING CONFIRMATION` markers.
- **OI-9 (DM review, 2026-10-14) — FSD §2.2 gaps.** Recorded here only — the ticket comment that would have carried them was dropped 2026-10-14 (Luis). Bullet 2 still invoice-level ("not yet been applied to it") vs the implemented memo-level rule; section titled "Data Selection and Sorting" carries no sort keys (implemented: invoice trx id, memo creation date, memo trx id); the dedup rule and its survivor rule are absent. Raise with functional at the next FSD update; owner: money-services / Deloitte doc owners.
- **OI-10 (new, 2026-10-14) — SOAP apply API: two trx-id fields for ad hoc selection; NEW PR (PR 5).** Vijay added `cred:CreditMemoTrxId` and `cred:InvoiceCustomerTrxId` to the Credit Memo application SOAP request — one comment thread per field on the SOAP API doc, 2026-10-12, assigned to Tony Huang, verbatim (both threads): "Added these two api fields to eliminate any duplicates during transaction number selection. Logic to derive trx IDs: `select customer_trx_id from ra_customer_trx_all where trx_number = '3002' and ct_reference = 'TP46T5G015'`". Tony Huang asked which integration it affects ("tentatively AR-I-3018?"); Vijay confirmed 2026-10-14 ("Yes it is for AR-I-3018") and reassigned both threads to Luis. Handling: NEW PR (Luis, 2026-10-14) — PR 5 in the split table; scope TBD pending a read of the ad hoc `Transaction_Number` path (likely: pin invoice/memo by id instead of number; adjacent to OI-3's ad hoc rerun concerns). Source: SOAP API doc sidecar (`integrations/AR-I-3018/docs/drive/Credit Memo application against AR Invoice - SOAP API.comments.md`, re-synced 2026-10-14 after the sandbox blocked rclone's token save and the comments API 401'd).
