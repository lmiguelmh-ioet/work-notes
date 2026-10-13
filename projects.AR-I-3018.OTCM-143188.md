# OTCM-143188 — AR-I-3018: select an exchange credit memo and its invoice while the invoice still has a balance
- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-143188
- **RICE**: AR-I-3018 (refund side: AR-I-3019)
- **Repos**: `monocle_integrations` (PR 1), `oracle-integration-cloud` (PR 2, data model)
- **Status** (as of 2026-10-13): PR 1 open in review; PR 2 not started
- **Plan**: [projects.AR-I-3018.OTCM-143188.plan.md](projects.AR-I-3018.OTCM-143188.plan.md)

## Outcome
- Code-side enforcement is open as PR #2729: a memo never applies more than the invoice still owes, even when several memos meet one invoice in a single run.
- Deploy order decided: the monocle change merges and promotes first, the data-model change second.

## What shipped
- [PR #2729](https://github.com/WarbyParker/monocle_integrations/pull/2729) — `[OTCM-143188] Cap AR-I-3018 apply amount by invoice balance with per-run tracking` — OPEN, in review. Commit `1d6fa5329`, label `enhancement`.

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

## Evidence
- Unit: 92 integration-package tests, 100% package coverage (2026-10-13).
- Pre-push gates: full unit suite 6,973 passed at 100% total coverage; API / streams / events 333 passed, 2 pre-existing skips (2026-10-13).
- Stage QA: pending. Needs PR 1 deployed to stage (vstage tag) and PR 2's data model on the stage pod. Cases: plan → Verification plan.

## Test data
- TP46T5G015 (scheduled run + ad hoc `Transaction_Number=3002`) planned for stage QA — details in the plan.

## Open items
- OI-1 (Q1): "one memo applies to one invoice" — FSD §2.2 comment to Vijay + Aruna (cc Daniela) posted 2026-10-13; Daniela cc'd Tony Huang; awaiting a functional answer. The code keeps the `PENDING CONFIRMATION` marker on the deduplicator.
- OI-3: an OIC ad hoc rerun can move the scheduled last-run window and skip a slice — propose a follow-up ticket; out of scope here.
- OI-4: stage pod credentials returned HTTP 401 on 2026-10-12; refresh before stage QA.
- OI-5: AR-I-3019 zero-due whole-refund is open Oracle-team work; prod go-live of the exchange flow waits on it.
- PR 2: data-model edits (1)–(7) in the live BIP editor on the stage pod, then export `.sql` + `.xdm.catalog` together.

## Artifacts
- Plan: [projects.AR-I-3018.OTCM-143188.plan.md](projects.AR-I-3018.OTCM-143188.plan.md)
- FSD export + comment sidecar: `integrations/AR-I-3018/docs/` (Drive-synced)
- Pre-opening review panel: run `20261013T1612`, 12/12 seats, zero blockers; findings and resolutions recorded in the plan
