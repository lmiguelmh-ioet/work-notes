# OTCM-149231 — AP-I-3006: Fix the customer refund report failing on more than one order number
- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-149231
- **RICE**: AP-I-3006
- **Repos**: oracle-integration-cloud
- **Status** (as of 2026-10-28): QA evidence posted (comment 975346 + 8 console screenshots, audit panel passed); fix live on dev1 + stage; PR #1169 open, merges at PROD promotion
- **Plan**: [projects.AP-I-3006.OTCM-149231.plan](projects.AP-I-3006.OTCM-149231.plan.md)

## Outcome
- The customer refund report no longer raises ORA-00920 when `P_SALES_ORDER_NUMBERS` holds more than one order number.
- The parameter is now one scalar bind; the SQL splits the CSV itself via the shared `order_keys` CTE. No caller changes.
- Validated live on dev1 and stage with row-asserting matrices, including the ticket's exact two-order repro.

## What shipped
- oracle-integration-cloud [PR #1169](https://github.com/WarbyParker/oracle-integration-cloud/pull/1169) — OPEN: paired `WP_AP_B2C_CUSTOMER_REFUND_DM.sql` + re-exported `.xdm.catalog` (`order_keys` CTE, `multiple` off, ~360-order ceiling line). Merges at PROD promotion.
- dev1 DM paste 2026-10-28 — deployed via `catalog_upload.py`; re-download byte-equal to the uploaded artifact.
- stage DM paste 2026-10-28 — deployed, same artifact; pre-paste backup at `/tmp/otcm149231_dev1/stage_prepaste_dm.xdm`.
- QA evidence on OTCM-149231 2026-10-28 — comment 975346 (stage-only S1–S8 console scenarios) + 8 screenshots (attachments 361129–361136); 4-seat audit panel fixes applied before posting.
- Monocle comment PR — DROPPED per user 2026-10-28 (#2844 closed unmerged, branch deleted); the CSV contract lives in the DM header comment and PR #1169's description.

## Decisions
### Functional clarifications (Q&A)
1. Contract stays one CSV string — the OIC form and monocle keep sending a single comma-separated value; the split moved inside the SQL (2026-10-28 review, findings C/F).
2. Ariel Sperduti (OTCM-147272, the DM's other author) needed no heads-up — he is not editing the DM (user, 2026-10-28).

### Design decisions (ours)
1. Single scalar bind + one `order_keys` CTE consumed by both UNION branches — one split site instead of a duplicated per-branch expression.
2. Whitespace trim includes NBSP via `UNISTR('\00A0')` — plain `[[:space:]]` misses the paste-from-Excel character (review skeptic finding, proven live on dev1).
3. The ~360-order ceiling (4000-byte VARCHAR2) is documented in the DM header comment, not in monocle code (user, 2026-10-28).
4. BIP console is the QA evidence entry point for this DM-only change — user-authorized; the production OIC schedule was not driven (2026-10-28).
5. Evidence runs are named scenarios S1–S8 with screenshot files 1:1 — one numbering namespace, no V/R ids (user review, 2026-10-28; codified in the `jira-qa-evidence` skill).
6. The dates+CSV console scenario was dropped from the evidence — console date handling on ad hoc runs is standard BIP behavior, out of scope (user, 2026-10-28). The audit panel's adversarial seat flagged the drop as covering the production failure shape; resolution is an open item.

## Evidence
- 2026-10-28 dev1 V1 matrix 5/5: none 187, dates 185, single TNZXR4G0W1→1805514, csv2 →1805514+1805518, dates+CSV 185.
- 2026-10-28 dev1 edge matrix 5/5: 3-order CSV, trailing/leading/doubled comma, spaces — NULL elements inert.
- 2026-10-28 stage V4 matrix 9/9: none 184, dates 184, single TP477X00X3→1832625, exact repro TP477X00X3,TP4A2KG0NZ→1832625+1833635, CM CSV →1863680+1862695, dates+CSV, 3-order, trailing/doubled comma.
- A/B row-equal: new text vs old live text on dev1 — none/dates/single all multiset-equal.
- CM branch: dev1 waiver (zero CM rows in the 187-row scheduled capture); stage validated live (10 CM rows in its 184-row capture).
- Parity gate 2026-10-28: re-exported `.xdm.catalog` SQL CDATA byte-equal to the validated artifact; `multiple="false"` present; remaining delta is env churn only.
- QA evidence comment 975346 (2026-10-28): stage-only, BIP console entry point (user-authorized), S1–S8 scenarios incl. the ticket repro; screenshots attached 1:1 (`S1_none.png`…`S8_doubled_comma.png`). Panel re-verification: stage DM re-download byte-equal to the PR `.sql` (5420 bytes); S4 re-run live PASS; scheduled count point-in-time (184 at capture, 135 at 16:46 UTC after 49 holds released mid-window by the live stage integration).

## Test data
- Skill: `ap-i-3006-customer-refund-test-data` (preferred source).
- stage: TP477X00X3→1832625, TP4A2KG0NZ→1833635, TP3VP101RC→1833633; CM TPG04MG09H→1863680, TPVKYP411D→1862695.
- dev1: TNZXR4G0W1→1805514, TNZYCE00MJ→1805518, TNZYH00119→1808435.
- All verified single-row 2026-10-28; re-derive from a fresh scheduled capture before relying on them later.

## Open items
- Prod paste at promotion + V5 smoke (CSV + single + scheduled count).
- E2E ad hoc OIC run (two orders through the form) — undecided; it announces real refunds to stage payment services.
- dates+CSV combined evidence coverage — the audit panel flagged the dropped scenario; options: leave / one-line boundary / SQL-level predicate probe (recommended).
- Dates-dropped follow-up ticket: draft at `oracle-integration-cloud/tmp/otcm149231_dates_dropped_ticket.md` (Tony's 10-22 symptom: form dates never reach the Lambda) for Emilio to create in Jira.
- fusion-sql `xdm_verify_sql.py` slices the wrong CDATA (description, not `<sql>`) — spurious FAIL on this DM; fix the script.

## Artifacts
- Review/triage: `oracle-integration-cloud/tmp/otcm149231_review/triage_plan.yaml` (15 findings, all resolved)
- Working dir: `/tmp/otcm149231_dev1/` (edited XDM, `new_dm.sql`, matrix runners, `v*_*.out` evidence, stage backups, `cmp_rows.py`)
- Independent investigation: `/tmp/otcm149231_independent/` (2026-10-27)
- QA evidence draft: `oracle-integration-cloud/tmp/otcm149231_qa_evidence_comment.md` (master copy of comment 975346); screenshots: `oracle-integration-cloud/tmp/otcm149231_shots/` (8 PNGs, also ticket attachments 361129–361136)
- Audit panel reports: `/tmp/otcm149231_panel/reports/` (ephemeral, delete once open findings close)
