# ON-CALL: 2026-10-19 → 2026-10-26

- **Board**: [OEH list, 10-19 → 10-26, not Rejected/Resolved](https://warbyparker.atlassian.net/jira/software/c/projects/OEH/list?jql=project%20%3D%20%22OEH%22%0AAND%20created%20%3E%3D%20%222026-10-19%22%0AAND%20created%20%3C%3D%20%222026-10-26%22%0AAND%20status%20NOT%20IN%20(Rejected%2C%20Resolved)%0AORDER%20BY%20created%20DESC)
- **Playbooks**: [team.oncall](team.oncall.md) · monocle branch `on-call-agent-wip` → `on-call-agent/skills/` (30 skills, synced with main 2026-10-22)
- **Prev**: `projects.md` → ON-CALL: AGO25-AGO31 (pre-convention) · **Next**: —

## Ledger

- `10-14 08:17` · [OEH-80300](https://warbyparker.atlassian.net/browse/OEH-80300) · Comerica → EPM (ARCS) · daily "No Data to process" → dup of master OEH-76395 (Fifth Third purge race) · pre-rotation backlog, swept 10-24 · Rejected
- `10-15 08:17` · [OEH-81052](https://warbyparker.atlassian.net/browse/OEH-81052) · Comerica → EPM (ARCS) · daily "No Data to process" → dup of master OEH-76395 · pre-rotation backlog, swept 10-24 · Rejected
- `10-16 08:17` · [OEH-83241](https://warbyparker.atlassian.net/browse/OEH-83241) · Comerica → EPM (ARCS) · daily "No Data to process" → dup of master OEH-76395 · pre-rotation backlog, swept 10-24 · Rejected
- `10-17 08:17` · [OEH-85835](https://warbyparker.atlassian.net/browse/OEH-85835) · Comerica → EPM (ARCS) · daily "No Data to process" → dup of master OEH-76395 · pre-rotation backlog, swept 10-24 · Rejected
- `10-20 13:26` · [OEH-88425](https://warbyparker.atlassian.net/browse/OEH-88425) · WMS-I-1005 · pick confirm failure → C1 · pulled · Resolved (parent)
- `10-20 13:27` · [OEH-88426](https://warbyparker.atlassian.net/browse/OEH-88426) · WMS-I-1005 · pick confirm failure → C1 · pulled · Rejected (dup of OEH-88425)
- `10-20 13:27` · [OEH-88427](https://warbyparker.atlassian.net/browse/OEH-88427) · WMS-I-1005 · pick confirm failure → C1 · pulled · Rejected (dup of OEH-88425)
- `10-20 13:28` · [OEH-88429](https://warbyparker.atlassian.net/browse/OEH-88429) · WMS-I-1005 · pick confirm failure → C1 · pulled · Rejected (dup of OEH-88425)
- `10-21 15:01` · [OEH-88586](https://warbyparker.atlassian.net/browse/OEH-88586) · WMS-I-1005 · pick confirm failure → C1 · pulled · Rejected (dup of OEH-88425)
- `10-21 16:26` · [OEH-88620](https://warbyparker.atlassian.net/browse/OEH-88620) · IN-I-2017A · receiving inbound failure → already put away (concurrent-completion race) · pulled · Rejected
- `10-22 02:02` · [OEH-88627](https://warbyparker.atlassian.net/browse/OEH-88627) · GL-I-1060 · payroll to Anaplan failure → trial-balance CSV already in S3 Archive 1s before ticket (upload-step race) · pulled · Rejected
- `10-22 06:11` · [OEH-88628](https://warbyparker.atlassian.net/browse/OEH-88628) · WMS-I-1031 · 8-digit external_id 16340304 (not an FR ID) → business-approved discard · pulled · Rejected
- `10-22 14:07` · [OEH-88641](https://warbyparker.atlassian.net/browse/OEH-88641) · AP-I-1039 · Expensify partial failure (113/76/37) → probes healed, self-heal via hourly retries · pulled · Parked (question to Sean, comment 973842) — awaiting functional confirmation
- `10-22 14:27` · [OEH-88642](https://warbyparker.atlassian.net/browse/OEH-88642) · WMS-I-1009 · Oracle inv txn import failure (28/27/1) → 1 row INV_NO_NEG_BALANCES (Sloatsburg Subinventory Transfer, item 10001058) → Andrew's team monthly close · pulled · Rejected (comment 973850)
- `10-22 17:06` · [OEH-88665](https://warbyparker.atlassian.net/browse/OEH-88665) · AP-I-1039 · Expensify partial failure (150/148/2) → probes healed, self-heal via hourly retries · pulled · Parked (question to Sean, comment 973843) — awaiting functional confirmation
- `10-23 14:06` · [OEH-88674](https://warbyparker.atlassian.net/browse/OEH-88674) · AP-I-1039 · Expensify partial failure (145/1/144, near-total) → probes healed + Sean confirmed integrated (comment 973641) · pulled · Rejected (self-healed, comment 973844)
- `10-20 08:17` · [OEH-88345](https://warbyparker.atlassian.net/browse/OEH-88345) · Comerica → EPM (ARCS) · daily "No Data to process" → dup of master OEH-76395 (Fifth Third purge race) · pulled · Rejected
- `10-21 08:17` · [OEH-88483](https://warbyparker.atlassian.net/browse/OEH-88483) · Comerica → EPM (ARCS) · daily "No Data to process" → dup of master OEH-76395 (Fifth Third purge race) · pulled · Rejected
- `10-22 08:17` · [OEH-88631](https://warbyparker.atlassian.net/browse/OEH-88631) · Comerica → EPM (ARCS) · daily "No Data to process" → dup of master OEH-76395 (Fifth Third purge race) · pulled · Rejected
- `10-23 08:17` · [OEH-88667](https://warbyparker.atlassian.net/browse/OEH-88667) · Comerica → EPM (ARCS) · daily "No Data to process" → dup of master OEH-76395 (Fifth Third purge race) · pulled · Rejected
- `10-24 08:17` · [OEH-88828](https://warbyparker.atlassian.net/browse/OEH-88828) · Comerica → EPM (ARCS) · daily "No Data to process" → dup of master OEH-76395 (Fifth Third purge race) · pulled · Rejected
- `10-22 15:30` + `10-24 01:08–01:29` · [OEH-88644](https://warbyparker.atlassian.net/browse/OEH-88644) + 70 · WMS-I-1005 · Oracle planned-outage burst (503 at intake products fetch, zero Oracle side effects) → C2 · swept 10-25 · investigation complete — 13 orders self-healed (re-sent with new FRs), 57 never re-sent; disposition pending Luis's call (handoff `/tmp/wms_i_1005_sweep/HANDOFF.md`)

## Resolution clusters

### C1 — WMS-I-1005 — pick confirmation failure burst

- **Tickets**: [OEH-88425](https://warbyparker.atlassian.net/browse/OEH-88425) (parent — Resolved) · [OEH-88426](https://warbyparker.atlassian.net/browse/OEH-88426) · [OEH-88427](https://warbyparker.atlassian.net/browse/OEH-88427) · [OEH-88429](https://warbyparker.atlassian.net/browse/OEH-88429) · [OEH-88586](https://warbyparker.atlassian.net/browse/OEH-88586) (Rejected as dups) — 5 total
- **Signature**: order 1192224 (TO/LSLO) — WMS picked more than the open remainder per item; "Overpicked lines found" false positive (picked == SUM(requested) per item; remainder lines still Released to warehouse)
- **Playbook**: new `wms-i-1005-overpick` skill (branch `on-call-agent-wip`, `c7b069361`) — Branch A corrected-payload replay at remainders; never plain-reprocess
- **Outcome**: resolved 10-23 — replay `POST /wms/pick-confirmation` HTTP 201 (uuid `3856d2c6-0499-4efd-83b1-8cea885ba989`), 3 remainder lines → Staged; parent Resolved with evidence attachments + comment, 4 dups Rejected. Root cause: overpick check compares running picked totals vs open remainder per item — OTCM bug pending. Watch for a follow-up `PickConfirmNotAllowedError` ticket → reject pointing to OEH-88425

### C2 — WMS-I-1005 — Oracle planned-outage burst (88644 + 70)

- **Tickets**: [OEH-88644](https://warbyparker.atlassian.net/browse/OEH-88644) (10-22 OAuth token connect failure) + 70 tickets (10-24 01:08–01:29 ET, `503 Planned Outage` from `fa-evdi-saasfaprod1`) — 71 total, one per order
- **Signature**: intake `POST /wms/pick-confirmation` dies at its FIRST Oracle call (products fetch) — before queue/resolution/any Oracle write. Zero side effects per ticket
- **Sweep findings** (10-25, full handoff `/tmp/wms_i_1005_sweep/HANDOFF.md`): 13/70 orders self-healed (Manhattan re-sent with NEW FR ids ≤30 min, all processed); 57/70 never re-sent and their fulfillment requests are gone from Oracle shipping; FR→order report is a pre-confirmation locator (zero rows for ANY FR older than hours — normal aging, not a bug); replay dead for all 71 (resolution would fail for the 57, double-confirm the 13)
- **Disposition**: pending Luis's decision — 13 healed → reject w/ evidence (ticket↔order map via the request-id bridge first); 57 unhealed → options (a) reject w/ evidence, (b) escalate to OM re fulfillment state (recommended), (c) park w/ evidence + follow-up
- **Skill updates**: `wms-i-1005-pick-confirm` playbook gained an "Outage bursts" section (log map, CW grep caveat, ticket↔order bridge, order-level self-heal, replay matrix); cross-skill notes into `aws-cloudwatch-logs`, `fusion-sql`, `oncall-triage-loop` — worktree edits UNCOMMITTED pending Luis's approval

## Knowledge delta

- Skill `in-i-2017a-receiving` created from OEH-88620 triage (branch `on-call-agent-wip`, `4d52262ac` + template fix `686979c67`): two-stage receiving verification — linesToPutAway + inboundShipments + errored-receipts + pending-putaway reports; reject-if-complete per OEH-65095.
- Payables rule (triage-loop skill updated 10-24, user directive): Payables (AP) tickets are special — money-out to vendors. Every Payables disposition must first answer the financial-impact question (vendor payment outcome of reject/replay); unclear → park/escalate, never force. Band read from the summary's third `|` segment. Also added to the hard-rules checklist.
- Triage-loop freshness rule (skill updated 10-24): a matched skill > 7 days since its last `on-call-agent-wip` commit or recorded review passes a full adversarial review BEFORE application; verdicts/fixes logged here reset the clock. First catch: `gl-i-1060-payroll-anaplan` (44 days) — APPROVE-WITH-CHANGES, 5 fixes in `86e4c8546` (fatal-Reject + GET-verified final status; env docs → `~/projects/ioet/.env` + `.env.prod` subshell; `Error/trial_balance_payroll` prefix; canonical S3 console host).
- Bash gotcha: `${var:-{}}` appends a literal `}` when var is SET (the first `}` ends the expansion) — write `${var:-"{}"}`. Killed the first OEH-88627 execute run with a jq parse error before any write.
- `.env.prod` repointed to wp-primary (`844647875270` / Argon-Contractors) 10-24 — it previously resolved to wp-dev. Refresh via the `aws-login` skill on ExpiredToken; session lifetime ~13h.
- WMS-I-1031 "Cannot determine source for external_id" (8-digit) failures are a **business-approved DISCARD** per OEH-88372: Krista Potter approved 2026-10-20 (Slack screenshot on the ticket; LMS sends numeric sequences, not FR IDs; the updates don't pertain to WP). Deterministic ValueError — reject citing OEH-88372, NEVER replay, no code change, file stays in `Error/LSLO|LLAS/`. Applied 10-21→10-24 across OEH-88592, 88601, 88612–88619, 88628, 88643 (50+ and continuing). OEH-88645 is a DIFFERENT category (Manhattan connect failure — transient) — do NOT discard it under this approval.
- Skill `wms-i-1031-unknown-source-reject` created 10-24 (`401acee93`): codifies the OEH-88372 discard — reject-only, never replay. `check-s3-evidence.sh` parses the body's `RXN <id>` as authoritative and aborts rc 3 if it ≠ the ticket's external_id (substring-regex alone let `6340304` pass against `16340304`). Passed the new pre-commit adversarial review (APPROVE-WITH-CHANGES, 5 fixes). `wms-i-1031-reprocess` "When NOT to use" now points at it for this signature.
- Skill `comerica-arcs-duplicate-reject` created 10-24 (`92b21dd7c`): the daily "No Data to process" Comerica→EPM ARCS failures are duplicates of master OEH-76395 (Fifth Third purges the file after ERP's SFTP pull; Tony Huang keeps the master open while ARCS automation is worked). Reject-only, Jira-only — no replay, no file artifact. Guard: master must be open (terminal → abort rc 3); matcher refuses the master itself. Passed pre-commit adversarial review (APPROVE-WITH-CHANGES, 11 fixes; sibling extraction pipelines hardened in `a8f98555c`). Sweep JQL excludes OEH-76395. Retire the skill when the master closes.
- Prod monocle Lambda invoker: AWS profile `oic4` (`oic-monocle-integrations-lambda-prod`) — `oic`/`oic3` 403 on prod. User keys live in Secrets Manager `oic-monocle-integrations/ENV/lambda_user_keys`. Prod URL in `notes/urls.md`.
- OEH workflow quirk: terminal `Resolved` status is reached via the transition named **Complete** (id 231) from `Promote to Production`; the transition named "Resolved" (id 141) only loops back to Testing. Path: Not Started → Triage → In Progress → Test → Testing → Complete.
- OEH workflow quirk 2 (verified live 10-25): reject transition names are asymmetric — from Not Started it is id 41 named "Rejected", from Triage id 2 named "Reject"; both land on Rejected. Scripts must alias-fallback (F2 pattern in `4ac528405`).
- Skill `wms-i-1009-negative-inventory` passed the 46-day freshness review 10-25 (APPROVE-WITH-CHANGES): F1–F4 fixes in `4ac528405` (fatal transitions + alias fallback + GET-verified final status; env subshell docs; precedent deep-link focusedCommentId=801660; jira-oeh workflow-guide Triage transitions corrected). First post-review application: OEH-88642 — Gate A adversary FIT CONFIRMED (5/5 same-shape rejects incl. same-day Sloatsburg Replen→Active; no disposition split; no dup; main has no neg-balance automation). Sibling OEH-88731 is a DIFFERENT signature (Lambda `_retrieve_transaction_types` failure) — separate pop.
- Triage queue rule (triage-loop skill updated 10-25): queue = `assignee IS EMPTY OR assignee = ext.elopez` — Emilio Lopez is the automation default, not a human owner. jira-oeh guard fix `ffb5561cd`: Payables band accepted in the search-jql mandatory filter (fuzzy `summary ~` matching still needs the exact OR-of-both-bands pattern).
- Self-heal checks are ORDER-level, never message-id-level (C2, 10-25): senders regenerate per-attempt ids on retry — Manhattan re-sent 13/70 outage-failed orders with NEW FR ids; an FR-level Archive scan falsely concluded "zero healed". Codified in `oncall-triage-loop` ("Retried items get new ids") and the `wms-i-1005-pick-confirm` playbook.
- The WMS-I-1005 FR→order report (`WP_ORDERS_BY_FULFILLMENT_REQUEST_ID`) is a PRE-CONFIRMATION locator: mapping wiped when the delivery line closes — confirmed orders unresolvable within hours, cancelled FRs immediately. Zero rows for an old FR proves nothing. Consequence: an outage burst older than ~a day is NOT replayable (re-driven files die at FR resolution). Manhattan `ERP_ORDER` does not key DOO headers in any probed column — no order→SO shortcut once the mapping is gone.
- OEH ticket ↔ order bridge when the ticket carries no order: description `AWS Lambda Instance ID` = the Lambda request id → Insights on the MAIN group → `Processing WMS pick confirmation request. UUID: <uuid>` → Error file `scale_pick_conf_<ts>_<uuid>.json` → payload. Codified in `aws-cloudwatch-logs` + playbook.
- CloudWatch business ids are NOT greppable (C2): payloads ship as OTel extras to New Relic; CW holds marker lines only. FR/order-id filters return zero even where the invocation ran. Search by request id / UUID / literal phrases. Log split: REST intake → MAIN group; queued async processing (FR resolution, ~7.6k lines/day) → EVENTS group.
- `WSH_DELIVERY_DETAILS` DFF columns (`SRC_ATTRIBUTE2` = FR id) are unindexed — an `IN (...)` probe is a ~70–85s full scan on prod (fusion-sql caveat added). BIP CSV output prints only the parameter echo for an empty data set — probe with `attributeFormat=xml` to distinguish empty-data from format problems.

## Open tickets

### [OEH-88641](https://warbyparker.atlassian.net/browse/OEH-88641) — AP-I-1039 Expensify partial failure (37 of 113)

- **Status**: Triage, assigned to on-call (Luis Mamani) — **parked awaiting functional**.
- **Path**: `ap-i-1039-expensify-partial-failure` skill, executed 10-24 → path "question" (park to Sean). Skill on `on-call-agent-wip`, **commit still pending user approval** (x2 protocol: 2 authors, 2 adversarial reviewers; survivor B + consolidated fixes).
- **Evidence** (probed 10-24, prod `fa-evdi-saasfaprod1`, re-confirmed healed at execute time): WP AP Expensify Payments Error Report for ESS load `142161630` EMPTY; interface residue 0 rows (`ap_invoices_interface` + `ap_interface_rejections`, load-id-only filter — the import id `130794374` is BU-wide and matches 49 wrong-file rows, never use it as the filter); OIC instance `XBiPYM5DEfGzMRcI0JVxFA`. All 37 failed records self-healed via hourly retries.
- **Comments posted**: comment `973842` (10-24) — evidence summary + ask Sean Jung to confirm integration, CC Tony Huang; passed the x2 comment gate (2 verifiers, both PASS) and the skill was patched so `--execute` emits the gate-approved wording.
- **Waiting on**: Sean Jung's confirmation on the ticket.
- **Next action**: re-run `./skills/ap-i-1039-expensify-partial-failure/scripts/resolve-ticket.sh OEH-88641` when Sean answers — the master guard picks up his confirmation and opens the close path (healed + integrated → close Rejected self-healed).
- **Watch-outs**: Payables — the failed records never became invoices, so no duplicate-payment risk; never a manual FBDI re-submission; a repull (OIC rerun) only after Sean's "good to repull", as a separately-confirmed Oracle write. Siblings: OEH-88665 (parked, below), OEH-88674 (Rejected 10-24), OEH-88676 (repull handoff, below — clearance only, NOT a close candidate).

### [OEH-88665](https://warbyparker.atlassian.net/browse/OEH-88665) — AP-I-1039 Expensify partial failure (2 of 150)

- **Status**: Triage, assigned to on-call (Luis Mamani) — **parked awaiting functional**.
- **Path**: `ap-i-1039-expensify-partial-failure` skill, executed 10-24 → path "question" (park to Sean). Same motion as OEH-88641.
- **Evidence** (probed 10-24, prod `fa-evdi-saasfaprod1`, re-confirmed healed at execute time): error report for ESS load `142183020` EMPTY; interface residue 0 rows (load-id-only filter; import id `130813974` is BU-wide, never the filter); OIC instance `WrLbrc5cEfGL_bvX5uM3kg`. Both failed records self-healed via hourly retries.
- **Comments posted**: comment `973843` (10-24) — evidence summary + ask Sean Jung to confirm integration, CC Tony Huang; passed the x2 comment gate (2 verifiers, both PASS).
- **Waiting on**: Sean Jung's confirmation on the ticket.
- **Next action**: re-run `./skills/ap-i-1039-expensify-partial-failure/scripts/resolve-ticket.sh OEH-88665` when Sean answers — master guard picks up his confirmation → close Rejected (self-healed).
- **Watch-outs**: same as OEH-88641 — Payables, no duplicate-payment risk, never a manual FBDI re-submission.

### [OEH-88676](https://warbyparker.atlassian.net/browse/OEH-88676) — AP-I-1039 Expensify partial failure (2 of 141)

- **Status**: Not Started — **repull handoff** (skill exit 4). Holds ONLY a functional clearance; NEVER close on it (almost wrongly closed 10-24 on the clearance alone).
- **Path**: `ap-i-1039-expensify-partial-failure` skill, guard reads `repull-approved`.
- **Evidence** (probed 10-25, prod `fa-evdi-saasfaprod1`): error report for ESS load `142273458` EMPTY; interface residue 0 rows (load-id-only filter; import id `130894124` is BU-wide, never the filter); OIC instance `shGzj88lEfGL_bvX5uM3kg`.
- **Comments posted**: none by us. Sean Jung's clearance comment `973728` (10-23 17:42): "fixed in Expensify and is good to repull into Oracle" — a CLEARANCE (data fixed, action ours), not a delivery.
- **Waiting on**: Luis asking Ariel (the OEH-77713 operator) what the actual repull steps were (10-25 decision) — until the mechanism is recorded, no delivery-check comment and no repull click.
- **Next action**: once Ariel answers, record the verified repull procedure in the skill handoff (step 2) and this entry; then re-run `resolve-ticket.sh OEH-88676` and follow the handoff — 1. DELIVERY CHECK (read-only; ask Sean or check the Payables UI; do NOT assume the hourly retries delivered — in the 77713 precedent the on-call engineer RAN the repull). 2. If not delivered, run the repull per the now-verified procedure (house oracle-write confirmation; NEVER a manual FBDI re-submission). 3. Delivery confirmation lands on the ticket → re-run → close Resolved (fixed in Expensify, delivered).
- **Watch-outs**: Payables. The delivery confirmation must use a guard-recognized phrasing ("Repulled, invoice created." / "confirm repulled" / "confirm pulled into erp" / "successfully integrated" / "integrated into Oracle" — affirmative, no "?", no "will/should") or the guard reads `none` and the ticket stays parked.

### [OEH-88644](https://warbyparker.atlassian.net/browse/OEH-88644) + 70 — WMS-I-1005 Oracle-outage burst (cluster C2)

- **Status**: Not Started (all 71) — investigation complete, disposition pending Luis's decision. NO Jira/Oracle writes made.
- **Evidence** (full inventory `/tmp/wms_i_1005_sweep/HANDOFF.md`): intake died at products fetch (503 Planned Outage) before any Oracle write (root cause traced via OEH-88704 request id `fd119e99-93b9-4d23-983b-04d069abb187`); 13/70 orders self-healed via Manhattan re-sends with new FR ids; 57/70 never re-sent, fulfillment requests gone from Oracle shipping; FR report zero rows for all 71 (normal pre-confirmation locator aging); replay dead for all 71.
- **Next action**: (1) rebuild healed/unhealed lists (wrapped-line contamination in `archive_order_hits.txt` — true split 13/57, not 13/59); (2) build ticket↔order map for the 13 healed via the request-id bridge; (3) Luis picks the 57 disposition — (a) reject w/ evidence, (b) escalate to OM (recommended), (c) park w/ evidence + follow-up; (4) execute per-ticket (x2 comment gate where a human is addressed).
- **Watch-outs**: NEVER replay any Error file for this cluster (double-confirm for the 13, resolution failure for the 57). Do NOT use the DynamoDB failures table (user directive — prefix-scan locator only). AWS session in `.env.prod` expires ~19:40 UTC 10-25.

## Handoff
