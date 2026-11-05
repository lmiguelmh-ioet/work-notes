# RMCS-I-3001 — release the warranty PoD when a covered line is canceled pre-shipping

**Ticket:** [OTCM-153073](https://warbyparker.atlassian.net/browse/OTCM-153073) (Story, To Do, assignee Luis)
**Status (2026-11-04, ~21:05 UTC):** BUILD IN PROGRESS — work items 1-4 DONE (freshness gate green base 76eb6e55; E1-E5 applied uncommitted in `tmp/otcm153073-wt`; harness matrix 9/9 PASS commits `93a9e85`+`68c0c40`; live A/B dev1 5/5 + stage 5/5 IDENTICAL — QA-1/QA-2 satisfied). (5) dev1 fixture DONE + **QA-3 PASS** — order `TestCP1` (header 300000913502149): member A (line 1) delivered T1=2026-11-04 16:30:00Z; member B (line 2) canceled pre-shipping (fulfill CANCELED 16:30:53Z); warranty line 3; contract **55049** + 4 obligations loaded (manual Identify ESS 117205474). The `doo_lines_all` stamp blocker cleared 2026-11-04 ~21:00Z: scoped AutoInvoice (request 117206060, arg3 Default Date + arg15/16 SO range — both interface rows had the NULL trx_date trap) billed lines 1+3 as invoice **60106**, the DOO callback closed both fulfill lines (~50 s), and a Close Orders rerun (117206082, the verified recipe) stamped all three order lines at 20:53:44Z — line 2 **CANCELED**. QA-3 windowed arbiter A/B (window 20:50-21:00Z containing only the cancel write; order-numbers mode off): old DM **0 rows** (family held forever); new DM **3 rows** — .2 PoD line 3.2 dated T1 (16:30:00), U record line 3.3 DEFERRED end date T1+365 (2027-11-04), .3 PoD held; .1 (3.1) co-emitted as the family's first-ever batch (no upload yet, dedup suppresses after). **Production-path run DONE (ott Lambda, ~21:00Z):** `POST /rmcs/proof-of-delivery-upload` `{"sales_order_numbers": ["TestCP1"]}` → HTTP 204 (instance `otcm-153073-testcp1-qa3-20261104-2100`; payload must be a LIST — a bare string 422s); FBDI load ESS **117206105** (+106/107) SUCCEEDED; 4 PoD sublines PROCESSED (line 1 std 5504952016, 3.1/3.2/**3.3** 5504952017-19 — .3 uploads too: order-numbers mode skips the future-date hold, same as the 2026-10-23 fixtures); U row staged on 3.3 (DEFERRED + end 2027-11-04, INITIALIZED_FOR_UPDATE); post-upload re-extract of the same QA-3 window returns **0 rows** (dedup + U guard). (6) live half DONE — edited DM SQL uploaded to live dev1 `.xdm` (CatalogService `updateObject`; splice freshness-guarded `--expect-old`; re-download byte-identical 67,687 B); the paired `.xdm.catalog` needs the user's BIP-UI Archive re-export at PR time. Next: work item 7 (stage e2e, QA-12) → 8 (QA evidence comment) → PR flow. Skill updates applied (`om-order-lifecycle` cancel Step 9 + wave/date + subset-pick + dev1 trx id; `rmcs-test-data` coveredLine name + canceled-line-never-loads). Skill updates applied (`om-order-lifecycle` cancel Step 9 + wave/date + subset-pick + dev1 trx id; `rmcs-test-data` coveredLine name + canceled-line-never-loads).
**Prior status (2026-11-04):** DESIGN VERIFIED — 2-round review panel complete (round 1: 3 independent seats converged on the same mechanism; round 2: 2 adversarial seats, zero design-breaking defects, AC5 bit-identity proven live 52=52 on stage). All questions closed: Q1 (dev1 fixture too), Q2 (cancel path deferred — assume possible, revisit at fixture time), Q3 (all-canceled hold reading on record since 11-03, no objection — accepted), Q4 (ANSWERED by Aruna 2026-11-04: "post shipping cancellation is not allowed" — confirms the design's reading). No external asks outstanding.
**Standing decision (inherited, user 2026-10-19):** RMCS-I-3001/3002/3003 never reached production — no prod data exists; decide only on prod-correct behavior and simplicity. This absorbs the panel's rollout-backlog observation (O2 in Design verification): no backlog can exist anywhere, and dev1/stage have zero mixed families, so no post-deploy flush run is a gate.

## Sources

- FSD: [RMCS-I-3001 - Proof of delivery upload in RMCS - FBDI Approach](https://drive.google.com/file/d/1BZInnIPHh0s6zG6n6Q6I93yGBVjl28Z8/view). The FSD body says nothing about cancellation; the ruling lives only in the comment thread: [canceled covered line ruling](https://docs.google.com/document/d/1BZInnIPHh0s6zG6n6Q6I93yGBVjl28Z8/edit?disco=AAAB_Ztc5xA) (Aruna, 2026-11-03: a canceled covered line must not hold the family; the PoD goes out with the latest delivered member's date).
- DM under change: `BI Publisher Reports/Custom/WP Integrations/FIN/Data Model/WP_RMCS_PROOF_OF_DELIVERY_DM.sql` in oracle-integration-cloud — live on dev1 + stage byte-equal to the PR #1181 branch file (verified 2026-11-03, sha256 c7cf84dd).
- Prior plans: `.cursor/plans/rmcs-i-3001_cpu_qcfail_warranty_returns.plan.md` (OTCM-146798, closed 2026-10-23), `.cursor/plans/rmcs-i-3001_warranty_pod_support_360cc59e.plan.md` (OTCM-139313).
- PR stack (merges only at prod promotion per repo convention): #1105 (OTCM-139313) ← #1141 (OTCM-146798) ← #1181 (OTCM-152262, in QA/Review) ← **this change stacks on #1181's branch** `OTCM-152262-rmcs-i-3001-pod-source-line-id` (worktree `oracle-integration-cloud/tmp/otcm152262-wt`, head 76eb6e55).
- Harness: `integrations/RMCS-I-3001/scripts/pod-window-harness/` (`gen_synthetic_matrix.py` DUAL-fixture matrix + `gen_live_compare*.py` A/B wrapping the actual DM text; regenerable per DM edit).
- QA evidence format template: `oracle-integration-cloud/tmp/otcm152262_qa_evidence_comment.md` (OTCM-152262 style). QA evidence runs go through the ott Lambda (dev1) / stage Lambda per the `rmcs-test-data` skill; order creation per `om-order-lifecycle` (no cancel coverage — see Q2).

## Current implementation map

One file changes: `WP_RMCS_PROOF_OF_DELIVERY_DM.sql` (+ paired `.xdm.catalog` re-export). No OIC/lookup/monocle changes.

The warranty family mechanism today:

- `covered_family_members` (343-380): warranty line → covered lines (Warranty EFF char1 = FR id prefix-matches `source_line_id`). No status filter.
- `covered_member_rollup` (395-469): per member, fulfill rows joined three ways (`afl` any status, `efl` shippable, `cfl` terminal SHIPPED/AWAIT_BILLING/BILLED/CLOSED) + `cfld` details, `ptd` pickup dates, `cqfr` QC-fail resolution (pickup types only).
- `covered_member_dates` (470-484): `member_complete` = terminal row (+ delivery date on DELIVERY types) OR (has fulfill rows, none shippable, not pickup — the exemption).
- `covered_item_dates` (486-520): `HAVING MIN(member_complete) = 1` — the family holds until EVERY member completes; MAX takes latest dates; a QC-held member poisons the family's pickup fields to NULL.
- Emission: `warranty_pod_rows` (~1142-1168) standard arm (dates in window) + backfill arm (`covered_pod_last_update` in window AND `fulfillment_date <= :P_TO_DATE`); `warranty_u_rows` (~1218-1234) on GREATEST(creation, pod date, pod last update, detected) in window + end-date guard; `:P_ORDER_NUMBERS` mode emits regardless of holds; per-split and EFF dedups block re-emission.

**The defect:** a covered line canceled before shipping never completes — its fulfill rows are all CANCELED (never terminal) or it has none, and the exemption cannot fire (canceled fulfill rows keep `shippable_flag='Y'`). `MIN(member_complete)` stays 0 forever → the warranty PoD never goes out even though a sibling member delivered.

## Verified facts (read-only fusion-sql probes, dev1 + stage; panel-verified)

- Cancel signal: `status_code='CANCELED'` ⟺ `CANCELED_FLAG='Y'` exactly (440 dev1 / 511 stage lines, zero mismatches both directions, zero with OPEN_FLAG='Y'). `DOO_CANCEL_REQUESTED` (1,526 dev1) keeps the flag 'N' — mid-flight, NOT a cancel.
- Every fulfill row of every canceled line is itself CANCELED (442/442 dev1 rows, 511/511 stage rows); zero canceled lines have a terminal fulfill row, a delivery date, fulfilled qty > 0, or a fulfill-row fulfillment_date — on either pod, across four independent layers (DOO rows, DOO details, WSH bridge, RMCS billing). **DOO's cancel cascade erases fulfill evidence 100% of the time.**
- 899 canceled dev1 fulfill rows keep `shippable_flag='Y'` → the exemption cannot save them (the defect's mechanism).
- 1,656 OPEN dev1 lines have ALL fulfill rows canceled (re-orchestration flow) → fulfill-row-level cancel detection would over-fire catastrophically.
- 1,045 dev1 return lines reference a CANCELED line → filtering canceled members out of `covered_family_members` would break RMA attribution at scale.
- The cancel bumps the order line's `last_update_date`: freshest write on 100% of canceled lines (440/440 dev1, 511/511 stage), time-stamped, day-tile friendly.
- dev1: 27 covered members / 5 warranty lines, ALL open → dev1 A/B expectation is EXACTLY ZERO DIFF.
- stage: 60 canceled memberships = 16 distinct covered lines across 11 warranty families, ALL all-canceled, on orders with zero `vrm_source_doc_lines` rows (never invoiced, warranty line itself canceled) → DM-invisible. 33 of 60 are exemption-shaped (shippable='N', complete today); 9 of the 16 distinct lines shippable='N' + 7 'Y'.
- Zero mixed families, zero canceled QC-failed lines, zero canceled members on pickup-sourced families, zero multi-order-type families, zero partial cancels — on either pod. **The release path (mixed family) exists nowhere live: the synthetic harness and the fixtures are its only evidence.**

## The design (panel-consolidated, verbatim)

Membership is never filtered. The cancel is detected at the order-line level guarded by terminal-row evidence; the exclusion applies in `covered_item_dates`; the cancel's order-line write folds into the family's last-update channels so the EXISTING backfill arm re-selects the family in the cancel's window. 5 edits, 4 CTEs, ~20 lines, no new joins/CTEs.

### E1 — `covered_family_members` (343-380): project two columns, filter nothing

```sql
cl.status_code      AS covered_line_status,
cl.last_update_date AS covered_line_last_update,
```

Both functionally dependent on `cl.line_id` → DISTINCT grain unchanged (probed: 27=27=27 dev1, 1986=1986=1986 stage).

### E2 — `covered_member_rollup` (395-469): carry them through

```sql
MAX(CASE WHEN cfm.covered_line_status = 'CANCELED' THEN 1 ELSE 0 END) AS line_canceled,
MAX(cfm.covered_line_last_update) AS covered_line_last_update,
```

### E3 — `covered_member_dates` (470-484): the exclusion flag

`member_complete` stays byte-identical. Add:

```sql
-- Canceled pre-fulfillment: the order line is canceled and no fulfill row
-- reached a terminal state; a terminal row keeps today's behavior.
CASE
    WHEN line_canceled = 1 AND has_terminal_row = 0 THEN 1
    ELSE 0
END AS is_excluded_canceled
```

### E4 — `covered_item_dates` (486-520): gate, no dates, no poison, the fold

```sql
covered_item_dates AS (
    SELECT
        cmd.warranty_line_id,
        cmd.covered_order_type_code,
        -- The date MAXes need no exclusion wrap: every member date channel
        -- is terminal-gated upstream, so an excluded member's dates are
        -- already NULL.
        MAX(cmd.member_delivery_date) AS covered_delivery_date,
        MAX(cmd.member_fulfillment_date) AS covered_fulfillment_date,
        -- An excluded member's cancel write stands in for the fulfill write
        -- it never produced, so the cancel re-selects the family in the
        -- backfill arm.
        GREATEST(
            MAX(cmd.member_detail_last_update),
            MAX(CASE WHEN cmd.is_excluded_canceled = 1
                     THEN cmd.covered_line_last_update
                     ELSE cmd.member_fulfill_last_update END)
        ) AS covered_delivery_last_update,
        MAX(CASE WHEN cmd.is_excluded_canceled = 1
                 THEN cmd.covered_line_last_update
                 ELSE cmd.member_fulfill_last_update END)
            AS covered_fulfillment_last_update,
        CASE
            WHEN MAX(CASE WHEN cmd.is_excluded_canceled = 1 THEN 0 ELSE cmd.pickup_held END) = 1
                THEN NULL
            ELSE MAX(CASE WHEN cmd.is_excluded_canceled = 1
                          THEN cmd.covered_line_last_update
                          ELSE cmd.member_pickup_last_update END)
        END AS covered_pickup_last_update,
        CASE
            WHEN MAX(CASE WHEN cmd.is_excluded_canceled = 1 THEN 0 ELSE cmd.pickup_held END) = 1
                THEN NULL
            ELSE MAX(CASE WHEN cmd.is_excluded_canceled = 1
                          THEN NULL
                          ELSE cmd.member_pickup_pod_date END)
        END AS covered_pickup_pod_date
    FROM
        covered_member_dates cmd
    GROUP BY
        cmd.warranty_line_id,
        cmd.covered_order_type_code
    HAVING
        -- Every non-canceled member complete. MIN over an all-excluded
        -- group is NULL: an all-canceled family releases no row and holds.
        MIN(CASE WHEN cmd.is_excluded_canceled = 1 THEN NULL ELSE cmd.member_complete END) = 1
),
```

Load-bearing choices:

- **The fold is mandatory, not optional.** In the headline case (member A delivered long ago, member B canceled this week) every standard-arm date predates the window and today's `covered_pod_last_update` holds only A's old writes — a gate-only fix emits nothing in scheduled runs (verified arm by arm, both rounds). The fold fires the backfill arm; the .2 goes out with A's old PoD date; the U fires on the same write (its NVL flooring prevents NULL-poison); the .3 stays held by the future-date guard; dedups + window math block re-emission next window.
- The fold is a CASE inside existing MAX arguments — never a new GREATEST argument (Oracle GREATEST NULL-poisons on any NULL argument → would break every normal family).
- The pickup pair is the ONLY date channel wrapped: `qc_fail_resolution` (461-464) feeds `member_pickup_*` regardless of fulfill status, so a canceled QC-failed member would otherwise leak its redirect date and poison. `member_pickup_last_update` for an excluded member is provably always NULL (has_terminal_row=0 poisons its inner GREATESTs) — the fold substitutes into a provably empty slot.
- The fold sits in the poison CASE's ELSE branch → a family poisoned by a NON-canceled QC-held member stays poisoned.
- No explicit "≥1 date supplier" HAVING conjunct: a gate-passing family with all-NULL dates holds downstream exactly as today's complete-but-dateless families do (lines ~1124/~1216) — zero behavioral gain for one more branch.
- All-canceled family: MIN over an all-NULL set is NULL (probed live), `NULL = 1` UNKNOWN → no row → holds exactly like today's held families. No new row shape anywhere.

### E5 — comment updates (the edits falsify three existing comments; panel-checked wording)

- Rollup header (386-390): today conflates "not yet orchestrated" (still holds) with "canceled before orchestration" (now leaves the gate). Replacement must keep both halves: a member with no fulfill rows at all (not yet orchestrated) never completes and the family holds; a member whose order line is canceled before a terminal fulfill row leaves the gate in `covered_item_dates`.
- Item-dates header (486-491): "A member never completes when its shippable fulfill rows were all canceled … The family holds." — first clause stays true (`member_complete` unchanged), second becomes false for line-canceled members; replace with the gate/exclusion/re-selection description.
- Backfill-arm comment (~1160-1162): the channel description gains the cancel-write variant ("…or a covered member's cancel landed in this window").
- All ≤2 lines per comment, standalone, no ticket keys/dates/conversation refs.

## Rejected alternatives (with the evidence that killed them)

- **Filter canceled members inside `covered_family_members`** (Guillermo's FSD suggestion): (1) loses the cancel write → re-selection impossible → "holds forever" moves from the gate to the emission arms; (2) breaks `covered_replacement_dates` attribution — 1,045 dev1 return lines reference canceled lines (AC4); (3) cannot express pre/post-shipping (`has_terminal_row` does not exist at that layer → flips AC5).
- **Fulfill-row-level detection** ("all fulfill rows canceled"): 1,656 OPEN dev1 lines match — re-orchestration flow, live-data AC5 break at scale; also blind to the no-fulfill-rows shape.
- **`DOO_CANCEL_REQUESTED` as the signal:** a requested cancel is not a cancel (flag 'N', can fail).
- **Mark canceled members `member_complete = 1`:** all-canceled families PASS the gate and emit a NULL-dates row — a row shape that does not exist today; the NULL-drop HAVING avoids it.
- **Merge the write downstream in `warranty_lines_gated` via `NVL(GREATEST(...))`:** touches 2 extra CTEs and adds a GREATEST NULL-poison hazard the in-channel fold does not have.
- **Feed ALL members' line writes (not just excluded ones):** not bit-identical — a post-delivery line write (SHIPPED→CLOSED flip) would re-fire the backfill arm where today it cannot.
- **Extra evidence guards beyond `has_terminal_row`** (no delivery date / fulfilled qty = 0): provably redundant (delivery dates live on terminal rows; qty > 0 implies a terminal row; zero canceled lines with either on both pods), and the erased-evidence shape defeats ALL guards equally — see A1.

## Design verification (2-round panel, 2026-11-04)

Round 1 — 3 independent seats, same brief, no cross-visibility: all converged on the same mechanism (flag downstream, never filter; line-level detection + terminal guard; gate exemption + no dates + no poison; cancel-write fold mandatory). Consolidation merged the strongest forms per fork.
Round 2 — 2 adversarial seats attacking the consolidated design as-found (28 failed attacks total). Verdicts: every AC holds; zero design-breaking defects.

Decisive evidence:

| Claim | Proof |
|---|---|
| AC5 bit-identity | Full old-vs-new `covered_item_dates` A/B (verbatim chain incl. QC CTEs, 8 columns, MINUS both ways): **stage 52 = 52 rows, 0 diffs**; dev1 0 = 0. Textual collapse of all 5 touched expressions verified line-by-line; grain probes zero fanout |
| Fold's timestamp | Order-line write is the freshest write on 100% of canceled lines (440/440 dev1, 511/511 stage) |
| Oracle NULL semantics | Probed live: `MIN({NULL,1})=1`; `MIN(all-NULL)=NULL` → `NULL=1` UNKNOWN (row filtered); `GREATEST(date,NULL)=NULL` |
| All-canceled holds | 11/11 stage families: `min_today=0`, `min_new=NULL` — hold both ways; A/B new_only=0 |
| Exemption-vs-exclusion overlap (nastiest shape) | 33/60 stage canceled members complete TODAY via the exemption; removing a 1-scorer from a MIN set is gate-neutral in every mix; only 0-scorers' removal flips the gate — exactly the defect being fixed |
| AC4 | Replacement CTEs read no touched expression; cfm grain unchanged (line_id unique both pods); 44 stage return lines referencing canceled members keep attribution |
| Windowed release | Arm-by-arm trace (both rounds): arm 1 correctly silent, backfill arm fires .2 with old date, U fires on same write, .3 held, no re-emission, order-numbers mode holds all-canceled (NULL guards outside the mode OR) |

Panel notes folded into this plan:

- **O1 — the erased-evidence limitation is structural, not hypothetical.** DOO's cancel cascade erases fulfill evidence 100% of the time → the `has_terminal_row` guard has never been exercisable; any future post-ship cancel of a covered member WILL be excluded (family releases without its dates). Accepted as A1; Q4 asks functional to sign it with this evidence.
- **O2 — deploy backlog:** absorbed by the standing decision (no prod data; zero mixed families anywhere).
- **O3 — live A/B legs are zero-diff by construction;** the harness matrix and fixtures carry the release path's entire burden (QA matrix below).
- Trivial comment fixes (in E3/E5 above): E3 comment ≤2 lines and PICKUP_TASK-safe wording; E5 rollup header preserves the not-yet-orchestrated half.
- Pre-existing multi-order-type fanout at the `warranty_lines_base` join (warranty_line_id only) widens in theory — zero multi-type families on either pod; one harness case documents it (QA-11).

## Questions — exact texts and response history

### Q1 — dev1 fixture scope — ANSWERED 2026-11-03 (user)

- **Context:** dev1 has zero canceled covered members, so the dev1 A/B delta is empty by construction; the ticket's AC6 asks the dev1 A/B to show diffs limited to canceled-member families.
- **Question:** accept an empty dev1 delta, or build a canceled-member fixture on dev1 so the dev1 A/B demonstrates the release?
- **Answer (user, 2026-11-03):** option (a) — build the canceled-member fixture on dev1 too, so the dev1 A/B delta demonstrates the release.

### Q2 — how to cancel a line pre-shipping (fixture mechanics) — DEFERRED (user, 2026-11-04): assume possible

- **Context:** neither `om-order-lifecycle` nor `erp-oeh` covers line cancellation; no tooling exists. Fixtures must cancel at the LINE level and let DOO cascade (never cancel fulfill rows directly — that is the 1,656-line re-orchestration shape, panel-verified).
- **Decision (user, 2026-11-04):** assume a single order line can be canceled before shipping; do not ask functional now. Not needed for implementation (work items 1-4: DM edit, harness matrix, live A/B) — only for the fixtures (work items 5, 7). Revisit at fixture time: try the REST cancel ourselves first; ask functional only if that fails.
- **Superseded draft (kept for the record; the 2026-11-03 two-track plan's functional ask):** "Hi @ext.rkyatham@warbyparker.com — for the OTCM-153073 test fixture on stage we need a sales order where a warranty covers two frame lines, one frame line is canceled before shipping, and the other delivers. Is there a standard way you cancel a single order line before shipping (OM UI or REST), or should we drive it another way? We are trying the REST cancel ourselves in parallel. cc @ext.abhairapuneni@warbyparker.com @ext.elopez@warbyparker.com"
- **Log:** 2026-11-03 — answered (user): two tracks (try REST ourselves + ask functional in parallel). 2026-11-04 — superseded (user): defer the ask, assume cancellation is possible, revisit at fixture time.

### Q3 — all-canceled family outcome — ACCEPTED ON RECORD (posted 2026-11-03, no objection)

- **Context:** Aruna's ruling covers a family where at least one covered line delivers. For every-covered-line-canceled there is no date to send. The design (and AC3) holds the family with no PoD and no error — consistent with her point that a canceled line never invoices, so there is no RMCS impact.
- **Resolution (user, 2026-11-04):** the reading is already on record — the 2026-11-03 post in the ruling thread stated it verbatim: "Our reading: if every covered line is canceled, there is no delivery date, so the report keeps holding the PoD. Please correct us if you disagree." No objection received → intrinsically accepted; no re-ping needed. AC3 stands as designed.
- **Log:** 2026-11-03 — reading posted in the ruling thread. 2026-11-04 — closed as intrinsically accepted (user).

### Q4 — post-ship cancel exclusion sign-off — ANSWERED 2026-11-04 (Aruna)

- **Context (panel round 2, both pods):** DOO's cancel cascade erases all fulfill evidence 100% of the time (every fulfill row flips to CANCELED; zero terminal rows, delivery dates, or fulfilled quantities survive on any canceled line, across DOO rows, DOO details, the WSH bridge, and RMCS billing). The design distinguishes pre- vs post-shipping cancels by surviving terminal evidence — but that evidence never survives, so a line canceled AFTER shipping would be excluded too: the family would release without that member's dates.
- **Posted text (user, 2026-11-04 — confirm landed wording at the next FSD sync):** "One more finding from our data checks. When a line is canceled, Oracle removes all traces of its fulfillment: every fulfillment record on the line changes to CANCELED. We verified this on dev1 and stage. So the report cannot tell two cases apart: a line canceled before shipping, and a line canceled after it shipped. In the second case, the warranty PoD would go out without that line's delivery date. Our reading: a shipped line is never canceled. We found no such case in our data checks. It comes back through a return (RMA) instead. This change does not touch the return flow. Please confirm that reading. If a post-shipping cancellation flow exists that we must handle, tell us."
- **Why it matters:** AC5's "post-ship cancel keeps today's behavior" is vacuous on real data; this is the design's last unverified premise.
- **Answer (Aruna, 2026-11-04, verbatim):** "post shipping cancellation is not allowed"
- **Design impact:** none — confirms the reading the design already proceeded on. There is no post-shipping cancellation flow to handle; shipped lines come back through returns/RMA (untouched, AC4). The `has_terminal_row` guard stays as insurance. A1 closed as confirmed.
- **Log:** 2026-11-04 — drafted (from panel evidence); rephrased STE-style per user request; adversarial review pass before posting (2 minimal edits applied: unambiguous split ask, evidence clause on the reading); posted by the user 2026-11-04. 2026-11-04 — **ANSWERED by Aruna** (verbatim above).

## Assumptions

- **A1 — erased-evidence post-ship cancel is indistinguishable from pre-ship** (structural, panel-proven): excluded; family releases without its dates. CONFIRMED by Aruna 2026-11-04 (Q4: "post shipping cancellation is not allowed") — the shape cannot occur; the `has_terminal_row` guard stays as insurance.
- **A2 — canceled member with a completed QC replacement loses its redirect date** (AC2's letter): the family may hold despite delivery-via-replacement. Zero such lines on either pod (QC-fail populations: dev1 249 OPEN/22 CLOSED, stage 424 OPEN/203 CLOSED — zero CANCELED). Not worth a separate functional question; flagged in QA notes.
- **A3 — partial cancels keep gating** (a partial-cancel line keeps status ≠ CANCELED; its remaining quantity still delivers). Zero partial-cancel lines on either pod. `canceled_quantity` is not BI-exposed (ORA-00904) — unprobeable, untouched by construction.
- **A4 — window tiling:** re-selection inherits the backfill arm's assumption that scheduled windows tile contiguously; a run gap loses the release until an order-numbers run. Pre-existing for deliveries; now also load-bearing for cancels. Harness case QA-4 documents it.
- **A5 — multi-order-type fanout (pre-existing):** `warranty_lines_base` joins `covered_item_dates` on warranty_line_id only; two passing type-groups would fan a split into two base rows. Zero multi-type families on either pod; QA-11 covers the shape synthetically.

## Implementation plan

### PR table

| PR | Repo | Contents | Est. lines | Depends on |
|----|------|----------|-----------|------------|
| 1 — `[OTCM-153073] Release warranty PoD when a covered line is canceled pre-shipping` | oracle-integration-cloud | `WP_RMCS_PROOF_OF_DELIVERY_DM.sql` (E1-E5) + re-exported `.xdm.catalog`; branch `OTCM-153073-rmcs-i-3001-pod-canceled-covered-line` in a new worktree (`tmp/otcm153073-wt`) **stacked on** `OTCM-152262-rmcs-i-3001-pod-source-line-id` | ~25 SQL + comments (+ binary re-export) | PR #1181 stack (base branch, in QA/Review) |
| 2 — harness matrix extension | integrations | `pod-window-harness`: new synthetic cases below (gen_synthetic_matrix.py) + expected-output updates | ~200 | PR 1's DM text (the harness wraps it) |

### Work items (build order)

1. **Freshness gate** (per `oic-integration-lookup`): fetch origin, check open PRs touching the DM, three-way live-pod diff (origin/main vs dev1 vs stage) — confirm the base is still byte-equal before editing.
2. **Apply E1-E5** to the `.sql` in the new worktree.
3. **Harness synthetic matrix** (PR 2): add the cases below; run the DUAL matrix — proves the release path before any pod is touched.
4. **dev1 + stage live A/B** (`gen_live_compare`, old vs new DM text): expect EXACTLY ZERO diff on both pods (QA-1/QA-2).
5. **dev1 fixture** (Q1): build the mixed-family order per `om-order-lifecycle`, load the contract (VRM rows), cancel one covered line pre-shipping at the LINE level (track 1: REST discovery; track 2: Q2 functional answer), with the delivered member's date BEFORE the run window; run the extract through the ott Lambda; verify .2 + U.
6. **`.xdm.catalog` re-export:** upload the new DM to dev1 (CatalogService — a pod WRITE, needs per-rule confirmation at the time), verify, re-export the catalog for PR 1.
7. **Stage end-to-end** (QA-12): same fixture shape on stage via the stage Lambda.
8. **QA evidence comment** in the OTCM-152262 style; user posts to the ticket.

### PENDING CONFIRMATION markers

None in the SQL — Q3/Q4 change no build default (A1/A2 stand).

### Sequencing / gates

- PR 1 stacks on #1181's branch and merges only at prod promotion (repo convention) — it can stay open approved while Q3/Q4 and the stack's QA proceed.
- Q3/Q4 answers do not block the build; a ruling against a default becomes a follow-up.
- The two FSD texts (Q2 functional ask, Q3, Q4) are posted by the user; edits reported back get recorded verbatim in their logs.
- Deploy note: seat B found RMCS-I-3001 in neither OIC lookup CSV (`WP_BIP_REPORT_DETAILS_LKP`, `WP_CMN_INT_UTIL_LKP`) — consistent with the flow never having reached prod; confirm the scheduling wiring when the stack promotes (not this PR's scope).

### QA test scenarios (requirement-traceable)

Fixture constraints (panel-verified): cancel at the LINE level and let DOO cascade; the warranty line itself must stay open and invoiced (VRM rows loaded) — stage's real all-canceled orders have the warranty line canceled and are DM-invisible; the delivered member's PoD date must PREDATE the run window, or the standard arm fires and the test proves nothing about re-selection.

| # | Scenario | Traces | Where | Expected |
|---|----------|--------|-------|----------|
| QA-1 | Full-extract A/B, 2026-06-01→run-date | AC5 | dev1 (`gen_live_compare`) | EXACTLY ZERO diff (no canceled members on dev1) — **SATISFIED 2026-11-04: 5/5 pairs identical** |
| QA-2 | Same | AC5 | stage | ZERO diff (52=52 proven by panel; re-run post-edit) — **SATISFIED 2026-11-04: 5/5 pairs identical (18 warranty rows incl. same-day emissions)** |
| QA-3 | Mixed DELIVERY family: member A delivered long ago, member B line-canceled pre-ship in-window | AC1 | dev1 fixture (work item 5) + harness | .2 emits in the cancel's window with A's old date; U emits alongside; end date = A + 365; .3 stays held — **SATISFIED 2026-11-04: old DM 0 rows; new DM .2 dated T1 + U end T1+365, .3 held** |
| QA-4 | QA-3 but the cancel write OUTSIDE the window | A4 | harness | no emit (documents window tiling) |
| QA-5 | All-canceled family (warranty invoiced, every member canceled) | AC3 | harness + stage e2e | no row, no error, holds |
| QA-6 | Canceled member shippable='N' (exemption-shaped — 9 of stage's 16 lines) | AC2/AC5 | harness | excluded from the gate; gate decided by the other members |
| QA-7 | Canceled QC-held member on a pickup-sourced family | AC2 | harness | poison stripped; redirect date dropped; family releases on the surviving member's date (holds if none) |
| QA-8 | Post-ship-cancel control: line canceled WITH a terminal fulfill row (synthetic — DOO never produces it) | AC5 guard | harness | member NOT excluded; byte-identical path |
| QA-9 | Shape-1 cancel (line canceled, zero fulfill rows) | AC2 | harness | excluded |
| QA-10 | Canceled member with a completed QC replacement | A2 | harness | redirect date dropped; family holds if it was the only date source |
| QA-11 | Multi-order-type family (two covered type-groups pass) | A5 | harness | documented fanout shape (pre-existing mechanics) |
| QA-12 | Stage end-to-end: partial-cancel family, contract loaded, delivered member's date predates the window | AC1/AC6 | stage (work item 7) | .2 + U emit in the cancel's window with the delivered member's date — **SATISFIED 2026-11-05 on dev1 (re-scoped: stage pod outage; stage leg stays open). TestCP3: ott Lambda request 6d1d2ca3-af47-4fc6-8c09-8d0393d36c02, 5 rows (.2 dated T1=2026-11-05, U on 3.3 DEFERRED end 2027-11-05=T1+365, .3 future-dated), FBDI ESS 117208796, U landed (53020 SRC_ATTRIBUTE_DATE1=2027-11-05), re-extract 0 rows** |
| QA-13 | RMA/returns regression | AC4 | existing regression suite + harness return cases | byte-identical |

## QA / functional back-and-forth (post-implementation)

### 2026-11-04/05 — work items 5-7 session log

- **Work item 6 (live DM) DONE both pods**: dev1 (2026-11-04) and stage (2026-11-04 21:13:49Z, byte-exact vs the worktree .sql). Stage gotcha: stage `_datamodel.xdm` has TWO CDATA spans (description first, SQL second) — `xdm_set_sql.py` splices the FIRST and would corrupt it; used a targeted splice on the CDATA byte-equal to the baseline. Remaining: user's BIP-UI Archive re-export of `.xdm.catalog` at PR time.
- **Callback investigation (user question)**: no Identify callback fired after the TestCP1 PoD load — not PR #2874's `KeyError: 'UPDATE_PROCESSED'` (that crash lives inside monocle's callback handler; zero invocations = not reached). Break is OIC-side dev1 flakiness. The every-~10-min stage error tickets are OIC calling the upload with `from_date: "T00:00:00"` → FastAPI 422 (distinct from #2874; the one real #2874 crash is OTCM-153172). Malformed bare-string invoke auto-created OTCM-153290 (noise; user to close).
- **Stage outage** (2026-11-04 ~21:20Z → 2026-11-05 AM): `fscmRestApi` 302 → oracle.com splash, Akamai 504s; BIP tier stayed up. Stage QA-12 leg blocked; user re-scoped QA-12 to dev1.
- **Work item 7 (QA-12) DONE on dev1 2026-11-05** — fixture `TestCP3` (header 300000913635069): line 1 delivered T1=2026-11-05 14:05:00Z (delivery 1524131), line 2 line-level cancel → Close Orders ESS 117208786 stamped `doo_lines_all.status_code='CANCELED'`, line 3 warranty; contract 55072 (manual Identify ESS 117208747 — callback did not fire, same dev1 flakiness); AutoInvoice 117208754 → invoice 61106; lines CLOSED. Run: ott Lambda `POST /rmcs/proof-of-delivery-upload` `{"sales_order_numbers": ["TestCP3"]}` → 204, request 6d1d2ca3-af47-4fc6-8c09-8d0393d36c02 (cold start). Extraction 5 rows; import submitted request_job_id 117208796; VRMPRCBL 117208801 SUCCEEDED. Post-state: obligations ORA_FULLY_SATISFIED dated 2026-11-05 (14:04:20, inside load window); doc line 53020 `SRC_ATTRIBUTE_CHAR4=DEFERRED`, `SRC_ATTRIBUTE_DATE1=2027-11-05`; post-upload re-extract 0 rows. **PASS.**
- **Open**: stage QA-12 leg (postponed by outage — evidence comment must disclose); work item 8 (QA evidence comment; user posts); `.xdm.catalog` re-export DONE 2026-11-05 09:57 (dev1 BIP Archive; CDATA byte-exact vs final .sql 658da45d272b; envelope churn = LastModifiedTime stamps only); PR stacked on #1181.
- **Comment-final pass DONE 2026-11-05 (post-assumption-post)**: `_2`/`_3` comment fixes applied (comment-only — comment-stripped executable SQL byte-identical to the QA'd text; final .sql sha256 `658da45d272b`, +49/−16, 7 hunks). Assumption-close message to Aruna POSTED by user (Slack). Dev1 parity chain DONE: splice asserted live CDATA == QA'd text (dfe8b2ddf372, no drift) → `updateObject` uploaded 2026-11-05 → re-downloaded CDATA byte-exact vs final .sql → report smoke parses (TestCP3 order-numbers, 0 rows, dedup holds). **Stage re-upload BLOCKED**: fa-evdi-test 503 Oracle splash (same outage as 2026-11-04 21:20Z) — rerun the stage leg of this chain when the pod recovers; stage still carries the comment-prior text (executable-identical). QA evidence draft updated: `_5` (7 hunks +49/−16, new hash), `_6` time-bound QA-1/AC6, Boundary 6 (QC-failed-then-canceled fail-closed silent hold, reprocessable; mirrors posted assumption 1), deploy-verification row. Pre-push freshness CLEAN: origin/main has no DM file (stack chain builds it: #1105→#1141→#1181→this PR), #1181 tip == worktree base 76eb6e55, no other open PR touches the file. Remaining: stage re-upload when the pod recovers; QA evidence comment post (user); ticket wrap-up. **PR OPENED 2026-11-05**: [#1184](https://github.com/WarbyParker/oracle-integration-cloud/pull/1184) — commit da8846cc (2 files, +49/−16), base #1181's branch, label `enhancement`, body = user's edited tmp/pr_description.md.
- **Pre-opening review DONE 2026-11-05** (light tier, 4 panel + 2 triage seats; scratch `/tmp/otcm153073_review/`): no blockers. Decided: 2 comment fixes (`_2` terminal-gated overclaim, `_3` non-canceled→non-excluded) + 2 evidence-draft fixes (`_5` 7 hunks +48/−16, `_6` QA-1 time-bound parenthetical) — ALL queued for ONE final .sql pass after the functional ruling (single pod re-upload + catalog re-export chain). Skipped: `_4` (explicit-CASE taste refactor, both seats). **Gray `_1` RESOLVED (user 2026-11-05, final)**: answered on record — the 2026-11-04 FSD affirmation (post-shipping cancellation not allowed; shipped lines return via RMA) + dev1 evidence (348/353 failed lines CLOSED/OPEN, never CANCELED) close the QC-redirect-vs-cancel shape. NO code change, NO PR hold. Documented as a fail-closed boundary (silent hold, reprocessable) in the QA evidence draft. User posts an assumption-close message to the FSD ruling thread (two assumptions: QC-failed-replaced line never canceled; all-canceled family keeps holding — the AC3 nudge rides along). (Earlier same-day plan — ask functional and hold the PR — superseded by the user.) **Gray `_7` (user: A — constraint stands)**: if this shape is ever implemented, pod-date arm only; the panel's second arm is GREATEST-NULL-poisoned. Recorded as a standing constraint.

## Next steps

1. User reviews this plan → go to build.
2. Q4 posted 2026-11-04 — confirm the landed text at the next FSD sync and record it in Q4's log. (Q2's functional ask is deferred to fixture time.)
3. Work item 1 (freshness gate) on user go.
