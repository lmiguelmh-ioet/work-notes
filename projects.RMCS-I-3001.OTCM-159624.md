# OTCM-159624 — RMCS-I-3001: emit PoD for Paid Expedite shipping lines at the first delivered line's delivery date

- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-159624 (filed by Emilio 2026-11-19, assigned to Luis, To do)
- **RICE**: RMCS-I-3001 (companions RMCS-I-3003 / RMCS-I-3002 are separate tickets; RMCS-I-3003 is out of scope for this ticket — user decision 2026-11-19)
- **Repos**: oracle-integration-cloud (PoD DM `.sql` + `.xdm.catalog` re-export); monocle_integrations (regression coverage only — orchestrator unchanged)
- **Status** (as of 2026-11-19): design drafted; seven functional questions posted in the 3001 FSD thread, ALL ANSWERED by Aruna same day (Q7 item scope: line-type filter confirmed; she will mirror the line-type condition in 3003 contract creation). No code yet. Planning kicked off 2026-11-19 (implement-jira-ticket skill).
- **Plan**: TBD — the Cursor plan archives at wrap-up as `projects.RMCS-I-3001.OTCM-159624.plan.md`. Pre-ticket design draft: `notes/future-work/rmcs-i-3001-expedite-pod-ticket.md` (superseded by this file).

## Outcome

- (in flight — nothing shipped yet)

## What shipped

- (nothing yet)

## Decisions

### Functional clarifications (Q&A)

