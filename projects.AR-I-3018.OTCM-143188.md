# OTCM-143188 — AR-I-3018: select an exchange credit memo and its invoice while the invoice still has a balance
- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-143188
- **RICE**: AR-I-3018 (refund side: AR-I-3019)
- **Repos**: `monocle_integrations` (PR 1), `oracle-integration-cloud` (PR 2, data model)
- **Status** (as of 2026-10-15): code stack fully merged — #2730, #2731, and #2732 MERGED (last: squash `f4d548b09`, 2026-10-15 evening, after a conflict-only midday merge `a0a3e83ca` with 2 resolutions byte-identical to the PR side); DM PR #1130 MERGED BY ERROR 2026-10-15 into the #1064 stack branch and reverted via #1133 (branch content unchanged); both Bugbot threads answered with evidence + resolved before the merge; successor [#1134](https://github.com/WarbyParker/oracle-integration-cloud/pull/1134) OPEN from the same DM branch (the squash merge kept its commits outside the base ancestry, so the full original diff shows); `ORDER BY` marker reworded to lowercase `tacitly accepted`, gained `:P_CT_REFERENCE` ad hoc scoping (`.sql` `611f123b` + re-exported `.xdm.catalog` `81f87d71`); PR 5 = [#2746](https://github.com/WarbyParker/monocle_integrations/pull/2746) OPEN (`exchange_order_reference` pass-through + LocalStack mock scoping); contract-tests PR 8 = [#2747](https://github.com/WarbyParker/monocle_integrations/pull/2747) OPEN (three reference-scoped cases; constants repointed 2026-10-15 to the self-owned stage fixture TestTPCOLA01/234001/29043 in `1b2ed8644` — CI green both ways, live pass with a fixture present and skips after the 17:20Z stage drain; fixture revived 18:49Z the same day via SOAP unapply — report-eligible again with a creation_date permanently behind the flow's sliding window); PR 7 dropped (out of ticket scope)
- **Plan**: [projects.AR-I-3018.OTCM-143188.plan.md](projects.AR-I-3018.OTCM-143188.plan.md)

## What AR-I-3018 does (plain terms)

### The business context

Warby Parker lets customers exchange products. The order system (OMG) records each exchange in Oracle Fusion Accounts Receivable (AR) as a credit memo. A credit memo holds money for the customer. The credit memo and the original invoice carry the same transaction reference (`ct_reference`).

Oracle does not net a credit memo against its invoice by itself. Someone must apply the credit memo to an open invoice. Until then, AR shows two open items: the full invoice as unpaid, and the credit memo as open credit. The books overstate what customers owe. Finance applies these credit memos by hand.

### What the integration does

AR-I-3018 applies exchange credit memos from OMG to open invoices automatically. It has two parts.

1. The report. The BIP data model `WP_AP_AR_CREDIT_MEMO_UNAPPLIED_DM` finds unapplied credit memos. It pairs each credit memo with an open invoice on the same transaction reference. It returns one row per credit memo.
2. The integration. The monocle Lambda `wp_ar_i_3018_credit_memo_application` reads the report rows. For each row, it computes the amount to apply. The amount never exceeds the invoice balance. It then applies the credit memo to the invoice in Oracle. Within one run, it tracks each invoice balance and stops when the balance reaches zero.

### Why OTCM-143188

The old report accepted only fully unpaid invoices. A partly-paid invoice blocked its credit memos. Those credits sat unapplied until finance fixed them by hand. The new report also accepts partly-paid invoices. A memo-level check skips credit memos that already have a current application. The report returns rows in a deterministic order. The integration applies each credit memo once, only while the invoice has a balance.

## Invoice, credit memo, and discount

- An invoice says "the customer owes us $150". It increases Accounts Receivable.
- A credit memo is a negative invoice. It says "the customer owes us $150 less". It decreases Accounts Receivable. No cash moves when one is created. Think of store credit: you return an item, and the store hands you a paper that deducts from what you owe instead of cash back.
- A discount reduces the price at sale time. The invoice is simply smaller. Nothing open appears in AR.

| | Discount | Credit memo |
|---|---|---|
| When | At sale time, before the invoice | After the sale, as a reversal |
| What exists | Nothing standalone | A document with its own open (negative) balance |
| In AR | Nothing to settle | An open item to apply, refund, or write off |

### Examples

- **Invoice.** A customer buys glasses for $150. Oracle creates an invoice: the customer owes $150. Accounts Receivable grows by $150. The customer pays $150. The invoice closes.
- **Discount.** A customer buys the same $150 glasses with a 20% promo. The invoice is $120 from the start. Accounts Receivable grows by $120. The customer pays $120. No other document exists.
- **Credit memo.** A customer returns $150 glasses and orders $180 glasses in exchange. OMG creates a $150 credit memo. The $180 invoice stands open. The credit memo applies to the invoice. The invoice balance drops to $30. The customer pays $30, not $180. No refund moves.

