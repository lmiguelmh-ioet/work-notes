# OTCM-143188 — AR-I-3018: select an exchange credit memo and its invoice while the invoice still has a balance
- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-143188
- **RICE**: AR-I-3018 (refund side: AR-I-3019)
- **Repos**: `monocle_integrations` (PR 1), `oracle-integration-cloud` (PR 2, data model)
- **Status** (as of 2026-10-14): #2730 merged; #2731 updated in review (main merged, all 10 review threads answered); #2732 open, restacked onto #2731 head `c3f9dc748`; DM PR #1130 open, stacked on #1064's branch
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
- Code-side enforcement is open as the stacked PRs #2730 → #2731 → #2732: a memo never applies more than the invoice still owes, even when several memos meet one invoice in a single run.
- Deploy order decided: the monocle change merges and promotes first, the data-model change second.

## What shipped
- [PR #2729](https://github.com/WarbyParker/monocle_integrations/pull/2729) — CLOSED unmerged 2026-10-14; split into the three-PR stack below.
- [PR #2730](https://github.com/WarbyParker/monocle_integrations/pull/2730) — `[OTCM-143188] Add AR-I-3018 credit memo row deduplicator` — MERGED 2026-10-14 (squash `d3c523c53` on `main`).
- [PR #2731](https://github.com/WarbyParker/monocle_integrations/pull/2731) — `[OTCM-143188] Add AR-I-3018 credit memo row processor` — OPEN, base retargeted to `main`. Updated 2026-10-14: merged main (conflict in `_steps/__init__.py` resolved to the branch version) + hardening commit `c3f9dc748` answering all 10 review threads (7 applied: sub-cent ROUND_DOWN-at-parse fix, processor logging restructure, test naming/AAA/fixture dedup, new mapping + gl_date + consume-spy tests; 2 declined with rationale: tracker injection, `_resolve_apply_amount` duplication; 1 reply-only: `amount_applied` is the wire name). 10/10 replies posted.
- [PR #2732](https://github.com/WarbyParker/monocle_integrations/pull/2732) — `[OTCM-143188] Apply AR-I-3018 credit memos only while the invoice has a balance` — OPEN, stacked on #2731. Merge order: #2730 → #2731 → #2732.
- [PR #1130](https://github.com/WarbyParker/oracle-integration-cloud/pull/1130) — `[OTCM-143188] AR-I-3018: Select unapplied credit memos for invoices with a balance` — OPEN 2026-10-14, stacked on [PR #1064](https://github.com/WarbyParker/oracle-integration-cloud/pull/1064)'s branch, label `enhancement`. Commit `dacd2a2e` (amended after the review-panel edits: `ps.class = 'CM'` memo-side, hoisted memo-level NOT EXISTS, bounded `pay_sched` scan, dropped dead projections, same-currency pairing guard; re-exported catalog embeds the edited query, verified byte-equal). A/B proofs: committed vs edited 23/23 identical on dev1; live vs edited 16/2/7/0 = the approved regression buckets.

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

## Evidence
- Unit: 92 integration-package tests, 100% package coverage (2026-10-13).
- Pre-push gates: full unit suite 6,973 passed at 100% total coverage; API / streams / events 333 passed, 2 pre-existing skips (2026-10-13).
- Pre-push gates, PR #2731 head `c3f9dc748` (2026-10-14): full unit 7,131 passed at 100% total coverage; API / streams / events 335 passed, 2 pre-existing skips, 1 parallel-execution flake (`fedex_cycle_count` IN-I-2019 — passes standalone in 15s, unrelated to the change).
- DM regression, live query vs new query (2026-10-14): dev1 — 16 identical, 2 old-only (classified: AR-I-3019-class NULL-dues memos, plus the TP1GPVG0GA sibling-memo case), 7 new-only (the partly-paid class), 0 value diffs. Stage — 0 identical, 1 old-only (Manual-source seed), 2 new-only (partly-paid), 0 value diffs.
- Stage pod credentials refreshed 2026-10-14 (resolves OI-4); the BIP arbiter answers on both pods.
- Stage QA: pending. Needs PR 1 deployed to stage (vstage tag) and PR 2's data model on the stage pod. Cases: plan → Verification plan.

## Test data
- TP46T5G015 (scheduled run + ad hoc `Transaction_Number=3002`) planned for stage QA — details in the plan.

## Open items
- OI-1 (Q1): "one memo applies to one invoice" — FSD §2.2 comment to Vijay + Aruna (cc Daniela) posted 2026-10-13; Daniela cc'd Tony Huang; awaiting a functional answer. The code keeps the `PENDING CONFIRMATION` marker on the deduplicator.
- OI-3: an OIC ad hoc rerun can move the scheduled last-run window and skip a slice — propose a follow-up ticket; out of scope here.
- OI-5: AR-I-3019 zero-due whole-refund is open Oracle-team work; prod go-live of the exchange flow waits on it.
- OI-8: "which invoice gets the money" (dedup survivor = lowest-id invoice) — posted by Luis on OTCM-143188, 2026-10-14; awaiting money-services.

## Artifacts
- Plan: [projects.AR-I-3018.OTCM-143188.plan.md](projects.AR-I-3018.OTCM-143188.plan.md)
- FSD export + comment sidecar: `integrations/AR-I-3018/docs/` (Drive-synced)
- Pre-opening review panel: run `20261013T1612`, 12/12 seats, zero blockers; findings and resolutions recorded in the plan
