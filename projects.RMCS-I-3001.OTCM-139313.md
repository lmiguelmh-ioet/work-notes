> CLOSED 2026-10-06 — validated, ticket moved to Done; this file is frozen.
> The open items below were outstanding at close and carry over as follow-ups.

# OTCM-139313 — RMCS-I-3001: PoD data model, warranty split lines

- **Ticket**: <https://warbyparker.atlassian.net/browse/OTCM-139313>
- **RICE**: RMCS-I-3001
- **Repos**: oracle-integration-cloud, monocle_integrations
- **Status**: done — validated 2026-10-06
- **Dates**: 2026-09-22 → 2026-10-06
- **Plan**: [frozen decision log](projects.RMCS-I-3001.OTCM-139313.plan.md)

## Outcome

- `WP_RMCS_PROOF_OF_DELIVERY_DM` handles warranty commission split lines (.1/.2/.3):
  - PoD rows carry the split line's own `document_line_id`.
  - A DEFERRED split row also emits a "U" record restating the contract line (updates only its EFFs).
- PoD-only path validated on ott against dev1; ticket closed Done 2026-10-06.
- Umbrella PR #1105 was in team review at close.
- The U-row path (VRM_SOURCE_DOC_LINES update) is built but not yet regression-tested.

## What shipped

