# OTCM-160175 — RMCS-I-3001: Identify Customer Contracts with Create Accounting = Yes
- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-160175
- **RICE**: RMCS-I-3001
- **Repos**: monocle_integrations
- **Status**: CLOSED 2026-11-27 — Jira shows Done (resolved 06:08 ET, QA). This file is now frozen.
- **Plan**: — (no plan file)

## Outcome
- Identify Customer Contracts now submits with Create Accounting = Yes, Summary report style, and the submission date in parameter position 3.

## What shipped
- monocle PR [#2975](https://github.com/WarbyParker/monocle_integrations/pull/2975) — **MERGED** 2026-11-26 21:40Z (`1551b2beb`).

## Decisions
### Functional clarifications (Q&A)
1. Why does an identified contract show no accounting entries? → Entries generate only at contract freeze, never at identification (Aruna, Slack, 2026-11-26).
2. What is the freeze period? → TEST held identified contracts 2 days for validation; prod freezes immediately (0 days). Aruna changed TEST to 0 days as well — new contracts freeze immediately (Aruna, Slack, 2026-11-26).
3. How do you get entries for a contract manually? → Freeze the contract in the RMCS UI, then re-run Identify Customer Contracts (Aruna, Slack, 2026-11-26). Verified live: freeze of contracts 24003/24004 (= O160175H/O160175G) + Identify re-runs produced DRAFT AE headers at 20:06:34Z and 21:30:28Z (requests 128254077, 128254375; the second batch replaced the first).
4. Which id is the "contract #"? → `customer_contract_header_id` (24003/24004), NOT `vrm_source_documents.document_id` (27004/28002). XLA entities key on the contract id; an early probe keyed on document ids falsely reported zero entries (self-correction, 2026-11-26).

### Design decisions (ours)
1. None beyond the ticket-specified parameter shape (`<LedgerId>,D,<date>,S,Y,N,N,N,#NULL`).

## Evidence
- QA runs 2026-11-26, stage Lambda vstage474 → TEST (fa-evdi-test): five Identify submissions (128253112, 128253541, 128253591, 128253659, 128253663) across contract creation, PoD, and billing triggers; AC1/AC3/AC5 pass ×5.
- AC2/AC4 probe: post-freeze Identify re-runs generated 5 DRAFT AE headers (324286580–584, ledger 300000003994590, one per event, duplicate check zero rows) for contracts 24003 (O160175H) and 24004 (O160175G); revenue recognized on G's lines ($103 + $62.40).
- QA evidence comment: **posted 2026-11-26, comment id 991696** — all ACs Pass, 9 attachments uploaded and linked inline (attachment ids 374190–374198).

## Test data
- Skill: `rmcs-test-data` (freeze-gate section and XLA cheatsheet rows added 2026-11-26).
- TEST fixtures: orders O160175H (document 27004 / contract 24003, invoice 22320 $104) and O160175G (document 28002 / contract 24004, invoices 22321 $103 + 27122 $80).

## Open items
- None — QA verified and closed the ticket 2026-11-27.

## Artifacts
- PR: https://github.com/WarbyParker/monocle_integrations/pull/2975 (merged `1551b2beb`)
- QA Run Evidence: Jira comment 991696 on OTCM-160175 + 9 attachments (ids 374190–374198)
- Skill touched: `rmcs-test-data`
