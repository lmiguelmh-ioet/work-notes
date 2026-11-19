# FILED as OTCM-159624 (2026-11-19, by Emilio) — SUPERSEDED. Canonical notes: `notes/projects.RMCS-I-3001.OTCM-159624.md`. Kept for history; do not edit.

**Title:** RMCS-I-3001: emit PoD for Paid Expedite shipping lines at the first delivered line's delivery date

**Project:** OTCM · **Type:** Story · **RICE:** RMCS-I-3001

## Context

Warby sells Expedited Shipping and Handling as a separate order line (item `P3`,
line type "Paid Expedite"). Functional direction (Aruna, 2026-11-19, relaying a
decision with Joel; identifier and rule defined by Vijay the same day): RMCS must
recognize revenue for this line across contract creation, billing upload, and PoD.

The FSD ("RMCS-I-3001 - Proof of delivery upload in RMCS - FBDI Approach", updated
2026-11-19) adds the PoD rule verbatim:

> For Shipping Lines:
> Identifier: The Line Type will be "Paid Expedite".
> Logic: The actual delivery (PoD) date for the Shipping line will equal to the
> Actual Delivery date of the First Delivered line.

Current behavior: the PoD data model (`WP_RMCS_PROOF_OF_DELIVERY_DM`) never emits a
PoD row for this line. Its standard branch (`rmcs_lines_base`) requires a terminal
fulfill status, `fulfilled_qty > 0`, shippability unless pickup-sourced, and a date
from the line's own fulfill records. A Shipping and Handling charge line has none of
these (sample order TP51K801FZ: the P3 fulfill row shows no shipped quantity and no
delivery date), so the line is filtered out and its revenue is never recognized
through this flow.

Change shape: a new branch in the standard-lines path for the "Paid Expedite" line
type, skipping the shippability/fulfilled-quantity/own-date gates. The PoD date is
the earliest actual delivery date across the order's delivered lines (order-grain
`MIN(doo_fulfill_line_details.actual_delivery_date)`), not the line's own records.
The PoD key uses the existing contract-line-combination fallback
(`customer_contract_header_id || document_line_id`), as non-delivered pickup lines
already do. The row emits only once the first delivery exists; the existing
`NOT EXISTS` ORA_PROOF_OF_DELIVERY guard keeps re-runs idempotent. No
`VRM_SOURCE_DOC_LINES` "U" record (today those are DEFERRED-split-only). The monocle
orchestrator (`_wp_rmcs_i_3001_proof_of_delivery_upload`) maps report rows through
and needs no date-logic change.

Scope: the paired `.sql` and a `.xdm.catalog` re-export of
`WP_RMCS_PROOF_OF_DELIVERY_DM`, plus monocle regression coverage. The base is the
unmerged PoD DM stack (live on dev1/stage, merges at prod promotion), latest text on
branch `OTCM-153073-rmcs-i-3001-pod-canceled-covered-line` (`da8846cc`) — not
`main`. Companion requirements (contracts grouped by sales order regardless of
shipment; expedite inclusion in contract creation and billing upload) belong to
RMCS-I-3003 / RMCS-I-3002 and are separate tickets.

## Acceptance criteria

1. An order line of type "Paid Expedite" emits one
   `VRM_SOURCE_DOC_ADDL_SUBLINES` / `ORA_PROOF_OF_DELIVERY` row once at least one
   line on the same sales order has an actual delivery date. The row's PoD date
   equals the earliest actual delivery date among the order's delivered lines
   (sample: order TP51K801FZ, delivered lines 11/02/2026 3:39 PM and 3:40 PM → the
   expedite row takes 3:39 PM).
2. Only the "Paid Expedite" line type uses the new branch. Every other line keeps
   the current gates (terminal fulfill status, `fulfilled_qty > 0`, shippability
   unless pickup-sourced, per-order-type date source).
3. While no line on the order has delivered, no expedite PoD row emits. A later
   scheduled run picks it up. Re-runs never duplicate the row.
4. The row matches the loaded RMCS contract line on either `DOC_LINE_ID_INT_1`
   grain (order line id or fulfill line id), as the standard branch does, and keys
   the PoD by the contract-line combination.