1. RMCS must recognize revenue for the Expedited Shipping and Handling line across contract creation, billing upload, and PoD; contracts group by sales order regardless of shipment (Aruna, sell-channel thread relaying a decision with Joel, 2026-11-19).
2. PoD identifier + rule, verbatim: Line Type "Paid Expedite"; the PoD date equals the Actual Delivery date of the First Delivered line (Vijay, 3001 FSD v04 + assigned comment, 2026-11-19).
3. Contract creation now includes item #3 "Expedited Shipping and Handling"; "Freight" and "Shipping Charge" stay excluded (Aruna, 3003 FSD update, 2026-11-19).
4. "First delivered" grain is the whole order ("on that Order" — Mapping Template note, synced 2026-11-19).
5. Six questions posted in the 3001 FSD thread 2026-11-19, ANSWERED by Aruna in the same thread 2026-11-19 (thread reassigned to Vijay):
   1. Q item scope → any order line with Line Type "Paid Expedite" (not item #3 only). Expedited shipping is only charged for B2C now. One Paid Expedite per order normally; if more than one, each takes the same first-delivered-date logic.
   2. Q PoD row values → confirmed: Satisfied/fulfilled qty = 1; the amount ($25) is loaded at contract creation by RMCS-I-3003 — the PoD row carries no amount.
   3. Q order types → B2C and B2C CPU only; never Takeaway, never B2B/Wholesale.
   4. Q first-delivered population → regular item delivery date only (warranty lines excluded): in the posted example, Nov 2.
   5. Q never delivered → covered by existing logic: the OM PoD integration populates delivery date as shipment date + 10 days when no delivery happens.
   6. Q returns → confirmed: a return does not change the expedite line's PoD.
   7. Q item-scope follow-up (posted by the user 2026-11-19) → keep the line-type filter: "it seems better to include the line type filter so that we can make sure we are not excluding any other item which has 'Paid Expedite' as line type. I will update the contract creation logic to include the Line type as condition as well" (Aruna, 3001 FSD thread, synced 2026-11-19 16:25).

### Design decisions (ours)

1. New branch in the PoD DM's standard-lines path for the "Paid Expedite" line type, skipping the shippability / `fulfilled_qty > 0` / own-date gates — the charge line has no fulfill records of its own.
2. PoD date = order-grain `MIN(doo_fulfill_line_details.actual_delivery_date)` over the order's delivered lines, not the line's own records.
3. PoD key uses the existing contract-line-combination fallback (`customer_contract_header_id || document_line_id`), as non-delivered pickup lines already do.
4. No `VRM_SOURCE_DOC_LINES` "U" record (U records are DEFERRED-split-only today).
5. Monocle orchestrator unchanged — it maps report rows through.
6. Base branch is the unmerged PoD DM stack tip `OTCM-153073-rmcs-i-3001-pod-canceled-covered-line` (`da8846cc`), live on dev1/stage — not `main`.
7. Functional questions posted as an FSD-thread reply, not Slack, and scoped to 3001 only — the billing-mirror question (3002) was deliberately routed out (user decisions 2026-11-19).
8. Proceeding assumptions recorded but NOT posted — restate at build start: item #3 only; documented sequence contract creation → billing → PoD; Satisfied Quantity = fulfilled quantity (1), Amount Applied blank; "first delivered" over regular product lines only; silent wait on never-delivered; returns don't change the expedite PoD. (Aruna's 2026-11-19 answers confirmed 3–6; item #3-only was superseded by her Q1 answer: any "Paid Expedite" line.)
9. DM line filter = `WP_PAID_EXPEDITE` line type (Aruna Q1, 2026-11-19), not item #3 only.
10. CPU orders are in scope (Aruna Q3): on CPU the "first delivered" date maps to the first regular line's pickup-task completion, the DM's existing CPU date source.
11. The expedite PoD row carries qty 1 and no amount; the $25 amount lives on the contract line created by 3003 (Aruna Q2).
12. RMCS-I-3003 is out of scope (user decision 2026-11-19): this ticket ships no contract-creation change, and the 3002 billing-mirror question is not pursued. The only open functional question is the PoD filter's item scope, which is 3001's own DM decision.
13. Item-scope follow-up posted by the user in the 3001 FSD thread 2026-11-19 (original pre-review wording) and ANSWERED by Aruna same day: keep the line-type filter so no "Paid Expedite" item is excluded; she will mirror the line-type condition in 3003 contract creation (her action, 3003 track). The PoD DM filter is FINAL: line type `WP_PAID_EXPEDITE` alone.

## Evidence

- Jira comment **988216** on OTCM-159624 (2026-11-19): the full functional Q&A (Aruna's six answers), the description-drift corrections (AC 5 assumption, open questions 7/8), and the implementation-readiness verdict — no functional questions remain for the DM change. (Edited same day to drop an unapproved scope question that was included by mistake; questions to functional go in the FSD thread, proposed to the user first.)
- 4-agent pre-post review of the question set (2 fact-check + 2 adversarial, 2026-11-19): caught the same-day 3003 FSD reversal of the shipping exclusion, the already-documented flow order, and the "(all five)" overreach; the message was reworked before posting. Claims that survived: code-level "shipping never reaches RMCS" (all five DMs), the OTCM-150967 attribution (commit `6dca2691`, PR #1154), the order-type taxonomy vs the stack DM.
- 2-agent pre-post review of the item-scope follow-up question (1 fact-check + 1 adversarial, 2026-11-19): caught the inverted failure mechanics (the DM inner-joins the contract tables, so a missing contract line means the PoD silently never loads — not an unmatched PoD row), the "today" wording overstating the 3003 FSD as live code, the suppressed third branch (items active → extend contract creation, not narrow the PoD), and the five-item universe (items 1/4 unverified → widen the ask). The user then posted the ORIGINAL pre-review wording in the 3001 FSD thread (2026-11-19), so the two factual errors above are live in the thread.

## Test data

- Skill: `rmcs-test-data`. Integration assets: `integrations/RMCS-I-3001/`.
- Sample orders from Vijay's FSD screenshots: TQA34ZG03G (contract view; P3 "Expedited Shipping and Handling" as contract line 2) and TP51K801FZ (shipping view; P3 has no shipped qty/delivery date; product lines delivered 11/02/2026 3:39 PM and 3:40 PM).

## Open items

- ~~Item scope~~ — ANSWERED (Aruna, 3001 FSD thread, 2026-11-19): line-type filter confirmed ("better to include the line type filter so that we are not excluding any other item which has 'Paid Expedite' as line type"); she will update the 3003 contract-creation logic to include the line type as a condition as well. The PoD DM filter is final — line type alone. (The two panel-caught inaccuracies in the posted wording did not affect the answer; no in-thread clarification needed.)
- Verify the never-delivered fallback (Aruna Q5: shipment date + 10 days from the OM PoD integration) — check at implementation whether that date lands in `actual_delivery_date` upstream or the 3001 DM needs its own fallback.
- CPU handling (Aruna Q3): expedite PoD on CPU orders takes the first regular line's pickup-task completion — confirm the DM's CPU date source covers it.
- ~~Billing mirror~~ — OUT OF SCOPE (user decision 2026-11-19): the 3002 billing DM still excludes 'EXPEDITED SHIPPING AND HANDLING' by name, so the charge would reach the contract but never bill. Not pursued under this ticket; belongs to the 3003/3002 track.
- Sequencing (AC 7): the expedite contract line must exist in RMCS before PoD; the contract-creation order-details DM on `main` still excludes the whole Shipping class (OTCM-150967) despite the 3003 FSD update. External dependency — 3003 is out of scope for this ticket; track, don't build. Spec sides now aligned: Aruna committed 2026-11-19 to update the 3003 contract-creation logic to the line-type condition; the code landing remains the 3003 track's.
- `line_type_code` `WP_PAID_EXPEDITE` to confirm on a pod order (e.g. TP51K801FZ) at implementation time.

## Artifacts

- 3001 FSD: https://drive.google.com/file/d/1BZInnIPHh0s6zG6n6Q6I93yGBVjl28Z8/view · Mapping Template: https://drive.google.com/file/d/1ZTlE9RFYYRHej9ZPCi3zxAwbA0hv9MoF/view · local syncs under `integrations/RMCS-I-3001/docs/drive/`.
- Functional questions thread: 3001 FSD, Vijay's 2026-11-19 comment anchored on the new Shipping Lines rule ("For Shipping Lines: Identifier: The Line Type will be 'Paid Expedite'…"), assigned to Luis, cc Aruna/Emilio. Word-sourced comment — no Drive deep-link id; use the doc link + anchor.
- PoD DM: `BI Publisher Reports/Custom/WP Integrations/FIN/Data Model/WP_RMCS_PROOF_OF_DELIVERY_DM.sql` on branch `OTCM-153073-rmcs-i-3001-pod-canceled-covered-line` (stack PRs #1105 ← #1141 ← #1181 ← #1184, live on dev1/stage).
- Monocle integration: `monocle_integrations/_domain/_integrations/_wp_rmcs_i_3001_proof_of_delivery_upload`.
- Pre-ticket design draft (superseded, kept for history): `notes/future-work/rmcs-i-3001-expedite-pod-ticket.md`.
- Related tickets: OTCM-153073, OTCM-152262, OTCM-146798 (PoD DM stack); OTCM-150967 (Shipping-class exclusion); OTCM-150433 (fulfilled-qty precedent); OTCM-151052 (held-PoD alert); OTCM-158814 (RMCS-I-3001S alert prod promotion); OTCM-158904 (RMCS-I-3003 line keys).
- Daily note: [day-20261119](day/day-20261119.md).
