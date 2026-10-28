# OTCM-149231 — AP-I-3006: fix the customer refund report failing on more than one order number (plan)

- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-149231
- **RICE**: AP-I-3006 — report `/Custom/WP Integrations/FIN/WP AP B2C Customer Refund Report.xdo`, data model `WP_AP_B2C_CUSTOMER_REFUND_DM`
- **Repo**: `oracle-integration-cloud` (one PR); optional regression guard in `monocle_integrations` (contract test)
- **Status**: **DONE 2026-10-28** — QA moved the ticket (12:32 local) on the posted evidence: comment 975346, stage-only S1–S8 console scenarios + 8 screenshots (attachments 361129–361136), 4-seat audit panel passed (byte-equal re-pulled, S4 re-run live; 184→135 point-in-time disclosed). dev1 + stage pasted (each re-download byte-equal; stage pre-paste backup at `/tmp/otcm149231_dev1/stage_prepaste_dm.xdm`); V1 dev1 5/5 + edge 5/5, V4 stage 9/9 incl. Tony's exact repro →1832625+1833635; V3 parity PASS; PR #1169 open at `5f11dedf`, merges at prod promotion. Post-closure follow-ups under Open items.
- **Independent check**: an independent agent re-derived the plan from raw inputs on 2026-10-27 — same root cause, same rollout, and a better fix shape than the first draft (adopted). Report + probe artifacts: `/tmp/otcm149231_independent/` (`report.md`, `live/proposed_fix_dm.sql`).

## Root cause (verified live 2026-10-27)