- [oracle-integration-cloud#1105](https://github.com/WarbyParker/oracle-integration-cloud/pull/1105) — umbrella PR: PoD DM `.sql` + re-exported `.xdm.catalog` — **in review**.
  - Stacked PRs #1113 / #1116 merged into it.
  - Comment-cleanup commit `3ba46139` shipped directly on it (no stacked PR).
- [monocle_integrations#2587](https://github.com/WarbyParker/monocle_integrations/pull/2587) — PoD reader adapter — **merged** 2026-09-29.
- [monocle_integrations#2589](https://github.com/WarbyParker/monocle_integrations/pull/2589) — port models + `ProofOfDeliveryImportModelsMapper` step — **merged** 2026-09-29.
- ott deploy `ott-v0.0.82` — 2026-10-06.
  - First ott-env QA of the PoD endpoint.

## Decisions

### Functional clarifications (Q&A)

- **Q1 — split-line numbering**: .1/.2/.3 = COMMISSION/UPFRONT/DEFERRED (the sheet's "3.1, 3.1, 3.3" was a typo) — functional, 2026-09-24.
- **Q2 — U-record scope**: DEFERRED split only — source review, user decision 2026-09-25.
- **Q3 — U-record amounts**: only identifiers + EFFs needed; restating not required — Aruna, 2026-09-28.
  - She then flipped 16 sheet fields to Optional; the restated superset stays meanwhile (slim deferred to `u-record-simplify`).
- **Q3a — satisfaction fields**: quantity-based; Satisfied Percent stays empty — functional, 2026-09-24.
- **Q4 — dedup granularity**: one PoD per split line → dedup keyed on (`document_line_id`, split suffix) — functional, 2026-09-24.
- **Q5 — replacement & covered-item linkage** — Aruna/Vijay + dev1 OM setup metadata, 2026-10-02 → 10-05:
  - The return line carries `reference_line_id` to the original line → line-level identity (solves the multi-item problem).
  - The replacement date comes from the sibling ship-only line (2-line structure guaranteed).
  - Linkage EFFs live on `DOO_FULFILL_LINES_EFF_B` context `Warranty`: Covered Line→`ATTRIBUTE_CHAR1`, Covered Order#→`ATTRIBUTE_CHAR2`.
  - Q5a: Covered Line always carries the numeric line number (dev1 junk was test data).
  - Q5b: replacement orders are typed WP_B2C_RETURN / WP_B2B_RETURN → dedicated `replacement_type_rules` CTE.
  - Q5c: first claim ends the deferral → MIN aggregation.
  - Q5d: exactly-2-lines-per-replacement accepted as guaranteed (user, 2026-10-05).
  - Q5e: missing EFF → the split waits silently; acceptable (EFFs are mandatory OMG→OM).
  - Q5f: order numbers are unique per real order (assigned by OMG).
  - Q5g: the reference link exists only on return lines.
- **Q6 — commission DFF segments**: UPFRONT→`ATTRIBUTE1`, DEFERRED→`ATTRIBUTE2` — FSD screenshot + dev1 metadata, 2026-09-23.
- **Q7 — UPFRONT ship+14 fallback**: removed — OM populates PoD with ship+14 upstream; sheet edit + user, 2026-09-25.
- **Q8 — extraction timing** — Aruna, 2026-10-01:
  - Each split goes only when its date exists.
  - Billing happens at ship confirm for all order types.
  - .3 DEFERRED at the earliest of replacement PoD / contract end date.
- **Q9 — PoD sub-line id**: header‖line concat stays — Aruna, 2026-09-30.
- **Q10 — replacement date flavor**: same per-type logic as sales (takeaway/wholesale: fulfillment date) — Aruna, 2026-09-30.
  - Replacements are ship-only: no billing, no new contract, no new splits.
- **Q11 — contract end date base**: covered-item PoD + 365 — Aruna, 2026-10-01.
  - The sample file's order-date-based value is ignored.
- **Q12 — U-record blanks**: blanks keep stored values — dev1 wipe-test + Aruna ("tested during POC"), 2026-10-01.
- **Q13 — order-type keying**: key on the order type CODE, never the display name — Aruna, 2026-10-02.
- **Q14 — early future-dated .3**: harmless; RMCS recognizes strictly by PoD date — Aruna, 2026-10-02.
- **Q15 — covered item never delivers**: that is a reshipment, not a replacement; PoD is guaranteed on the covered item — Aruna, 2026-10-02.
- **Q16 — ship-to account NULL on all dev1 fulfill lines** — user, 2026-10-01:
  - Revoked as a functional question; the reader was relaxed to the sheet's Required/Optional instead (D6).
  - The team was notified as a diagnostic (I-3003 may want the value, derivable from the ship-to party).
  - The CONTRACT_END_DATE half still gates the dev1 U-row regression.
- **Return-type flavor mirror** (last open item) — Aruna, FSD comment 2026-10-05:
  - Plain returns need no PoD upload: auto-reversal via I-3003 return lines + I-3002 credit memo.
  - The replacement PoD date comes from the ship-only sibling's delivery/fulfillment date.
  - Verdict: the mirror stands (WP_B2C_RETURN→DELIVERY, WP_B2B_RETURN→FULFILLMENT).
  - Cross-checked against OM's "Order and Line Types" spreadsheet, 2026-10-06.

### Design decisions (ours)

- **D1 — dates computed in SQL** (BIP DM), not Python — user, 2026-09-24.
  - One less monocle PR; rule tweaks go through the BIP re-export cycle.
- **D2 — dedup engages only post-transformation**: the join on `document_line_id` means the ~4-min INITIALIZED window does not suppress re-extract — disclosed in the Jira evidence comment.
- **D3 — `contract_end_date` required on both port models** → a dateless "U" update is unrepresentable — PR #2589 review, 2026-09-29.
- **D4 — unguarded `TO_NUMBER` on EFF values**: loud failure over a silent NULL — user, 2026-09-28.
  - Reconfirmed 2026-10-02 after the ORA-01722 regression (the F6 semi-join was reverted instead).
- **D5 — U record keeps the full column set** — user, 2026-10-01.
  - The CHAR41/42/44 pass-through PRs (9a/9b) were dropped after the Q12 wipe-test.
- **D6 — reader honors the live sheet's Required/Optional** for all U-record fields — user, 2026-10-01.
  - Only `document_id`, `document_number`, `contract_end_date` stay required.
- **D7 — comment-cleanup shipped directly on the umbrella branch** (no stacked PR) — user, 2026-10-06.

## Evidence

- QA run 2026-10-06 (ott Lambda → dev1 pod), order 274, line 2.1 COMMISSION split, qty 1:
  - `POST /rmcs/proof-of-delivery-upload` → HTTP 204; Lambda request `a99254e1-60cf-40ff-bb90-8eee8fdf741c`.
  - ESS job 117067194 → SUCCEEDED.
  - `vrm_source_doc_addl_sublines` row 31002: INITIALIZED → CREATE_ASE_PROCESSED (`document_line_id` 38014).
  - Dedup proven: report re-run for order 274 → 0 rows.
- Audit-grade evidence: Jira OTCM-139313 comment id 956375.

## Test data

- **PoD recipe**: skill `rmcs-test-data` — PoD eligibility rules, VRM table cheatsheet, dev1 limitations, dedup caveat.
- **Order create → deliver chain**: skill `om-order-lifecycle`.
- **dev1 orders**: 274/275 — WP_B2C with WP_AI_WARRANTY lines (item 49000007, commission DFF).
  - 274 is the QA-green order (line 2.1, contract 38015 / line 38014).
- **TestPoD* series** (TestPoD2/3/5, …) — created during the 2026-09-28 spikes; history in [projects.RMCS-I-3001.archive](projects.RMCS-I-3001.archive.md).
- **QA payload**: `{"sales_order_numbers": ["274"]}` → ott `POST /rmcs/proof-of-delivery-upload`.
  - Full identifier set: Jira comment 956375.

## Open items

Outstanding at close (2026-10-06) — carried over as follow-ups:

- Activation PR (monocle): wire the mapper and extend `init_import_models` so `source_doc_line_updates` reach the FBDI payload (follow-up named in #2589).
- U-row path regression:
  - Needs CONTRACT_END_DATE data on dev1 (OM Warranty EFF setup).
  - The ship-to half is unblocked by D6.
- Prod regression after PR #1105 review completes.
- Optional hardening: key the replacement sibling on line type WP_SHIP_ONLY/WP_CPU_SHIP_ONLY instead of "any shippable fulfill line".

## Artifacts

- FSD: <https://docs.google.com/document/d/1BZInnIPHh0s6zG6n6Q6I93yGBVjl28Z8/edit>
- Mapping template: <https://docs.google.com/spreadsheets/d/1ZTlE9RFYYRHej9ZPCi3zxAwbA0hv9MoF/edit>
- Skills touched: `rmcs-test-data`, `om-order-lifecycle`, `jira-qa-evidence` (new), `lambda-function-url-invoke` (oic2 profile), `fusion-sql` (`run_bip_report.py`).
- Pre-ticket history + query collection: [projects.RMCS-I-3001.archive](projects.RMCS-I-3001.archive.md)
