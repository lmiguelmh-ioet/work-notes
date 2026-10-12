# OTCM-143188 — AR-I-3018: select an exchange credit memo and its invoice while the invoice still has a balance

- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-143188 (To Do, assignee Luis)
- **RICE**: AR-I-3018 — Apply Credit Memo to AR Invoice (API Approach) for B2C exchanges
- **Repos**: `oracle-integration-cloud` (data model), `monocle_integrations` (apply logic)
- **FSD**: `integrations/AR-I-3018/docs/drive/AR-I-3018 - Apply Credit memo to AR Invoice (API Approach) for B2C exchanges.md` (refreshed 2026-10-12, current; Data Selection updated 2026-10-02)
- **Status**: plan drafted 2026-10-12, awaiting approval; implementation not started

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

Explicitly out of scope: OIC flow changes (see Open item OI-4), AR-I-3019's zero-due whole-refund (OI-6).

## Verified assumptions (2026-10-12, dev1 pod `USAHFQKJ_F` via fusion-sql)

- **A1 (edit 2 predicate)** — CONFIRMED. SOAP-applied memos (QA 15003/204001) carry `status=APP, display=Y, type=CM`; reversals flip to `display=N`; `UNAPP/N` history exists. Nuance: OMG memos also carry `ACTIVITY/Y` rows, all with `applied_customer_trx_id = NULL` — refund/activity applications, not invoice applications; they correctly do NOT block selection, and optional edit (a) keeps amounts safe in that case.
- **A2 (batch source)** — CONFIRMED. Exactly one source named `OMG` (`batch_source_seq_id` 300000876754234); join column valid both sides (174 OMG trx on dev1).
- **A3 (no OIC contract change)** — CONFIRMED. Proposed query returns the same column list the monocle reader already maps; only selection changes.
- **A4 (memo remaining == total under edit 2)** — holds by construction (no current application; OMG memos get no manual adjustments).
- **A5 (deploy order flexible)** — monocle's new `min()` is safe against the current DM (`invoice_amount` already in the payload); the new DM is safe against current monocle (same columns).
- **O4 (.iar freshness)** — VERIFIED 2026-10-12: repo pulled, already up to date; the Sep 11 `.iar` is the latest export. Live-flow check moves to OI-4.

## Decisions — proceeding on assumption, flagged PENDING CONFIRMATION in code

| ID | Decision | Code flag |
|----|----------|-----------|
| Q1 | Strict memo-level exclusion: a memo with any current application is never selected (one memo → one invoice). | `PENDING CONFIRMATION` on the `NOT EXISTS` |
| Q3 | Non-zero ATTR7/8 selects exchange memos *with an amount to apply*; zero-due exchange memos (money-services RET-5a / FIN-7087) are excluded by design — AR-I-3019 owns them. | Design-note comment on the ATTR7/8 filter |
| Q4 | `ORDER BY` invoice trx id, memo creation date, memo trx id; monocle applies in report order, later memos absorb any shortfall. | `PENDING CONFIRMATION` on the `ORDER BY` + orchestrator note |
| Q5 | Both optional edits taken. | `PENDING CONFIRMATION` on `amount_applied` / `pay_sched` |

## PR split

| PR | Repo | Contents | Est. lines | Depends on |
|----|------|----------|-----------|------------|
| 1. `[OTCM-143188] Cap AR-I-3018 apply amount by invoice balance with per-run tracking` | `monocle_integrations` | `ApplyAmountResolver` step class (replaces bare `resolve_apply_amount`): `min(due, memo remaining, invoice remaining)`; orchestrator owns per-invoice running-balance tracker, decrements only on successful application; unit tests (100% coverage gate). No port/API changes. | ~320 (≈40% code / 60% tests) | none |
| 2. `[OTCM-143188] Update WP_AP_AR_CREDIT_MEMO_UNAPPLIED_DM selection for invoices with a balance` | `oracle-integration-cloud` | Edits (1)–(6) in the live BIP data model on the stage pod, then export `.sql` + `.xdm.catalog` together. | ~95 SQL + binary | Live BIP edit on stage; merges at PROD promotion (repo rule) |