`P_SALES_ORDER_NUMBERS` is a text parameter with `multiple="true"` (BIP "comma-separated values"). BIP textually substitutes the quoted list wherever `:P_SALES_ORDER_NUMBERS` appears. OTCM-147272 ([PR #1139](https://github.com/WarbyParker/oracle-integration-cloud/pull/1139), merged 2026-10-20) added a scheduled-mode clause that references it outside `IN ()`:

```sql
OR (:P_FROM_DATE IS NULL AND :P_TO_DATE IS NULL
    AND :P_SALES_ORDER_NUMBERS IS NULL)
```

With 2+ order numbers that line becomes `AND 'TP477X00X3','TP4A2KG0NZ' IS NULL` — a comma expression list where Oracle expects a relational operator → **ORA-00920**. Every evidence-table row follows:

| Parameters | Result | Substituted fragment |
|---|---|---|
| none | works | `NULL IS NULL` |
| dates only | works | `NULL IS NULL` |
| one order | works | `'TPPH29G0A3' IS NULL` |
| CSV (2 orders) | **ORA-00920** | `'A','B' IS NULL` |
| dates + CSV | **ORA-00920** | same |

CSV worked before 147272 (the pre-#1139 text references the param only inside `IN (...)`): proven on stage 2026-10-27 — pre-147272 text + CSV → 2 rows (TP477X00X3/refund 1832625, TP4A2KG0NZ/refund 1833635).

**Deployed state**: dev1 (10-20 18:47Z), stage (10-19 18:54Z), prod (10-20 18:25Z) all run the same DM, SQL byte-identical to `origin/main`. The bug is live on all three pods. Stage's edit landed 3.5 h before the ticket's failing run. No open PR touches this DM (#990 carries only the `.iar` + lookup row).

**Call chain**: OIC `ProcessCustomerRefund` → monocle `POST /wp/customer-refund-processing` → `ParseCustomerRefundRequest` splits `order_numbers` CSV → `OracleCustomerRefundReader._report_parameters` re-joins with commas → `report_payload_template.xml` sends ONE `<typ:item>` holding the CSV → BIP splits it because `multiple="true"`.

## Why the ticket's two candidate fixes both fail

1. **"DM binds the parameter as a multi-value list"** — already the case, and it is the bug's enabler. Keeping multi-value means no safe scalar null-test for scheduled mode (any `IS NULL`/`NVL`/`CASE` occurrence breaks on 2+ values; the `sys.odcivarchar2list` count guard works but is exotic and leaves the landmine armed). Dropping the null-test instead would make orders-only runs match the catch-all and announce every held request — unacceptable.
2. **"monocle passes each order number as its own value"** — dead twice: the substituted SQL text is identical (still ORA-00920), and a live probe (stage, 2026-10-27) sending two `<item>` values returned HTTP 200 but BIP consumed only the FIRST value — silent incomplete announcements, strictly worse than the loud failure.

## The fix (chosen)

Two coordinated edits inside `WP_AP_B2C_CUSTOMER_REFUND_DM` — both required:

1. **Uncheck the multi-value flag** on `P_SALES_ORDER_NUMBERS` (`multiple="true"` → `multiple="false"`). The parameter binds as one ordinary VARCHAR2; `IS NULL` becomes a valid scalar test in every mode.
2. **Split the CSV inside the SQL**, one shared CTE consumed by both UNION branches (amended 2026-10-28 per pr-review topic A — the inline-duplicate form was the repo's only same-parameter inline split; house precedent for one parameter with many consumers is a prologue CTE, `SUBINV_FILTER` in `get-inventory-quantities-by-items.sql`):

```sql
-- Splits the order-number CSV; a null list yields one NULL key, which IN never matches.
WITH order_keys AS (
SELECT REGEXP_REPLACE(REGEXP_SUBSTR(:P_SALES_ORDER_NUMBERS, '[^,]+', 1, LEVEL),
                      '^[[:space:]' || UNISTR('\00A0') || ']+|[[:space:]' || UNISTR('\00A0') || ']+$', '') AS sales_order_number
FROM DUAL
CONNECT BY LEVEL <= REGEXP_COUNT(:P_SALES_ORDER_NUMBERS, ',') + 1
),
refund_data AS ( ...
      OR rem.invoice_reference IN (SELECT sales_order_number FROM order_keys)
      ... OR cm.ct_reference IN (SELECT sales_order_number FROM order_keys)
```

The `REGEXP_REPLACE` edge-strip covers tab/CR/LF (`[[:space:]]`) AND NBSP (`UNISTR('\00A0')` — `[[:space:]]` alone is ASCII-only and misses NBSP; monocle's Python `strip()` already cleans the production channel, so this guards direct BIP console runs). Header comment also gains the ceiling line: single scalar bind, max ~360 order numbers per run (4000-byte VARCHAR2). Null param → one NULL key → `IN` never matches → scheduled catch-all governs; uncorrelated, evaluated once.

No caller changes: monocle keeps sending one CSV string; the OIC form keeps collecting it; output columns unchanged → no `.xdo`, lookup-CSV, monocle, or OIC change.

**Validation (2026-10-27, inline-text form)**: fixed text with scalar CSV bind on stage returns the identical row set as the known-good pre-147272 text (same 2 refunds); all-null params run scheduled mode (155 rows stage, 187 dev1 — same as current text); re-run on dev1 in Luis's session: CSV shape parses, null shape row-equal.

**Re-validation (2026-10-28, amended CTE text — supersedes the above as the artifact under deploy)**, all via fusion-sql arbiter, read-only; fixtures from the scheduled captures (dev1: TNZXR4G0W1→1805514, TNZYCE00MJ→1805518; stage: TP477X00X3→1832625, TP4A2KG0NZ→1833635, CM rows TPG04MG09H→1863680, TPVKYP411D→1862695):
- 9/9 row-asserting shapes PASS: single/csv2/csv-with-space/csv-with-tab+NBSP on both pods, plus stage CM-branch CSV — every run returned exactly the expected (order, refund) pairs.
- 3/3 A/B old-live-vs-new row-equal on dev1: scheduled mode 187==187, October date window 185==185, single order 1==1 (multiset compare).
- `_datamodel.edited.xdm` re-spliced (5420-byte CDATA byte-equal to `new_dm.sql`, `multiple="false"` clean, rest untouched); artifacts + probes in `/tmp/otcm149231_dev1/`.
- Note: stage scheduled count moved 155→184 since 10-27 (QA data churn; dev1 steady at 187 — text behavior unaffected, proven by the A/B).

**Alternatives rejected**: keep multi-value + `odcivarchar2list` count guard (works, verified on dev1 — but exotic and leaves the class of bug armed); `COALESCE(:P) IS NULL` (ORA-00938 with one argument); `','||:P||',' LIKE` (per-row concatenation, worse readability); OIC-side form validation (doesn't fix the report, blocks a documented use case).

## Verification plan

Read-only legs via the fusion-sql arbiter / `run_bip_report.py`; pod writes (paste round-trip) follow oracle-write-confirmation at execution time.

- **V1 — 5-case report matrix on dev1 after the paste** (`run_bip_report.py`): none / dates-only / single / CSV / dates+CSV — all HTTP 200 with ROW-COUNT assertions (never 200-only: 200+0-rows is the silent half-paste signature). The **single-order leg is a row-asserting HARD GATE for stage promotion** (pr-review topic C — the comma-free single order is the dominant production shape): dev1 fixture TNZXR4G0W1 must return refund 1805514. CSV leg: TNZXR4G0W1,TNZYCE00MJ must return 1805514+1805518.
- **V2 — A/B old-live vs new** (`compare_sql_variants.py`): COVERED PRE-PASTE at SQL level 2026-10-28 (3/3 row-equal: none 187, dates 185, single 1). Post-paste there is no old-live on the pod to compare against; the V1 matrix is the post-paste proof.
- **V3 — catalog parity**: re-export `.xdm.catalog` (BIP UI Archive action — manual step for Luis), `xdm_catalog_sql.py` byte-compare vs repo `.sql`.
- **V4 — stage**: same 5-case matrix with row assertions (single TP477X00X3→1832625 is the gate here too); Tony's exact repro (`TP477X00X3,TP4A2KG0NZ` → 1832625+1833635); **CM-branch CSV** (`TPG04MG09H,TPVKYP411D` → 1863680+1862695, already SQL-proven 2026-10-28); one end-to-end ad hoc OIC run with two order numbers (pass order numbers ONLY — see Related issue below).
- **V5 — prod at promotion**: smoke CSV + single + scheduled-count; confirm next scheduled run clean.

## Rollout / sequencing

```
Ariel heads-up (OTCM-147272 comment or Slack) → dev1 paste (write confirmation)
→ V1+V2 → stage paste (write confirmation) → V4 → V3 re-export + parity
→ PR → review → prod promotion (write) → V5 → QA evidence comment on the ticket
```

- Base text = the LIVE text downloaded at edit time (equals `origin/main` today; re-check `catalog_ls.py` lastModified — Ariel is actively iterating).
- `xdm_set_sql.py --expect-old` guard on every paste: aborts if the live text moved.
- No emergency promotion: blast radius is ad-hoc multi-order runs (stage mostly); AP-I-3006's OIC flow is not in prod yet (#990 open). Normal window is fine.

## PR plan

| # | Repo | Title | Contents | Est. | Depends on |
|---|---|---|---|---|---|
| 1 | oracle-integration-cloud | `[OTCM-149231] Split the order-number list inside the AP-I-3006 customer refund data model` — **OPEN: [PR #1169](https://github.com/WarbyParker/oracle-integration-cloud/pull/1169)** (2026-10-28, `bug` label; parity gate PASS: SQL CDATA byte-equal to validated artifact, `multiple="false"`, only env churn) | `WP_AP_B2C_CUSTOMER_REFUND_DM.sql` (`order_keys` CTE + `multiple` off + ceiling line) + re-exported `.xdm.catalog` | ~25 lines + binary | Ariel heads-up; V1–V4 |
| 2 (optional) | monocle_integrations | `[OTCM-149231] Cover multi-order selection in the customer refund contract test` | `test/contract/__init__.py` — `CUSTOMER_REFUND_SALES_ORDER_NUMBERS` → two values (unskip requires seeded fixtures per the `ap-i-3006-customer-refund-test-data` skill) | ~10 | PR 1 on stage |

Monocle comment PR — **DROPPED per user 2026-10-28** (PR #2844 opened, then closed unmerged and branch deleted at user instruction): the CSV contract (single scalar bind, ~360-order ceiling) already lives in the DM header line and will be stated in PR 1's description; no monocle change.

## Coordination risks

- **OTCM-147272 (Ariel Sperduti, In Progress)** introduced the regression and owns this DM's current evolution; he has merged monocle #2776 (dates optional) and #2815 (negative amounts) and holds draft #2773 (dedup adapter — no file overlap). Flag the DM edit to him before pasting so he does not re-export from an older editor session and clobber the fix.
- Repo worktree is on the unrelated `OTCM-143188` branch — branch off fresh `origin/main`.

## Related but separate issue (not this ticket)

Tony's 10-22 comment on OTCM-149231: ad hoc runs now reach monocle with `start_date=None, end_date=None` — the form's dates get dropped in OIC (mapping or the dates-optional change). Lives in the AP-I-3006 OIC integration (#990). Affects how V4's e2e run is driven; may need its own ticket.

## Open items

- Prod paste at promotion + V5 smoke (CSV + single + scheduled count; confirm next scheduled run clean).
- E2E ad hoc OIC run (two orders through the form) — undecided; announces real refunds to stage payment services.
- dates+CSV combined coverage — the audit panel's adversarial seat flagged the dropped console scenario as the production failure shape (10-19 prod run and Tony's repro both sent dates + CSV): leave as-is, add a one-line boundary, or verify the combined predicate at SQL level (recommended).
- Dates-dropped follow-up ticket (Tony's 10-22 symptom: form dates never reach the Lambda): draft at `oracle-integration-cloud/tmp/otcm149231_dates_dropped_ticket.md`; filed BEFORE close per pr-review (_10/_13).
- fusion-sql `xdm_verify_sql.py` slices the first CDATA (the 95-byte description) instead of the `<sql>` CDATA — spurious FAIL on this DM; fix the script.