Applying a credit memo nets it against a specific invoice. The invoice balance drops. The credit memo is consumed. The customer pays the difference. Cash moves only if the credit gets refunded instead.

In the exchange flow, the net effect resembles a discount. The mechanics differ: the store honors the full price of item B and separately honors the return of item A. The credit memo is the bridge between the two events. Credit memos carry `amount_due_remaining < 0` for this reason: their open balance is the mirror image of an invoice's positive balance.

### Why one memo applies to one invoice here (and not in general)

In Oracle AR generally, a credit memo works like store credit. It can be applied in slices to many of the customer's invoices until the balance runs out. Example: a $150 memo pays $100 of a glasses invoice, and the remaining $50 later pays part of a sunglasses invoice. Oracle supports this natively.

AR-I-3018 narrows that freedom by design, because it is the exchange flow, not general credit management:

- **Same order only.** The memo pairs only with invoices that carry the same transaction reference (`ct_reference`) — the same exchange order. It never touches unrelated invoices of the customer.
- **One memo, one invoice.** The report emits one row per memo, paired with one invoice. The integration applies each memo once.
- **The remainder is refunded, not kept as credit.** If the memo exceeds the invoice balance, the leftover stays on the memo, and AR-I-3019 refunds real money to the customer's payment method. The exchange closes value-neutral instead of leaving floating store credit.

The split-shipment edge case exposes the tension. One exchange order can produce two invoices ($100 + $50). The strict rule applies the $150 memo to the first ($100) and refunds $50, which leaves the second invoice open — odd for an even exchange. The Oracle-natural alternative splits the memo across both invoices. The FSD §2.2 comment asks money-services which rule holds (posted 2026-10-13, OI-1). If the answer is "split", the report dedup and the memo-level exclusion change shape, and the integration allows several applications per memo.

The edge is rare in practice. On dev1 (2026-10-14), 25 of 26 OMG-memo references with open invoices have exactly one open invoice; one reference has two. Stage is fully 1:1. Test pods understate the prod rate (backorders and multi-item exchanges are more common in prod), but one-exchange-one-invoice is clearly the dominant flow. The dedup and survivor rules exist for the deviations: several invoices on one reference, and the mirror case of several memos on one reference (supported by design through the running balance).

## Outcome
- Code-side enforcement merged to `main` as the stacked PRs #2730 → #2731 → #2732 (last: #2732 squash `f4d548b09`, 2026-10-15): a memo never applies more than the invoice still owes, even when several memos meet one invoice in a single run. Stage/prod promotion pending (vstage tag).
- Deploy order decided: the monocle change merges and promotes first, the data-model change second.