Sequencing: PR 1 first (fully in our control; inert-safe against the current DM per A5). PR 2 needs the live BIP editor change before export. Stage QA needs BOTH on stage: monocle stage deploy (vstage tag) + DM updated on the stage pod.

## Verification plan

1. **Pre-BIP query validation (dev1)**: run the new query through the fusion-sql arbiter before touching the BIP editor — syntax, TP46T5G015-class rows appear, APP/Y memos excluded, zero-due excluded, OR-window works.
2. **monocle unit**: step min-of-three, memo cap, invoice cap, parse errors, both/neither dues; orchestrator running balance across several memos on one invoice, decrement only on success, failure leaves balance, report-order processing.
3. **Stage QA** (ACs, evidence via `jira-qa-evidence` skill): TP46T5G015 scheduled + ad hoc (`Transaction_Number=3002`); pricier exchange with top-up applied first; cheaper exchange; two memos one failing; non-OMG / zero-due never selected; unapplied-by-hand re-selected; FSD Testing Strategy cases 1–5 and 13.

## Open items

- **OI-1 (Q1) — pending functional confirmation.** FSD comment anchored on §2.2 "Data Selection and Sorting" (the new selection bullet). Ask: **Vijay Bellurkar, Aruna Bhairapuneni** (cc **Daniela Palacios**). Text: implementing with the memo-level reading of round 2 Q2(a): a memo with ANY current application is excluded — one memo applies to one invoice, so a memo already applied to one shipment's invoice of a two-shipment exchange is not selected for the other. Proceeding on this reading because it prevents double-applying a sibling memo after a failed-then-retried run; please confirm, or say if a memo must be splittable across same-reference invoices. Why it matters: it decides the `NOT EXISTS` shape (memo-level vs per-invoice).
- **OI-2 (Q3+Q4+Q5) — inform decisions.** One Jira comment on OTCM-143188 tagging **Daniela Palacios** (+ **Vijay Bellurkar** for Q4 visibility). Text: (Q3) non-zero ATTR7/8 = exchange memo with an amount to apply; zero-due memos excluded by design (money-services RET-5a/FIN-7087, decided 2026-10-02) — they belong to AR-I-3019; no action needed, recording the decision. (Q4) `ORDER BY` added (invoice, memo creation, memo id); monocle applies in report order — when receipts landed first, later memos absorb the shortfall and stay for AR-I-3019; the FSD error table does not specify which memo carries the remainder. (Q5) both optional edits taken; `amount_applied` is now the memo's remaining balance (equals total for any selected memo).
- **OI-3 (Q2) — DEFERRED, out of this ticket.** Sep 11 `.iar` shows a linear OIC flow (`GetLastRunDate` → REST → `UpdateLastRunDate`, no `Transaction_Number` branch): an ad hoc rerun can move the scheduled window and skip a slice. Propose a follow-up ticket: verify the live flow branches or not, and if not, skip the last-run update when `Transaction_Number` is present. Owner: Oracle tech team / Daniela to triage.
- **OI-4 — Stage pod credentials.** `.env.stage` returned HTTP 401 from `fa-evdi-test` on 2026-10-12; refresh before stage QA (dev1 works).
- **OI-5 — AR-I-3019 zero-due whole-refund.** Money-services doc flags "AR-I-3019 must refund a memo nothing was applied from, whole" as open Oracle-team work; not this ticket, but prod go-live of the exchange flow waits on it — surface to the team.
- **OI-6 — integrations repo sync leftovers.** Unstaged from the 2026-10-12 refresh: `catalog.yml` (`comments: true` for AR-I-3018), `manifest.json`, FSD image renames, 6 comment sidecars. Commit per house routine (not part of any PR).
