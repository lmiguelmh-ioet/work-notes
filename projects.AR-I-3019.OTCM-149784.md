# OTCM-149784 — AR-I-3019: refund unapplied exchange credit memos stranded by the zero-balance skip

- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-149784
- **RICE**: AR-I-3019 (report `WP AP AR Credit Memo Applied Report`, DM `WP_AP_AR_CREDIT_MEMO_APPLIED_DM`)
- **Repos**: `oracle-integration-cloud` — [PR #1151](https://github.com/WarbyParker/oracle-integration-cloud/pull/1151), stacked on #1147
- **Status** (as of 2026-10-23): **ON HOLD** — PR in review (round-1 comments answered 2026-10-23, awaiting re-review), trimmed DM text live on stage + dev1, QA legs done except A5 and the V7 ad-hoc leg
- **Plan**: [projects.AR-I-3019.OTCM-149784.plan.md](projects.AR-I-3019.OTCM-149784.plan.md)

## Outcome

- In flight (on hold 2026-10-23): the skip-class door is in the DM and proven live — the stage AR-I-3019 schedule organically refunded four fixtures within minutes of eligibility.

## What shipped

- [PR #1151](https://github.com/WarbyParker/oracle-integration-cloud/pull/1151) — `WP_AP_AR_CREDIT_MEMO_APPLIED_DM.sql` (+ re-exported `.xdm.catalog`, archived from dev1, embedded query byte-identical). Stacked on #1147; merges at prod promotion bundled with #1147, after #1143.
- Live paste 2026-10-23 ~13:15: PR text `updateObject`'d onto stage AND dev1 (`/Custom/WP Integrations/FIN/Data Model/WP_AP_AR_CREDIT_MEMO_APPLIED_DM.xdm`); rollback originals at `integrations/AR-I-3019/data/OTCM-149784-qa/paste/{stage,dev1}/`.
- Review round 1 (2026-10-23): commit `61ccabb2` trims the query comments and re-exports the catalog (CDATA byte-identical, 5,628 B); trimmed text `updateObject`'d onto stage AND dev1 ~15:20 (rollback = the `b805e520` committed text); five replies posted (threads r4363912196–r4363912297).

## Decisions

### Functional clarifications (Q&A)

- Tony's Q1–Q5 on the first-invoice pin (sent 2026-10-21, OTCM-149784 comments) — UNANSWERED as of 2026-10-23; D1 assumption in force.

### Design decisions (ours)

- D1 — proceed under the first-invoice-pin assumption; gate wording follows if Tony rules differently.
- D2 — single PR stacked on #1147's branch (promotes bundled).
- D3 — "unapplied" = no CURRENT application (reversed memos eligible); never re-applies anything.
- D4 — skip-branch window anchor: `GREATEST(MAX(first-invoice last_update_date), memo creation)` + `P_LOOKBACK_MINUTES` cushion; date-only closure columns rejected (midnight trap).
- D5 — first-invoice-closed gate holds in every mode (scheduled, ad-hoc range, trx bypass).
- D6 — edit base = #1147 head (byte-identical to live stage at open).
- Panel resolutions (2026-10-23): 1A #1143 hard predecessor; 2A over-face cap + credit-class guard; 3A GREATEST anchor; 6A/7A comment wording; 9A gray-cell probe.
- Review round 1 (Johnny, 2026-10-23): header and display note dropped, cap shrunk to "Never refund more than the memo's face amount.", class-2 label tightened to one line. Class-1 label kept — the BIP editor shows only the query, so the labels are the only in-place pointer from each branch to its refund class.

## Evidence

QA artifacts: `integrations/AR-I-3019/data/OTCM-149784-qa/` (probe SQL/XML, A/B buckets, paste originals, fixture envelopes). Full narrative in the plan file.

- Read-only legs (2026-10-23): V1 A/B old-vs-new (dev1 new_only 34039/35030, stage new_only 33070, all probe-verified skip class); V2 ad-hoc probes (33070 → 1; 239003/33072 → 0); V5 lookback boundary (from T+4 selects, T+6 does not); race trio on open invoices → 0.
- Batch 1 (live stage DM): V6 Pass (33117 closed 240001; leftovers 33118/33119 selected); V3 Pass (33120 applied-then-reversed → selected; 33121 fully applied → 0).
- Batch 2 (live stage DM): V4 Pass (receipt `TestRCP149784A` closed 240003; memo 33122 born after closure → selected; creation-dominant GREATEST arm proven); bad-reading-1 Pass (240004 open + 240005 zeroed by `TestRCP149784B`; memo 33123 → 0 rows — permanent negative fixture).
- V7 organic leg Pass ×4: stage schedule (~10 min) refunded 33118 +$50 @18:20:03, 33119 +$30 @18:20:04, 33120 +$100 @18:30:14, 33122 +$100 @18:30:14 — ACTIVITY applications by OAuth client `ec0d977d21c6460b9270430dfeee2158`, exact open balances, never re-selected.
- V8 Pass: 1-day/1-month/1-year windows — stage 2.3/1.8/1.6 s, dev1 2.9/2.2/1.9 s.
- V9 Pass: re-exported catalog's embedded SQL byte-identical (7,845 B) to the PR `.sql`; `P_LOOKBACK_MINUTES` declared. Export sourced from dev1 (env churn only).
- Post-trim verification (2026-10-23, commit `61ccabb2`): live CDATA byte-identical to the trimmed `.sql` on dev1 AND stage; stage probes 33123 → 0 rows (closure gate holds) and 33070 → 1 row; dev1 window run clean; new catalog parity sha256 `3bd3d2224a520c46`, `P_LOOKBACK_MINUTES` still declared.
- QA evidence Jira comment: NOT YET POSTED (waits on A5 + V7 ad-hoc).

## Test data

- Stage `TestTPCOLA06`: memo 33070 (−50, pre-fix skip, first invoice 238001 CL) — RESERVED for the V7 ad-hoc leg; anchor behind the rolling window, stays eligible for ad-hoc naming.
- Stage `TestTPCOLA12` (permanent negative): 240004 OP $100, 240005 zeroed, memo 33123 OP −100 — schedule can never pick it up.
- Stage `TestTPCOLA13` (A5, primed): invoice 240006 OP $100, memo 33125 OP −100 with PENDING adjustments 16001 (−10) and 16002 (−2) — approving 16001 inflates it to −110; then receipt-close 240006 and probe (expect 0 rows).
- Stage TestTPCOLA07/10/11: refunded by the schedule (V7 evidence); memos CL/0.
- Dev1: 34038 (class 1, −55/−15), 34039 (skip class, −40) — A5 dev1 fallback target (adjust −2 → probe 0); dev1 denies `createAdjustment` for the integration user (WSFunctionPermission).
- Fixture tooling: `ar-i-3018-credit-memo-test-data` skill (invoice/memo scripts); receipt/adjustment envelopes at `integrations/AR-I-3019/data/OTCM-149784-qa/fixtures/`; receipt path = REST `standardReceipts` + `applyReceipt` action (RemittanceBankAccountNumber `REC00000601300257` mandatory).

## Open items

- Johnny's re-review of #1151 after the round-1 trim (commit `61ccabb2`, five replies posted 2026-10-23).
- V7 ad-hoc leg — OIC console Run Now on `WP_AR_I_3019_CRED_MEMO_REFU|01.00.0000` with `credit_memo_trx_numbers=33070` (Luis drives; no local OAuth client has ServiceInvoker — the `.env.prod` "Prod WMS Oauth Client" gets 401 at the Gen-3 design host). Verify the $50 refund lands and 33070 closes.
- A5 — an AR-rights user approves stage adjustment 16001, or posts −2 on dev1 memo 34039, or skip (guard is one SQL line, code-review covered).
- QA evidence Jira comment after those two legs (jira-qa-evidence skill: production entry point + readability rules).
- Promotion: #1143 (AR-I-3018 pin) ahead of this bundle; #1125 (OIC schedule) independent. Tony's Q1–Q5 gate #1143.
- One-shot asymmetry disclosure for the QA note (plan file, round-2 10A).

## Artifacts

- Plan: [projects.AR-I-3019.OTCM-149784.plan.md](projects.AR-I-3019.OTCM-149784.plan.md)
- Related: [PR #1143](https://github.com/WarbyParker/oracle-integration-cloud/pull/1143) (pin), [PR #1147](https://github.com/WarbyParker/oracle-integration-cloud/pull/1147) (base), [PR #1125](https://github.com/WarbyParker/oracle-integration-cloud/pull/1125) (OIC schedule), [OTCM-149147 project file](projects.AR-I-3018.OTCM-149147.md)
- Skills: `ar-i-3018-credit-memo-test-data`, `fusion-sql`, `oic-file-integration`