5. `satisfied_quantity` and any amount fields follow the mapping template.
   ASSUMPTION: Satisfied Quantity ← fulfilled quantity (= 1 for this billed line),
   Amount Applied blank, per the mapping template. Posted for functional
   confirmation 2026-11-19 (Q2 below).
6. Regression: product-line PoD (DELIVERY / FULFILLMENT / PICKUP_TASK), warranty
   .1/.2/.3 splits, QC-fail redirect, canceled-member release, and RMA flows are
   unchanged. Verified by a dev1 A/B against the then-current DM over the standard
   QA window, with differences limited to orders carrying a Paid Expedite line.
   Stage verification covers one expedited order end to end.
7. Sequencing: the expedite contract line must already exist in RMCS (the DM joins
   `vrm_source_doc_lines` and active `vrm_perf_obligation_lines`). Sample contract
   TQA34ZG03G already shows the P3 line as contract line 2 — confirm current
   RMCS-I-3003 coverage, or sequence this ticket after the RMCS-I-3003 work.

## References

- FSD "RMCS-I-3001 - Proof of delivery upload in RMCS - FBDI Approach" (Shipping
  Lines section, updated 2026-11-19):
  https://drive.google.com/file/d/1BZInnIPHh0s6zG6n6Q6I93yGBVjl28Z8/view
  · Mapping Template:
  https://drive.google.com/file/d/1ZTlE9RFYYRHej9ZPCi3zxAwbA0hv9MoF/view
- Sell channel thread, 2026-11-19: Aruna's change list (discussed with Joel) and
  Vijay's identifier/logic definition, with two annotated screenshots (orders
  TQA34ZG03G and TP51K801FZ).