## What shipped
- [PR #2729](https://github.com/WarbyParker/monocle_integrations/pull/2729) — CLOSED unmerged 2026-10-14; split into the three-PR stack below.
- [PR #2730](https://github.com/WarbyParker/monocle_integrations/pull/2730) — `[OTCM-143188] Add AR-I-3018 credit memo row deduplicator` — MERGED 2026-10-14 (squash `d3c523c53` on `main`).
- [PR #2731](https://github.com/WarbyParker/monocle_integrations/pull/2731) — `[OTCM-143188] Add AR-I-3018 credit memo row processor` — OPEN, base retargeted to `main`. Updated 2026-10-14: merged main (conflict in `_steps/__init__.py` resolved to the branch version) + hardening commit `c3f9dc748` answering all 10 review threads (7 applied: sub-cent ROUND_DOWN-at-parse fix, processor logging restructure, test naming/AAA/fixture dedup, new mapping + gl_date + consume-spy tests; 2 declined with rationale: tracker injection, `_resolve_apply_amount` duplication; 1 reply-only: `amount_applied` is the wire name). 10/10 replies posted.
- [PR #2732](https://github.com/WarbyParker/monocle_integrations/pull/2732) — `[OTCM-143188] Apply AR-I-3018 credit memos only while the invoice has a balance` — MERGED 2026-10-15 (squash `f4d548b09` on `main`), stacked on #2731. Merge order: #2730 → #2731 → #2732. Updated 2026-10-15: `346e99e94` injects the deduplicator + a processor factory (orchestrator tests rewritten routing-only, ~200 lines of double-duty tests dropped); `29cf5e829` adds the dedicated in-loop abort handler (logs the in-flight row plus applied/failed/zero-balance rows, real exception text in the message, dict lists as the primary log storage). All 4 review threads applied, 4/4 replies posted. 2026-10-15: `37b345627` fixes the CI lint failure — mypy strict rejected the route unit test (zero branch diff) after `29cf5e829` typed `applied_credit_memos` as dicts; the test now builds dicts. Gates green (check-format-parallel on 3,428 files; 7,094 unit at 100%); pushed. Merge-day: conflict-only merge `a0a3e83ca` (2 conflicts vs main's #2731 squash, both byte-identical to the PR side) + three main-tracking merges (`c6e06b880`, `eb373d7d7`, `13ef97fbe`); final diff 9 files +278/−469.
- [PR #1130](https://github.com/WarbyParker/oracle-integration-cloud/pull/1130) — `[OTCM-143188] AR-I-3018: Select unapplied credit memos for invoices with a balance` — OPEN 2026-10-14, stacked on [PR #1064](https://github.com/WarbyParker/oracle-integration-cloud/pull/1064)'s branch, label `enhancement`. Commit `dacd2a2e` (amended after the review-panel edits: `ps.class = 'CM'` memo-side, hoisted memo-level NOT EXISTS, bounded `pay_sched` scan, dropped dead projections, same-currency pairing guard; re-exported catalog embeds the edited query, verified byte-equal). A/B proofs: committed vs edited 23/23 identical on dev1; live vs edited 16/2/7/0 = the approved regression buckets. Updated 2026-10-15: `a11e4431` rewords the `ORDER BY` marker to lowercase `tacitly accepted`; `611f123b` adds the optional `:P_CT_REFERENCE` parameter scoping ad hoc `:P_TRX_NUMBER` selection to one exchange reference; `81f87d71` re-exports the catalog so the `.sql` + `.xdm.catalog` pair lands together. Both pods carry the new text live (pasted 2026-10-15, verified byte-identical). 2026-10-15 incident: merged by error into the #1064 stack branch (squash `b39f4aba`) and reverted by #1133 (`62a06a2e`); the base branch content is unchanged and both Bugbot threads were answered with evidence and resolved before the merge. A merged PR cannot be reopened, so #1130 is superseded by #1134.
- [PR #1134](https://github.com/WarbyParker/oracle-integration-cloud/pull/1134) — `[OTCM-143188] AR-I-3018: Select unapplied credit memos for invoices with a balance` — OPEN 2026-10-15, successor to #1130 from the same DM branch and base, label `enhancement`. The squash merge kept the original commits outside the base ancestry, so the PR shows the full original diff; the body links #1130 for the review history and the resolved Bugbot threads. The stale `revert-1130-...` branch was deleted.
- [PR #2746](https://github.com/WarbyParker/monocle_integrations/pull/2746) — `[OTCM-143188] Scope ad hoc credit memo selection to the exchange order reference` — OPEN 2026-10-15 from `main`, label `enhancement`, commits `9051a5f62` + `f347a7e5b` (+249/−25). The port request gains optional `ct_reference`; the reader sends `P_CT_REFERENCE` with `P_TRX_NUMBER`; the route accepts `exchange_order_reference` and normalizes before dispatch (blank reference 400s, reference-without-number 400s, blank number falls through); the LocalStack mock filters `P_CT_REFERENCE` and the API suite pins the cross-business-unit collision case. Pre-opening panel (12 seats, run `20261015T1029`) applied: normalize-then-branch, blank/precedence matrix, factory truthiness, mock scoping. Deploy order: #1130's DM promotes first — BIP rejects unknown parameters.
- [PR #2747](https://github.com/WarbyParker/monocle_integrations/pull/2747) — `[OTCM-143188] Add AR-I-3018 contract tests for reference-scoped ad hoc selection` — OPEN 2026-10-15 from `main`, label `enhancement` (plan row 8). Three cases on live stage fixtures (memos 28018/28021 on invoice 16062, references TPG5CXG16A/TPG5CZ0010): memo+reference → {28018}, invoice+reference → {28018,28021}, wrong reference → zero rows (`G_1` absent). Live execution defers to CI — no local `ORACLE_OAUTH_*` credentials. Updated 2026-10-15: `1b2ed8644` repoints the constants to the self-owned stage pair (memo 29043 on invoice 234001, reference TestTPCOLA01, wrong-reference TestTPCOLA99) after Vijay's fixture proved shared mutable data. CI: live pass 17:05Z on the borrowed fixture (60p/28s, exact memo sets matched); green-with-skips 17:35Z after an AR-I-3018 stage run applied our pair at 17:20Z (57p/31s).

## Decisions

### Functional clarifications (Q&A)
1. Rows apply in report order; when the balance cannot cover every memo, the later memos absorb the shortfall — posted as a decision by Luis (Jira comment 960756, 2026-10-13); no objections as of 2026-10-13.
2. Zero-due memos are excluded from the report selection and stay for AR-I-3019 to refund whole — same comment.
3. Both optional data-model edits (one row per memo, invoice-balance filter) accepted — same comment.
4. AR-I-3019 refunds a partly applied memo's remaining balance; the refund amount is the balance left after application; the due DFFs are gross of tax with freight excluded — implementation review, no stakeholder question needed (2026-10-13; verbatim in plan → Q6a/Q6b/Q6c).

### Design decisions (ours)
1. The primary fix for one memo pairing with several same-reference invoices is report-level (`ROW_NUMBER() = 1` in PR 2's data model); the code dedup is the safety net (Luis, 2026-10-13).
2. Row outcomes are exceptions, not status returns; the row processor returns a frozen result dataclass on success (Luis, 2026-10-13).
3. `_InvoiceBalanceTracker` merges the apply-amount resolver and the balance tracker; `consume` decrements only after a successful apply (Luis, 2026-10-13).
4. Deploy order: PR 1 merges first. New code on the current report is a no-op; the new report on the old code fails every run that selects a partly paid invoice (Luis, 2026-10-13; reversed an earlier same-day decision after the pre-opening review panel).
5. Row exceptions live in the step module, not the shared `_exceptions` namespace (Luis, 2026-10-13).
6. The DM change rides its own branch stacked on #1064's branch, as a second PR — not a commit onto #1064 itself. Each ticket keeps its own SOX-clean PR, and #1064 stays untouched (Luis, 2026-10-14).
7. Two independent agents rewrote the DM query with a minimal-change mandate; solution A was adopted. A drops the dead `ext_amount` CTE. Its hidden existence filter is vacuous: zero line-less OMG memos on dev1 and stage, and A vs B returned byte-identical rows on both pods (Luis, 2026-10-14).
8. Decision markers tied to Jira-posted decisions with no objections become lowercase `tacitly accepted`; only the FSD-linked OI-1 markers stay `PENDING CONFIRMATION` (Luis, 2026-10-15).
9. PR 5 implements the ad hoc duplicate fix in the DM — optional `:P_CT_REFERENCE` parameter scoping `:P_TRX_NUMBER` selection (Vijay's derivation: number + reference identify one transaction) — with a small monocle pass-through (request, reader, API route); the DM change rides #1130, the monocle PR branches from `main` (Luis, 2026-10-15).
10. PR 7 (OIC flow change) dropped — out of this ticket's scope (Luis, 2026-10-15).
11. The API wire field is `exchange_order_reference`, the FSD §Business Context vocabulary ("Exchange order reference"); the port and the report parameter keep Oracle's `ct_reference`, and the route translates. The panel's rename-the-port proposal was reverted (Luis, 2026-10-15).
12. A blank reference 400s at the route while a blank number means "absent": a reference alone can never select anything, but a blank number still has the date-range and missing-criteria paths (review panel, Luis, 2026-10-15).
13. The contract-test fixture is self-owned and Test-prefixed, not the AR team's shared stage data; their apply flow can consume shared data at any time (Luis, 2026-10-15).
14. The same-number collision case is dropped as unseedable on stage: every transaction-number path is closed (OMG/Manual auto-numbering overrides sent values; CONTRACT sources reject REST create with AR-856364; AutoInvoice shares the OMG wall). The wrong-reference case covers the `P_CT_REFERENCE` behavior instead (Luis, 2026-10-15).
15. A drained fixture is revived by unapplying the application (SOAP `createUnapplyOnAccountCreditMemo`), never by re-seeding: the revived pair keeps its old creation_date, which the flow's sliding last-run window can never reach again (Luis, 2026-10-15).

## Evidence
- Unit: 92 integration-package tests, 100% package coverage (2026-10-13).
- Pre-push gates: full unit suite 6,973 passed at 100% total coverage; API / streams / events 333 passed, 2 pre-existing skips (2026-10-13).
- Pre-push gates, PR #2731 head `c3f9dc748` (2026-10-14): full unit 7,131 passed at 100% total coverage; API / streams / events 335 passed, 2 pre-existing skips, 1 parallel-execution flake (`fedex_cycle_count` IN-I-2019 — passes standalone in 15s, unrelated to the change).
- Pre-push gates, PR #2732 head `29cf5e829` (2026-10-15): full unit 7,094 passed at 100% total coverage; `make test-api` 336 passed, 2 pre-existing skips, zero flakes on a fresh LocalStack.
- Pre-push gates, PR #2746 head `f347a7e5b` (2026-10-15): full unit 7,082 passed at 100% total coverage; scoped API suite (the touched route file) 3 passed including the cross-BU collision case; mypy strict clean on 3,427 files.
- DM regression, live query vs new query (2026-10-14): dev1 — 16 identical, 2 old-only (classified: AR-I-3019-class NULL-dues memos, plus the TP1GPVG0GA sibling-memo case), 7 new-only (the partly-paid class), 0 value diffs. Stage — 0 identical, 1 old-only (Manual-source seed), 2 new-only (partly-paid), 0 value diffs.
- Stage pod credentials refreshed 2026-10-14 (resolves OI-4); the BIP arbiter answers on both pods.
- Contract tests, PR #2747 (2026-10-15): CI run `2c17f3ef` green with the three cases passing live on stage (60 passed, 28 skipped; exact memo sets {28018} / {28018,28021}); run `2186d703` green with all five credit-memo tests skipped after the self-owned fixture drained at 17:20Z (57 passed, 31 skipped). The pass-then-skip sequence across a stage drain also proves CI runs against stage.
- Fixture drain evidence (2026-10-15): memo 29043 applied to invoice 234001 ($100) at 17:20:04Z — `ar_receivable_applications_all` row `APP`/`display=Y` created by service-account GUID `ec0d977d21c6460b9270430dfeee2158`; both payment schedules zeroed.
- Fixture revival evidence (2026-10-15, 18:49Z): unapply of application 375934 returned HTTP 200; payment schedules restored (invoice 234001 +100 OP, memo 29043 −100 OP); the application flipped to `display='N'` plus reversal row 375963 (−100, `display='N'`); the report with `P_TRX_NUMBER=234001` + `P_CT_REFERENCE=TestTPCOLA01` returns the pair again.
- Stage QA: pending. Needs PR 1 deployed to stage (vstage tag) and PR 2's data model on the stage pod. Cases: plan → Verification plan.

## Test data
- TP46T5G015 (scheduled run + ad hoc `Transaction_Number=3002`) planned for stage QA — details in the plan.
- Self-owned stage pair for the contract tests: invoice `234001` + memo `29043` on reference `TestTPCOLA01` (US BU, USD, $100, memo on OMG source, attribute7=100). Created 2026-10-15 via REST (both numbers auto-assigned); applied by an AR-I-3018 stage run at 17:20Z; revived at 18:49Z via `createUnapplyOnAccountCreditMemo` (application 375934 reversed, schedules back to +100/−100, report row back) — now permanently report-eligible: creation 17:14Z sits behind the flow's last-run marker, so the sliding-window schedule cannot select it again while `P_TRX_NUMBER` can.

## Open items
- OI-1 (Q1): "one memo applies to one invoice" — FSD §2.2 comment to Vijay + Aruna (cc Daniela) posted 2026-10-13; Daniela cc'd Tony Huang; awaiting a functional answer. The code keeps the `PENDING CONFIRMATION` marker on the deduplicator.
- OI-3: an OIC ad hoc rerun can move the scheduled last-run window and skip a slice — propose a follow-up ticket; out of scope here. PR 7 (the OIC flow change) dropped 2026-10-15.
- OI-5: AR-I-3019 zero-due whole-refund is open Oracle-team work; prod go-live of the exchange flow waits on it.
- OI-8: "which invoice gets the money" (dedup survivor = lowest-id invoice) — posted by Luis on OTCM-143188, 2026-10-14; Vijay replied 2026-10-14 (comment 962249): the return credit memo always matches the exchange-line invoice with the same reference. Functional treats one reference = one invoice, so the survivor rule stays as the guard for the rare multi-invoice deviation (dev1: 1 of 26 references).
- Follow-ups parked in the plan (2026-10-15): OIC forwards the reference from the flow (row 9), exception-taxonomy sweep after #2732 merges (OI-11), typed search-criteria union (OI-12).
- OI-13 (RESOLVED 2026-10-15): fixture revival via unapply (decision 15) replaces just-in-time re-seeding — the revived pair is permanently outside the flow's window.
- OI-14 (DROPPED 2026-10-15): the revival unapplied the pair again, so there is no self-owned applied pair to point the applied-side test at.

## Artifacts
- Plan: [projects.AR-I-3018.OTCM-143188.plan.md](projects.AR-I-3018.OTCM-143188.plan.md)
- FSD export + comment sidecar: `integrations/AR-I-3018/docs/` (Drive-synced)
- Pre-opening review panel: run `20261013T1612`, 12/12 seats, zero blockers; findings and resolutions recorded in the plan
