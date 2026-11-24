---
name: RMCS-I-3001 Paid Expedite PoD
overview: "Implement OTCM-159624: a new dedicated UNION ALL arm in WP_RMCS_PROOF_OF_DELIVERY_DM emits PoD rows for WP_PAID_EXPEDITE shipping lines, dated at the order's first delivered regular line (panel-validated design, inert until RMCS-I-3003 creates expedite contract lines), plus test-only regression coverage in monocle."
todos:
  - id: dm-arm
    content: "Phase 1: implement the expedite UNION ALL arm + scoped D6 exclusion in WP_RMCS_PROOF_OF_DELIVERY_DM.sql on a branch stacked on OTCM-153073-rmcs-i-3001-pod-canceled-covered-line"
    status: completed
  - id: dm-verify
    content: "Phase 1: fusion-sql verification — full DM clean on dev1, dev1 A/B zero-diff vs base, TEST arm probes (0 rows pre-seeding)"
    status: completed
  - id: catalog
    content: "Phase 1: paired .xdm.catalog re-export in the dev1 BIP editor (USER STEP) + byte-identical embedded-SQL verification before commit"
    status: completed
  - id: pr1
    content: "Phase 1: PR-workflow for PR 1 (self-review, tmp/pr_description.md, pre-opening panel, open stacked on #1184, gh stack link, enhancement label)"
    status: completed
  - id: monocle-tests
    content: "Phase 2: monocle test-only PR — expedite-shaped rows through reader/mapper/FBDI action + orchestrator regression test, 100% coverage"
    status: completed
  - id: qa-evidence
    content: "Phase 3: dev1 A/B regression evidence + QA evidence comment on OTCM-159624 (jira-qa-evidence skill); full TEST arm exercise once a contract line is seeded (precondition)"
    status: completed
isProject: false
---

# RMCS-I-3001 Paid Expedite PoD (OTCM-159624)

**Status (2026-11-24):** DONE — ticket moved to Done 2026-11-24. All three phases complete: oracle-integration-cloud **#1211** (stacked on #1184 in stack #1182) and monocle **#2953** (test-only) open, merging at PROD promotion per repo convention; the DM is deployed on dev1 and TEST (both live texts byte-verified against the branch). QA evidence posted 2026-11-24 (comments 990237/990238 + 36 attachments, ids 373210–373245): all seven ACs Pass — dev1 zero-diff A/B over a wide window, TEST end-to-end on the seeded TestExp2 fixture (contract 22002) and the organic RMCS-I-3003 contracts 22003/22004, with dedup on re-runs. Archived verbatim at wrap-up to `notes/projects.RMCS-I-3001.OTCM-159624.plan.md`.

## Context

FSD v04 (Vijay, 2026-11-19) extends RMCS-I-3001: order lines with line type **Paid Expedite** ("Expedited Shipping and Handling", e.g. $25) must receive Proof of Delivery rows in RMCS so their revenue can be recognized. Rule, verbatim from the FSD: "For Shipping Lines: Identifier: The Line Type will be 'Paid Expedite'…" — the PoD date equals the Actual Delivery date of the **first delivered line** on the order.

- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-159624 (In Progress, 3 pts, Sprint OTCM SPRINT 71)
- **Canonical working notes**: [projects.RMCS-I-3001.OTCM-159624.md](notes/projects.RMCS-I-3001.OTCM-159624.md) — decisions 1–15, evidence, open items; this plan mirrors its state and does not duplicate it
- **Q&A record model**: [rmcs-i-3001_warranty_pod_support_360cc59e.plan.md](monocle_integrations/.cursor/plans/rmcs-i-3001_warranty_pod_support_360cc59e.plan.md) Phase 0 (warranty ticket's plan — same format reused below)
- **DM to change**: `BI Publisher Reports/Custom/WP Integrations/FIN/Data Model/WP_RMCS_PROOF_OF_DELIVERY_DM.sql` in oracle-integration-cloud
- **Base**: stack tip branch `OTCM-153073-rmcs-i-3001-pod-canceled-covered-line` (`da8846cc`, live on dev1/stage, PR #1184) — new work stacks on it, never on `main` (stack PRs #1105 ← #1141 ← #1181 ← #1184)
- **Monocle**: [\_wp_rmcs_i_3001_proof_of_delivery_upload](monocle_integrations/monocle_integrations/_domain/_integrations/_wp_rmcs_i_3001_proof_of_delivery_upload/) — orchestrator and mapper are fully generic; **zero production change**, regression coverage only
- 3003/3002 (contract creation, billing mirror) are **out of scope** (user decision 2026-11-19); the arm is inert until 3003 creates expedite contract lines

## Pod verifications (fusion-sql, 2026-11-19/20; TEST = fa-evdi-test, dev1 = fa-evdi-dev1)

- TP51K801FZ (TEST): line 1 `WP_B2C` CLOSED qty 1, delivered **2026-11-02 15:39:52** (the AC-1 expectation); line 2 `WP_B2C` CLOSED, delivered 15:40:04; line 3 `WP_PAID_EXPEDITE` CLOSED qty 1, single **undated** fulfill detail. Delivery values stamped **2 days late** (last_update 2026-11-04 13:32) — the write-date backfill catch is mandatory.
- `WP_PAID_EXPEDITE` line type code confirmed on pod. Census: 82% of TEST expedite fulfill rows rest in `PAUSE FOR BILLING` qty NULL/0 (billing-hold is the dominant state — no fulfill gate in the design).
- TQA34ZG03G contract (TEST): `doc_line_id_int_2` = 1, 3, 4, 5, 6 — the expedite line's contract line does **not** exist (ticket description stale); contract absent on dev1 entirely. Zero expedite contract lines on both pods (arm inert until 3003).
- dev1's expedite delivered-population is **empty** — the dev1 A/B proves zero-diff regression (AC 6) but cannot exercise the new arm; only TEST has both populations.
- Expedite lines exist off-gate: `WP_B2C_RETURN` (9, TEST) and `WP_B2C_TAKEAWAY` (1, dev1) — excluded by the type gate; D6 scoping keeps their standard-arm backstop.
- Panel round 1 (3 seats) converged on the design family; round 2 (2 adversarial seats) = **ADOPT WITH CHANGES**, both finding the same BLOCKER (write-date catch) — all fixes folded into the design below. AC 1 simulated by both seats to the exact timestamp.

## Final design (panel-validated; decision 15 in the ticket file)

New dedicated UNION ALL arm in `WP_RMCS_PROOF_OF_DELIVERY_DM` — the only arm that emits expedite contract lines:

1. **Pool** — `WP_PAID_EXPEDITE` lines on `WP_B2C`/`WP_B2C_CPU` orders (explicit type list per Aruna Q3), stub headers excluded (`h.status_code NOT IN ('DOO_REFERENCE','DOO_DRAFT')`), pre-fulfillment-canceled lines excluded (mirror `is_excluded_canceled`; cancel-after-terminal keeps dates per Aruna Q6). **No fulfill status/`fulfilled_qty` gate** — emission keys off regular-line delivery + contract match, not the charge line's billing lifecycle. Semi-join/EXISTS shapes: one row per expedite line by construction (no in-batch duplicates).
2. **Date** — order-grain MIN over the order's REGULAR lines' per-line completion dates: `fulfill_delivery` per-line `MAX(actual_delivery_date)` for DELIVERY lines; `NVL(qc_fail_resolution.replacement_pickup_date, pickup_task_dates.pickup_completion_date)` per line on PICKUP_TASK (the standard arm's QC-fail redirect overlay, dm_base.sql:733–739). Regular = line types NOT IN (`WP_AI_WARRANTY`, `WP_PAID_EXPEDITE`, `WP_CPU_SHIP_ONLY`, `WP_SHIP_ONLY`); MIN must be non-null; aggregation restricted to pool orders by `header_id`. No `otr.date_source` switch — the FSD pins actual delivery date.
3. **Contract match** — both grains (order line id OR fulfill line id) via the warranty arm's semi-join + earliest-viable pin + active `vrm_perf_obligation_lines`; `SUB_LINE_ID = customer_contract_header_id || document_line_id`. No contract line → no row (inert until 3003).
4. **Emit shape** — qty 1, ALL update columns NULL, `UPDATE_RECORD_TYPE` blank (the monocle reader's PoD-only contract, `_oracle_proof_of_delivery_reader.py`: raises on update fields without UPDATE_RECORD_TYPE and on missing SUB_LINE_ID). One row per expedite contract line; multi-expedite orders emit one row per line, all at the same order-grain date.
5. **D6 exclusion (scoped)** — in `rmcs_lines_base` (~lines 762–765, the only standard-path line-type filter) add `WP_PAID_EXPEDITE` to the exclusion list **scoped to `WP_B2C`/`WP_B2C_CPU` orders** so off-gate Takeaway/Wholesale expedite lines keep their existing standard-arm path; prevents two-arm double-emission once 3003 contract lines exist.
6. **Window arms (three-path parity with the standard arm)** — primary `GREATEST(first_delivery, sdl.creation_date)` (creation-date fold re-selects orders whose contract line arrives after delivery — the normal 3003 sequencing); backfill catch on the order-grain MAX of the regular lines' write dates (`pod_last_update` equivalents, dm_base.sql:740–754) guarded by `first_delivery <= :P_TO_DATE`; `P_ORDER_NUMBERS` order-numbers mode parity (the only recovery path for a missed row).
7. **Idempotency** — same `NOT EXISTS ORA_PROOF_OF_DELIVERY` guard as existing arms. Caveat for the test plan: a REJECTED first load suppresses re-emission until purge.

## Phase 0 — Functional clarifications (questions tracked here: exact texts + response history)

All functional questions live in the **3001 FSD comment thread** anchored on Vijay's 2026-11-19 Shipping-Lines rule (per standing rule: never Jira; exact wording pre-approved by the user before posting). The thread is Word-sourced — invisible to the Drive comments API; the verbatim record is the synced sidecar [RMCS-I-3001 - Proof of delivery upload in RMCS - FBDI Approach.comments.md](integrations/RMCS-I-3001/docs/drive/RMCS-I-3001%20-%20Proof%20of%20delivery%20upload%20in%20RMCS%20-%20FBDI%20Approach.comments.md) (refresh: `integrations/sync/sync.sh --refresh --no-commit --only RMCS-I-3001-docs`). The FSD doc: https://drive.google.com/file/d/1BZInnIPHh0s6zG6n6Q6I93yGBVjl28Z8/view. The Q&A summary is Jira comment [988216](https://warbyparker.atlassian.net/browse/OTCM-159624) (2026-11-19, edited clean).

Anchor comment (Vijay, 2026-11-19, assigned to Luis, cc Aruna/Emilio): "For Shipping Lines: Identifier: The Line Type will be "Paid Expedite".Logic: The actual delivery (PoD) date for the Shipping line will equal to the Actual Delivery date of the First Delivered line." — whole-order grain per the Mapping Template note ("on that Order").

### Open

#### P1 — 3003 contract-creation order-type gate (cross-ticket, 3003 track)

- **Context:** Aruna's Q7 mirror commitment names the line-type condition only; the PoD side gates on `WP_B2C`/`WP_B2C_CPU` per Q3. Expedite lines exist on `WP_B2C_RETURN` (9 on TEST) and `WP_B2C_TAKEAWAY` (1 on dev1) orders. If 3003 creates contract lines for those, they never get a PoD from the new arm — the scoped D6 keeps the standard-arm path as a backstop, so nothing breaks, but the contract line's performance obligation may never satisfy.
- **Question (drafted, NOT posted):** "You will update the contract creation logic to include the Line type as condition. Will it also keep the same order-type scope as the PoD side (B2C and B2C CPU only), or could contract lines be created for Paid Expedite lines on return or takeaway orders too?"
- **Why it matters:** a contract line with no PoD path sits in RMCS with a performance obligation that never satisfies — a silent mismatch between the two specs.
- **Where to ask:** the 3001 FSD thread anchored on Vijay's Shipping-Lines rule (reply in the existing thread — it already carries the Q7 exchange; do not open a new one). Belongs to the 3003 track, not this DM.
- **Status:** parked — user decides whether/when to post (3003 is out of scope for this ticket, user decision 2026-11-19).

#### P2 — "First delivered" grain under split shipments

- **Context:** the FSD says "the Actual Delivery date of the First Delivered line". The DM dates every line at its per-line completion (MAX over its delivery details). Two readings: the first line to *finish* delivering (MIN of per-line MAX — adopted) vs the earliest delivery *event* (MIN over all dated regular-line details). They diverge only when the first-delivered line ships in split packages.
- **Working assumption (adopted):** MIN of per-line MAX — the DM's own per-line dating convention, and AC 1's fixture cannot distinguish the readings (one dated detail per line). Pod census: 0 divergent orders on TEST, so this is unexercised in data today.
- **Question (optional, drafted):** "For an order whose first-delivered item ships in two packages on different days, should the expedite PoD date be the day that item finishes delivering, or the day its first package arrives?"
- **Why it matters:** one aggregation flip in `expedite_first_delivery` — not a redesign.
- **Where to ask:** same FSD thread. Parked — confirmation optional (0 divergent orders today; proceed on the assumption).

### Resolved

#### Q1 — Item scope: item #3 only, or any "Paid Expedite" line?

- **Posted 2026-11-19** (message of six questions, this thread): "1. Item scope. Is the inclusion item #3 "Expedited Shipping and Handling" only, or any order line with Line Type "Paid Expedite"? Other shipping items carry that type too (e.g. "Next Day Air 30", "Expedited 25"). And if an order ever has two Paid Expedite lines, does each take the same first-delivered date?"
- **ANSWERED 2026-11-19 (Aruna):** "1) Business confirmed that Expedited shipping and handling is only charged for B2C process now. lets Include line type as " Paid Expedite". It is one paid expedite per order, if order has more than one paid expedite lines, then consider the same logic of first delivered date."
- Design impact: pool filter = line type alone (finalized by Q7); multi-expedite orders emit one row per line, all at the same order-grain date.

#### Q2 — PoD row values (confirmation)

- **Posted 2026-11-19:** "2. PoD row values (confirm). For the expedite line's PoD row: the mapping template fills Satisfied Quantity from the fulfilled quantity, which is 1 for this billed line, and Amount Applied stays blank. Confirm both?"
- **ANSWERED 2026-11-19 (Aruna):** "2) yes Satisfied/fulfilled qty is 1 and amount is $25 which is loaded while creating the contract in 3003 contract creation integration."
- Design impact: qty constant 1, no amount on the PoD row (supersedes the AC-5 assumption — the correction is recorded in Jira comment 988216). Template drift note: the mapping template derives Satisfied Quantity from `FULFILLED_QTY` — constant 1 per this answer wins.

#### Q3 — Order types in scope

- **Posted 2026-11-19:** "3. Order types. Can a Paid Expedite line appear on B2C CPU, B2C Customer Takeaway, or B2B/Wholesale orders — or only on shipped-to-address B2C orders? The delivery date source differs per order type, so this changes the logic."
- **ANSWERED 2026-11-19 (Aruna):** "3) Expedite shipping line can appear on B2C orders, CPU orders. But not on Take away, B2B/Wholesale orders."
- Design impact: pool gate = `('WP_B2C','WP_B2C_CPU')` explicit; on CPU the first-delivered date maps to the first regular line's pickup-task completion (the DM's existing CPU date source — panel-verified against `pickup_task_dates` + the QC-fail redirect overlay).

#### Q4 — "First delivered" population

- **Posted 2026-11-19:** "4. "First delivered" population. Which lines count — every product line on the order that has a delivery date, or only the regular sales lines (excluding warranty and canceled lines)? Example: a warranty line on the order delivers Nov 1 and the regular item delivers Nov 2. Is the expedite PoD Nov 1 or Nov 2?"
- **ANSWERED 2026-11-19 (Aruna):** "4) Only the regular item delivery date. In the example it is Nov 2 is the POD"
- Design impact: regular = line types NOT IN (`WP_AI_WARRANTY`, `WP_PAID_EXPEDITE`, `WP_CPU_SHIP_ONLY`, `WP_SHIP_ONLY`). Adopted interpretation (panel F3): "canceled excluded" = canceled pre-fulfillment; cancel-after-terminal keeps its dates (mirrors the standard arm's `is_excluded_canceled`; consistent with Q6).

#### Q5 — Never delivered

- **Posted 2026-11-19:** "5. Never delivered. If the product lines ship and bill but nothing ever gets a delivery date (e.g. lost in transit), the expedite line's PoD waits indefinitely with no error. Is that acceptable, or should it alert?"
- **ANSWERED 2026-11-19 (Aruna):** "5) In OM POD integration Logic is in place to populate delivery date as Shipment date+10 days. This covers the never delivered scenario"
- Design impact: none — the date lands in `actual_delivery_date` upstream; the DM reads the resulting date either way. Template text says ship + 14 (upstream OM/Easypost drift) — tracked as an open item in the ticket file, no DM change.

#### Q6 — Returns (confirmation)

- **Posted 2026-11-19:** "6. Returns (confirm). A return does not change the expedite line's PoD — the return flow reverses the recognized revenue automatically and no additional PoD load is needed. Correct?"
- **ANSWERED 2026-11-19 (Aruna):** "6) yes, it is correct."
- Design impact: no return arm for expedite lines; return-typed orders are outside the pool gate entirely.

#### Q7 — Item-scope follow-up: is the line-type filter safe?

- **Posted 2026-11-19 by the user** (original pre-review wording — the two panel-caught inaccuracies are live in the thread: "today" describes the 3003 FSD, not live code, which still excludes the whole Shipping class per OTCM-150967; and the failure mode is silent non-emission, since the DM inner-joins the contract tables — no PoD would "go out". Neither affected the answer): "@ext.abhairapuneni@warbyparker.com one follow-up on your answer to Q1 (item scope). We have the PoD filter as Line Type = "Paid Expedite", as you confirmed. Two other items carry that same line type: "Next Day Air 30" and "Expedited 25". Contract creation today includes only "Expedited Shipping and Handling", so if one of the other two ever appears on a live order, the PoD would go out for a contract line that was never created. Are "Next Day Air 30" and "Expedited 25" legacy items that are no longer sold — so a filter on Line Type alone is safe — or should the PoD upload restrict to "Expedited Shipping and Handling"?"
- **ANSWERED 2026-11-19 (Aruna):** "Based on the test orders it seems better to include the line type filter so that we can make sure we are not excluding any other item which has "Paid Expedite" as line type. I will update the contract creation logic to include the Line type as condition as well."
- Design impact: **PoD filter FINAL — line type `WP_PAID_EXPEDITE` alone**; the 3003 contract-creation mirror is her action on the 3003 track (see P1 for the order-type facet her answer does not cover).

### Back-and-forth log

- 2026-11-19 — Vijay posts FSD v04 with the Shipping-Lines rule; comment assigned to Luis, cc Aruna/Emilio.
- 2026-11-19 — Six questions posted in the thread; thread reassigned to Vijay; Aruna answered all six same day.
- 2026-11-19 — Jira comment [988216](https://warbyparker.atlassian.net/browse/OTCM-159624) posted 15:47 (edited 15:50): full Q&A summary + description-drift corrections (AC 5 assumption, open questions 7/8) + implementation-readiness verdict.
- 2026-11-19 — Q7 follow-up posted by the user (pre-review wording; a 2-agent pre-post review had flagged fixes — user chose the original text).
- 2026-11-19 16:25 — FSD sync picks up Aruna's Q7 answer: line-type filter final; 3003 mirror committed.
- 2026-11-20 — "Update in the FSD thread" scare: sync + direct Drive API probe showed nothing new — Vijay's thread is Word-sourced (API-invisible); the notification was a re-surface of Aruna's Q7 answer.

## Implementation

### Phase 1 — DM change (oracle-integration-cloud)

Branch `OTCM-159624-rmcs-i-3001-pod-paid-expedite` off the stack tip `OTCM-153073-rmcs-i-3001-pod-canceled-covered-line`; stack on PR #1184, link with `gh stack link` after opening. File: `WP_RMCS_PROOF_OF_DELIVERY_DM.sql` (+ paired `.xdm.catalog` re-export — **user step** in the dev1 BIP editor, embedded SQL verified byte-identical before commit).

- New CTEs: `expedite_lines` (pool per design 1), `expedite_first_delivery` (order-grain MIN per design 2, pool-restricted), `expedite_pod_rows` (contract match + emit + three-path window + dedup per designs 3/4/6/7) — one UNION ALL arm.
- D6 scoped exclusion in `rmcs_lines_base`: `AND (NVL(l.line_type_code,'-') <> 'WP_PAID_EXPEDITE' OR h.order_type_code NOT IN ('WP_B2C','WP_B2C_CPU'))`.
- Comments per the code-comments rule (1–2 lines, no ticket/QA references); mark the P2 grain assumption if posted-unconfirmed.
- Pre-commit verification (fusion-sql, SELECT-only): full DM runs clean on dev1; A/B vs base on dev1 = zero diff on existing rows (checksum, harness precedent at [integrations/RMCS-I-3001/scripts/pod-window-harness/](integrations/RMCS-I-3001/scripts/pod-window-harness/)); simulated arm exercise on TEST (expedite census orders) — today emits 0 rows (no contract lines), proven by probe rather than full run.
- Pre-opening flow per `pr-workflow`: self-review, description to `tmp/pr_description.md`, independent `pr-review` panel, then slow suites N/A (SQL-only repo) — CodeQL + pr-title-check CI.

### Phase 2 — Monocle regression coverage (monocle_integrations, independent, can open first)

Branch off `main`. Test-only PR: integration tests with expedite-shaped seeded rows (PoD-only row: SUB_LINE_ID + qty 1 + date, all UPDATE columns blank) through `_oracle_proof_of_delivery_reader.py` → `_proof_of_delivery_import_models_mapper.py` → FBDI import action; orchestrator regression test proving pass-through. Keep the 100% coverage gate. No production code changes expected — if a gap surfaces, stop and re-plan. (Unit-level reader/mapper cases were dropped: the expedite row is shape-identical to a standard PoD-only row, already pinned by the existing unit suites — review-panel verified.)

### Phase 3 — QA / regression evidence (merge gate)

- dev1 A/B regression (AC 6/7): modified DM vs deployed DM over identical windows; zero-diff on existing arms; evidence captured (checksums + row counts).
- TEST arm exercise (AC 1–5): **precondition — an expedite contract line must exist** (3003 landing or functional manual FBDI seed, Aruna's precedent). Until then AC 1 is verified by simulation (already done by the panel to the exact timestamp).
- Post the audit-grade QA evidence comment on OTCM-159624 (skill `jira-qa-evidence`); QA moves the ticket, never us.

## PR breakdown (≤ ~400 changed lines each)

- **PR 1** — `[OTCM-159624] Add Paid Expedite arm to WP_RMCS_PROOF_OF_DELIVERY_DM` — oracle-integration-cloud — DM `.sql` (new arm + scoped D6 exclusion) + paired `.xdm.catalog` re-export — est. ~300–380 lines SQL — depends on: stacked on #1184 (unmerged stack tip); catalog re-export (user) — opens after pre-opening panel.
- **PR 2** — `[OTCM-159624] Cover the paid expedite PoD row in the proof-of-delivery upload tests` — monocle_integrations — reader integration + orchestrator regression tests — ~85 lines (tests only; 100% coverage gate) — depends on: nothing; can open before/alongside PR 1.

Sequencing notes: PR 1 is inert until 3003 creates expedite contract lines (semi-join matches nothing) — no feature flag needed, and oracle-integration-cloud merges at PROD promotion per repo convention. PR 2 is independent test coverage. Cross-repo order is safe in any sequence: monocle already passes generic PoD rows through (verified — decision 14).

## QA test-scenario matrix (requirement-traceable)

- **AC 1** expedite row dated at first delivered regular line — TP51K801FZ on TEST → expect 2026-11-02 15:39:52 — verified by panel simulation now; full DM run after contract-line seeding (QA precondition).
- **AC 2** filter = `WP_PAID_EXPEDITE` line type alone — code review + A/B (no item-number predicate anywhere in the arm).
- **AC 3** CPU date = pickup-task completion — TP56Y6005R (TEST, WP_B2C_CPU, expedite present; regulars 3–6 qcFail=Yes exercise the QC overlay; line 1 supplies the MIN) — probe + DM run post-seeding.
- **AC 4** qty = 1, no amount — DM output inspection on TEST.
- **AC 5** contract match required — 0 expedite contract lines on both pods → 0 rows today (probed); positive case post-seeding.
- **AC 6** no regression on existing arms — dev1 A/B checksum-identical (harness precedent); merge gate.
- **AC 7** branch inert until contract lines exist — 0-row runs on dev1/TEST pre-seeding (probed); arm emits after seeding.
- **Panel scenario — late-stamped delivery**: synthetic window case in the harness (delivery value before window, write inside window) → backfill path emits; mirrors AC-1 fixture's 2-day stamp lag.
- **Panel scenario — canceled expedite**: pre-fulfillment cancellation → no row; cancel-after-terminal regular lines still feed the MIN (Q6 consistency).
- **Panel scenario — multi-expedite order** (TEST has 1 order with 2 lines) → two rows, same order-grain date.
- **Panel scenario — stub headers**: DOO_REFERENCE twins of pool orders → no duplicate rows (header status filter + header_id aggregation).
- **Panel scenario — scoped D6**: Takeaway/Wholesale expedite lines keep the standard-arm path (no standard-arm diff for off-gate types in the A/B).
- **Panel scenario — REJECTED first load**: a rejected PoD suppresses re-emission until purge (inherited guard) — documented in the test plan; `P_ORDER_NUMBERS` run is the recovery path.

## Risks

- **Inert until 3003** (accepted): no expedite contract lines exist; AC 1 full-run verification blocked on seeding. Mitigation: simulation evidence + explicit QA precondition.
- **dev1 cannot exercise the new arm** (empty delivered population): new-arm behavior is validated on TEST; dev1 A/B proves only zero-diff. Disclose in the PR.
- **Template drift**: mapping template says ship + 14 vs Aruna's ship + 10 (upstream OM/Easypost logic); the DM reads the resulting date either way — no DM change; tracked as an open item.
- **P2 grain assumption**: split-shipment reading unconfirmed (0 divergent orders today); a contrary answer flips one aggregation, not the design.
- **REJECTED-first-load suppression**: inherited from existing arms; QA must know a rejected first load blocks a naive retest (purge or order-numbers run).