- Functional questions thread (2026-11-19): Vijay's FSD comment assigned to Luis,
  cc Aruna and Emilio, anchored on the new Shipping Lines rule ("For Shipping
  Lines: Identifier: The Line Type will be 'Paid Expedite'…"). 3001 FSD:
  https://docs.google.com/document/d/1BZInnIPHh0s6zG6n6Q6I93yGBVjl28Z8/edit
  (Word-sourced comment; no Drive deep-link id available).
- PoD DM: `BI Publisher Reports/Custom/WP Integrations/FIN/Data Model/WP_RMCS_PROOF_OF_DELIVERY_DM.sql`
  on branch `OTCM-153073-rmcs-i-3001-pod-canceled-covered-line` (stack PRs
  #1105 ← #1141 ← #1181 ← #1184, live on dev1/stage).
- Monocle integration:
  `monocle_integrations/_domain/_integrations/_wp_rmcs_i_3001_proof_of_delivery_upload`.
- Related tickets: OTCM-153073, OTCM-152262, OTCM-146798 (recent PoD DM work);
  OTCM-158814 (RMCS-I-3001S alert prod promotion); OTCM-158904 (RMCS-I-3003 line
  keys).

## Open questions / scope changers

1. What goes in `satisfied_quantity` (and any amount fields) for a charge line?
   Posted 2026-11-19 as Q2 (see below). Assumption: Satisfied Quantity ← fulfilled
   quantity (= 1 for this billed line), Amount Applied blank, per the mapping
   template.
2. Does the expedite line need a `VRM_SOURCE_DOC_LINES` "U" record? Assumption: no
   (U records are DEFERRED-split-only today). Internal; not posted.
3. Order-type scope: can Paid Expedite appear on FULFILLMENT-sourced types
   (takeaway/wholesale), which have no delivery dates? Posted 2026-11-19 as Q3.
   Assumption: delivery-sourced orders only.
4. "First delivered" grain: RESOLVED — the Mapping Template note says "the First
   Delivered line on that Order" (order grain). The remaining population question
   (which lines the scan sees) posted 2026-11-19 as Q4.
5. Returns interaction: if the first delivered line is later returned, does the
   expedite PoD change? Posted 2026-11-19 as Q6. Assumption: no; out of scope.
6. Exact DOO `line_type_code` behind the "Paid Expedite" display name: code is
   `WP_PAID_EXPEDITE` per OTCM-150967. Confirm on a pod order (e.g. TP51K801FZ) at
   implementation time.
7. The FSD update has not reached the local sync yet (last sync 2026-11-19 09:05).
   RESOLVED 2026-11-19: synced at 11:01 (integrations commit `150237e`); the rule
   text quoted above is current.
8. RMCS-I-3003 coverage (AC 7): the 3003 FSD's 2026-11-19 update now includes the
   expedite item in contract creation ("Need to Include Item number # 3 for
   'Expedited Shipping and Handling'"; "Freight" and "Shipping Charge" stay
   excluded). The gate moved to the code: the contract-creation order-details DM
   on `main` still excludes the whole Shipping item class (OTCM-150967), and the
   billing DM still excludes 'EXPEDITED SHIPPING AND HANDLING' by name
   (RMCS-I-3002) — without the billing fix the charge reaches the contract but
   never bills.
9. Item scope: item #3 only, or any line typed "Paid Expedite"? The 3003 FSD
   scopes inclusion to item #3; the 3001 FSD keys on the line type. Line type
   verified only for items 2, 3, 5 (OTCM-150967); items 1 ("Expedited 35") and 4
   ("Next Day") unverified. Posted 2026-11-19 as Q1.

## Functional questions (posted 2026-11-19)

Posted in Vijay's 2026-11-19 thread in the 3001 FSD (assigned to Luis; cc Aruna,
Emilio), anchored on the new Shipping Lines rule. Status: awaiting answers.
Verbatim as posted:

1. Item scope. Is the inclusion item #3 "Expedited Shipping and Handling" only, or
   any order line with Line Type "Paid Expedite"? Other shipping items carry that
   type too (e.g. "Next Day Air 30", "Expedited 25"). And if an order ever has two
   Paid Expedite lines, does each take the same first-delivered date?
2. PoD row values (confirm). For the expedite line's PoD row: the mapping template
   fills Satisfied Quantity from the fulfilled quantity, which is 1 for this
   billed line, and Amount Applied stays blank. Confirm both?
3. Order types. Can a Paid Expedite line appear on B2C CPU, B2C Customer Takeaway,
   or B2B/Wholesale orders — or only on shipped-to-address B2C orders? The
   delivery date source differs per order type, so this changes the logic.
4. "First delivered" population. Which lines count — every product line on the
   order that has a delivery date, or only the regular sales lines (excluding
   warranty and canceled lines)? Example: a warranty line on the order delivers
   Nov 1 and the regular item delivers Nov 2. Is the expedite PoD Nov 1 or Nov 2?
5. Never delivered. If the product lines ship and bill but nothing ever gets a
   delivery date (e.g. lost in transit), the expedite line's PoD waits
   indefinitely with no error. Is that acceptable, or should it alert?
6. Returns (confirm). A return does not change the expedite line's PoD — the
   return flow reverses the recognized revenue automatically and no additional
   PoD load is needed. Correct?

Context carried by each question (not posted):

- Q1 decides the DM's line filter (`WP_PAID_EXPEDITE` line type vs item #3 only).
  The 3003 FSD scopes inclusion to item #3; the 3001 FSD keys on the line type.
- Q2: the mapping template prescribes Satisfied Quantity ← FULFILLED_QTY, and
  billed non-shipped lines populate fulfilled quantity (OTCM-150433 precedent, per
  Aruna's template comment). Amount Applied is blank for every row.
- Q3: the PoD DM derives the date per order type (delivery date / pickup-task
  completion / fulfillment date). A Paid Expedite line on a fulfillment-sourced
  type would need its own date rule.
- Q4: the Mapping Template fixes the grain ("on that Order"); the open part is
  which line population the first-delivered scan sees.
- Q5: shipped and billed but never delivered → the expedite row waits indefinitely
  with no error. Related machinery: OTCM-151052 (held-PoD alert).
- Q6: grounded in the FSD's return flow ("Oracle will reverse recognized revenue
  automatically and No additional POD load is needed").

Proceeding assumptions (drafted, NOT posted — restate when the build starts): item
#3 only; the documented sequence contract creation → billing → PoD; Satisfied
Quantity = fulfilled quantity (1), Amount Applied blank; "first delivered" over
regular product lines only; silent wait on never-delivered; returns don't change
the expedite PoD.

Deliberately kept out of the 3001 thread (3002/3003 scope): the billing flow still
excludes 'EXPEDITED SHIPPING AND HANDLING' by name, so the charge would reach the
contract but never bill. Route "mirror the 3003 inclusion in billing, and update
the 3002 FSD?" via the 3003 FSD thread / Aruna.
