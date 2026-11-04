---
name: IN-I-2019 outage fix
overview: "Fix the IN-I-2019 3FED cycle count outage (OTCM-151550) with three PRs: error-chain hardening (plus WARNING logs on silent-success paths), dual-create serialization, and event-route ticket identity — plus one Jira comment (orphan-header per-header review request to functional). The monitor (WI5/AC4) and the disconnect self-recovery (WI4/AC3) are both OUT per user direction (2026-10-28): no follow-up commitment, each parked as a future implementation with an open question on whether it is needed. Scoped down after an adversarial plan review and two scope passes (2026-10-28)."
todos:
  - id: jira-comments
    content: "Post the WI6 orphan-header review-request comment on OTCM-151550 (functional reviews EACH of the 5 headers: keep or purge)"
    status: completed
  - id: pr1-error-chain
    content: "PR1: str(error) typing fix + FedEx handler hardening + timeout/logging on the ticket call + WARNING logs on silent-success paths (WI2 + AC4 partial)"
    status: completed
  - id: pr2-serialize
    content: "PR2: serialize the dual create on both routes + safe close_all_sessions (WI1) — opened as PR #2851"
    status: completed
  - id: pr3-ticket-identity
    content: "PR3: event-route ticket identity — rice_id fallback, origin_rice_id, file_path (WI3)"
    status: completed
  - id: followup-ticket
    content: PARKED — WI4 self-heal and WI5 monitor are future implementations with open questions (Q14/Q15) on whether they are needed; no ticket commitment
    status: cancelled
isProject: false
---

# OTCM-151550 — IN-I-2019 cycle count outage fix (3FED)

Ticket: https://warbyparker.atlassian.net/browse/OTCM-151550 · Repo: `monocle_integrations` · Integration: IN-I-2019 FedEx cycle count snapshot (REST + SFTP routes). Phase 1 discovery, Phase 2 Q&A, Phase 2.5 panel Round 1, an adversarial plan review (2026-10-28, verdict REJECT → all 15 findings verified and folded in; review-driven changes marked ◆), and a final scope pass are complete; all decisions locked 2026-10-28. Scope pass (user, 2026-10-28 PM): this ticket implements only the three acute fixes (WI1 race, WI2 ticket path, WI3 ticket identity) in three PRs — all self-healing / auto-recovery (WI4/AC3) moves to a follow-up ticket. Second scope pass (user, 2026-10-28 ~15:30): the questions are internal ("we made the ticket, so any question is for us") — the Q13 comment to the reporter is dropped unposted. WI5 monitor and WI4 self-heal are both OUT with no follow-up commitment, each parked as a future implementation with an open question on whether it is needed (Q14/Q15); the silent-success paths gain WARNING-level logs in PR1 instead of the monitor (AC4 partial). WI6 orphans: functional reviews EACH header via Jira comment and decides keep-or-purge per header.

## Context

No 3FED cycle count has landed in Oracle since 2026-10-24. (Update 2026-10-28 ~15:40: the 10-28 08:12 UTC SFTP run landed the non-AI count `3FED Snapshot 2026-10-28`, header 300001040406623, with 2,301 items, then failed on a serial-quantity data error — OEH-89097; the AI twin was never created.) The ticket names three defects — a concurrency race in the dual create, an unreliable/unfindable ticket path, and no disconnect recovery — plus empty orphan headers in prod. Evidence below was verified 2026-10-28 against CloudWatch (prod log group), New Relic (account 3902898), and read-only Oracle prod REST GETs.

## Verified evidence chain

10-25 09:32 UTC REST run (aws_request_id `1ab132ac-f949-40cd-a532-2a0553408c36`):
- AI definition create → 201, id `300001036816365`; its items batch (14 parts) posted 1 ms later → 400, all 14 parts `11404 Not Found` (body recovered from NR). Per the ticket, header 365 was later deleted by an unidentified actor — the 404s hit a committed parent, so Oracle-side create-visibility lag is the likely trigger and bounded retry absorbs this shape.
- Legacy close-all fired (isolation flag OFF in prod) mid-flight → non-AI items batches "Server disconnected" → `CycleCountCreationException` wrapped raw (`message=<exception object>`).
- Detached gather sibling died `RuntimeError: dictionary changed size during iteration` (unsafe `close_all_sessions` iteration, proven).
- Jira POST sent but abandoned mid-flight (invocation shut down 60 ms later; no response/error line) → no ticket for the run.
- finally path crashed: `TypeError: Object of type CycleCountCreationException is not JSON serializable` at `_fedex_exception_handlers.py:106` → Mangum plain-text 500.

10-26 14:03 UTC SFTP backfill (6 files): first run disconnected after the definition committed (OEH-88909); five others 400 `already exists` (run-date names collide by design). All six tickets named `s3_event_handler` (OEH-88909–88914).

Prod Oracle (read-only, 2026-10-28): 365 → 404 (deleted); 333 exists as `FEDEX Snapshot 2026-10-25`, zero items, `AutomaticallySchedule: Yes`, `Frequency: Daily` — orphan generating empty scheduled counts daily. Reader probe: `GET cycleCountDefinitions?q=CycleCountName='<name>'` works with exact match (`like '%…%'` returns 0 rows — use exact).

Prod Oracle (read-only, 2026-10-28 ~15:40 ET) — hard per-header evidence: direct-item GETs (`/cycleCountDefinitions/{id}`) + `child/countItems?totalResults=true`. ALL FIVE orphans verified 0 items; CORRECTION — all five (not just 333) carry `AutomaticallySchedule=Yes` / `Frequency=Daily` / `WorkdaySchedule="CC Schedule"`, `NextScheduledDateTime` null on all five. Per header: 085 `FEDEX Snapshot 2026-10-24` (10-24 09:31 UTC, morning run), 333 `FEDEX Snapshot 2026-10-25` (10-25 09:32 UTC), 952 `FEDEX Snapshot 2026-10-26` (10-26 09:31 UTC), 686 `3FED Snapshot 2026-10-26` (10-26 14:03:43 UTC — the OEH-88909 backfill run), 987 `3FED AI Snapshot 2026-10-26` (same run). Today's run: `3FED Snapshot 2026-10-28` = header 300001040406623 with **2,301 items** (created 08:12:33 UTC by the integration user — NOT an orphan); `3FED AI Snapshot 2026-10-28` and `FEDEX Snapshot 2026-10-28` do not exist (0 matches). OEH-89097 (2026-10-28 04:13 ET) is a serial-quantity data error (`Serialized line quantity (177) does not match serial count (164) for item 846864072957 in subinventory Replen`, `_inventory_snapshot_sftp.py:87`) — a different defect class from the race (the OEH-88666 serial thread), not this ticket.

Evidence-based corrections to the ticket framing: the AI create's items got a 400 (not a disconnect); the disconnects hit the non-AI batches after close-all. Header 365 committed and was deleted later, so "phantom id" is resolved.

## Decisions locked (user, 2026-10-28)

- Q2 = (a) purge + recreate on same-name replay.
- Q8 = NO flag flip: `http-client-session-failure-isolation` stays OFF in prod (ON in dev/stage/ott). Race fix carried by serialization + recovery. QA note: force the flag OFF in local/QA runs for prod parity.
- Q5 = keep BOTH intake routes (REST + SFTP→S3) — "we shouldnt be dropping anything".
- WI5 monitor (AC4): descoped — internal decision (user, 2026-10-28 ~15:30): "we only fix the issue here, no self heal, no alarm in scope." No reporter sign-off sought ("any question is for us"). Partial AC4 coverage instead: the silent-success paths log at WARNING (PR1). The full monitor (success-marker + New Relic alert) is parked for future implementation; open question Q14 on whether it is needed.
- WI6 orphans: keep-and-note — functional reviews EACH of the 5 headers via Jira comment and decides keep-or-purge per header (user, 2026-10-28 ~15:30: "We NEED to ask functional to review each one"). No cleanup script, no deletion spike from our side.
- Scope cut: dropped items-batch fan-out bounding, purge-rollback extension, file-date naming, in-repo scheduler, ticket-call retry.
- Panel Round 1 (2 seats) converged 3/3 with the approach; panel findings (str-typing TypeError; `_entry_points.py:252` close-all after event invocations) were verified and folded in. The originally skipped adversarial round was later executed as a dedicated adversarial plan review (user request, 2026-10-28): verdict REJECT with 15 findings; every load-bearing claim was independently re-verified against the repo before acceptance.
- ◆ Purge guard: automatic recovery only for same-name headers with ZERO items; a same-name header that already has items fails loudly (collision error → properly-named ticket) and is never purged — this prevents destroying committed counts in the 10-26 same-day-multi-file shape.
- ◆ The all-parts-11404 batch-400 retry inclusion is DROPPED: the adapter flattens 400 bodies into an `ERPActionError` string through the 8192-char log truncation (`_http_client.py:20`), so all-parts detection is unreliable exactly for large counts, and the create-visibility-lag theory is unproven. A typed batch-outcome error is a possible follow-up, not this ticket.
- ◆ AC1's completion mechanism re-mapped: PR2's serialization (no concurrent close-all during the Jira POST — the `atlassian` session lives in the shared registry, `_client_factory.py:91`) + PR1's typing fix (the invocation no longer crashes around the call). The ticket-call timeout is hang-hardening only, not the AC1 carrier.
- ◆ PR5 splits into 5a (lookup + guarded recovery + ESS poll-to-terminal) and 5b (connection-error retry/backoff) — superseded by the scope pass: both halves moved to the follow-up ticket.
- Scope pass (2026-10-28 PM, user): "auto recovering should not be part of the ticket" — WI4/AC3 (by-name reader, purge guard, recovery, ESS polling, retry/backoff, dev1 spike) moves OUT of this ticket. The shared `CreateCycleCount` base is untouched, so no ABB/WMS changes — the H3 wiring concern disappears with the recovery. The ◆ recovery-design decisions above stay as the parked starting design. Second scope pass (2026-10-28 ~15:30): no follow-up ticket commitment — WI4 parks as a future implementation with open question Q15 on whether it is needed.
- Adversarial round 2 (user request, 2026-10-28 PM): verdict APPROVE-WITH-CHANGES (0 blockers, 2 high, 3 medium, 5 low); all findings verified against the repo and folded in — dangling S5–S10 pointer inlined, Q13 justification corrected (silent-success shapes exist: `:70-76` 'Received' early return, `:120` non-empty-only ValueError, creator-failure swallow at `:245-247`), PR3 fleet-wide rename acknowledged, S1 prerequisites + PR2 failure matrix stated, plus the minor L1–L5 corrections.

## Rejected alternatives

- Enable isolation flag in prod — rejected by user (no flips).
- Per-create/per-request sessions — bigger HTTP-layer change than needed.
- `DummyCookieJar` for the `oracle_erp` session — addresses cookie sharing only, not the close-all cascade.
- `TaskGroup` instead of serialization (Seat B dissent) — no gain; serialization is the minimal fix.
- Drop the REST route (Q5 option b) — rejected by user.
- Auto-recovery inside this ticket (lookup + guarded purge + recreate / retry) — rejected by user 2026-10-28 PM ("additional changes or self healings should be in other tickets"); split to the follow-up ticket.

## Scope

In: IN-I-2019 snapshot flow (both routes), shared HTTP session layer, event-route ticket identity, WARNING logs on the silent-success paths, Jira documentation comments.
Out: disconnect recovery / retry / by-name lookup (WI4 — future implementation, open question Q15), the monitor (WI5 — future implementation, open question Q14), any change to the shared `CreateCycleCount` base or the ABB/WMS flows, serial-controlled counting functional decision (OEH-88666), empty-file count suppression, isolation-flag rollout, orphan header deletion (unless functional requests a per-header purge).

## Stages and PRs

All PRs titled with the Jira key, repo `monocle_integrations`, fresh branch off `main` each, <= ~400 changed lines including tests (100% unit coverage gate).

Three PRs (acute, independent — any order):
- PR1 `[OTCM-151550] Make the IN-I-2019 error chain survive failing runs` — WI2 + AC4 partial (WARNING logs), ~140 lines
- PR2 `[OTCM-151550] Serialize the IN-I-2019 dual cycle count create` — WI1, ~250 lines
- PR3 `[OTCM-151550] Carry RICE id and file path on event-route error tickets` — WI3, ~150 lines

Non-code deliverables (first, before or with the PRs): the WI6 orphan-header review-request comment (functional reviews EACH of the 5 headers: keep or purge). The Q13 scope-confirmations comment is dropped unposted — the questions were resolved internally (user, 2026-10-28 ~15:30).

Sequencing: monocle deploys by tag (stage, then prod with manual approval). PR2 changes daily-flow behavior → stage regression before prod. PR1/PR3 are error-path-only. Nothing touches the shared `CreateCycleCount` base or the ABB/WMS flows. Stage flag-parity blind spot ◆: feature flags are baked at packaging and dev/stage/ott all have the isolation flag ON, so no deployed stage run can reproduce the prod close-all cascade — stage evidence is regression-only for the race; the prod-parity failure exercise runs locally (S2). Each PR runs the full pr-workflow gate (fast checks → self-review → description file → user review → pr-review panel → slow suites → push).

## Future implementation (NOT this plan — WI4/AC3, parked)

The disconnect self-recovery is parked with open question Q15: is it needed at all? If the team decides yes, this plan's analysis is its starting design:
- By-name reader port + Oracle adapter: `GET cycleCountDefinitions?q=CycleCountName='<name>'` (exact match; verified against prod 2026-10-28); response includes `item_count` for the purge guard. Five verified `CreateCycleCount` construction sites: REST `_inventory_snapshot.py:31-38` (`**kwargs` passthrough), SFTP `_FlareCreateCycleCount` + factory `_wp_in_i_2019_fedex_inventory_snapshot/__init__.py:27-35`, ABB `_abb_cycle_count_creation.py:39-61`, WMS I-1010 `_wms_inventory_balances.py:69-95`, WMS I-1040. Make the reader a required param.
- dev1 spike first: does `InvCcPurgeCycleCountDetailsJob` delete the header or only the details? Header → purge + recreate; details-only → reuse header + purge details + reload items.
- Guarded recovery: a 0-item same-name header → poll the ESS purge to terminal (`get_job_details` in `_scheduled_job_manager.py`; the purge action is submit-only, completion arrives via callback) → recreate; a with-items header → loud collision error, never auto-purge a committed count.
- Retry/backoff on connection-error causes only (never 4xx), re-looking up per attempt. The 11404 batch-400 typed error is a possible extension.
- QA scenarios (one-liners, re-derived from this plan's deleted matrix): reader probe vs dev1/stage pod (found/not-found); dev1 purge spike (header-delete vs details-only decides the branch); stage recovery — a manually-created 0-item same-day header → poll to terminal → recreate → count lands; guard — a replay after a successful same-day run fails loudly and the loaded count stays untouched; ABB + WMS I-1010/I-1040 regression — first-run path unchanged, no purge submitted; disconnect retry — live if practical, else structural unit evidence.

### PR1 detail (WI2/AC1)
- `_domain/_integrations/_wp_in_i_2019_fedex_inventory_snapshot/_inventory_snapshot.py:168` (REST route): `message=error` → `message=str(error)`.
- `_domain/_integrations/_wp_in_i_2019_fedex_inventory_snapshot/_inventory_snapshot_sftp.py:90-92` (SFTP funnel — hygiene ◆, not a live defect: the S3 handler already str()s the exception and nothing JSON-serializes the message there; `str(error)` keeps both funnels consistent): `message=error` → `message=str(error)`.
- `_api/_handlers/_exception_handlers/_fedex_exception_handlers.py:103`: `error_description=exc.args[0]` → a `_get_error_description` static method on the decorator: `str(getattr(exc, "message", exc))` (matches `_base_exception_handlers.py:236`), except `RequestValidationError`, which keeps the `exc.errors()` array the 422 response has always shipped, JSON-encoded as `json.loads(json.dumps(exc.errors(), default=str))` so a non-serializable `ctx` value cannot crash the response build (amended 2026-10-29, user decision: the pre-push API suite caught that `str(exc)` on this path also embeds the raise-site traceback frame — internal paths in the partner response; encoding mechanism amended same day after the light review panel: `jsonable_encoder` itself raises on some `ctx` values, `default=str` is total and preserves the validator's message text).
- `_api/_handlers/_exception_handlers/_base_exception_handlers.py:245`: wrap the ticket-creator await in `asyncio.wait_for` (new settings key, ~30 s) + attempt/success/timeout step logs. The ticket key is logged by the creator's own `Created ticket:` line; the decorator's logs carry function name + request id (`WpErrorTicketCreator` returns None, so the key cannot sit on the decorator's line — amended 2026-10-29 after PR1 review). Hang-hardening only ◆: the 10-25 kill completed in ~33 ms, so no timeout could have fired, and on timeout `wait_for` cancels the POST — the same abandonment shape by design, so it is a last-resort guard and the response still returns. Every `HttpClient.request` failure path logs before raising (`_http_client.py:231,251,259`); the only silent exit is cancellation (`CancelledError` is `BaseException`), which matches the 10-25 evidence — the new step logs make any recurrence visible.
- Silent-success observability (AC4 partial; user, 2026-10-28 ~15:30: "A success that returns without doing anything should be logged with WARNING level"): the two verified silent-success paths in the REST route log at WARNING — the incomplete-file-set "Received" early return (`_inventory_snapshot.py:70-76`) and the empty/zero-match "N/A - N/A" return (`:120`) — so a silent day is greppable in CloudWatch/New Relic instead of invisible. Audit the SFTP funnel for the same shape during implementation and mirror the WARNING where present.
- Tests: raw-exception message JSON-serializable on BOTH funnels; handler with non-serializable `args[0]` → JSON 500; validation error keeps its errors array and a non-serializable `ctx` is encoded safely; creator hang → timeout logged + response returned; success → attempt/success step logs emitted (the ticket key is asserted in the creator's own suite); each silent-success path logs at WARNING.

### PR2 detail (WI1/AC2)
- `_inventory_snapshot.py:156-158` (REST route): `asyncio.gather` → sequential awaits with failure capture (AI fails → non-AI still runs → raise the AI error after; both counts attempted, no concurrency).
- `_steps/_cycle_count_creator.py:86-88` (SFTP route): same serialization.
- `_adapters/_http/_session_management.py:113-124`: rewrite `close_all_sessions` as pop-and-close by identity ◆ (loop popping keys and closing each popped session). The current code iterates the LIVE `_sessions.values()` view — the proven `dictionary changed size` RuntimeError source when `add_session` runs mid-close — and then `clear()`s, which would leak sessions added during the close window (cleared without being closed); pop-and-close fixes both.
- AC1 note ◆: this PR carries the ticket-call completion mechanism — with the dual create serialized, no close-all fires concurrently with the Jira POST (the `atlassian` session is in the shared registry and subject to the legacy close-all while the flag is OFF). Session recreation on demand already works in the session manager.
- Failure matrix ◆ (stated for reviewers): AI fails → non-AI still runs, then the AI error raises (both counts attempted); both fail → the first error raises after both attempts; a partial failure commits partial state (e.g. non-AI fully lands while the AI header may remain as a new empty orphan) and the run fails loudly with a correctly-named ticket. Interim behavior without WI4: a same-day replay after a partial commit hits the date-based name collision and fails loudly with a correctly-named ticket (manual cleanup until the follow-up ticket's recovery ships) — accepted interim, proven by S3's double-run.
- Tests: serial order on both routes; AI failure → non-AI runs, error raised after; no detached create tasks (integration level ◆ — the adapter's intra-create batch gather is unchanged and out of this test's scope); concurrent closes never raise; a session added mid-close is either closed or survives registered (never leaked-cleared). The AC2-named shape (two creates sharing one HttpSessionManager, one failing → no RuntimeError, deterministic outcome) is an explicit test ◆, pinned with a blocked mock transport so the close lands deterministically mid-flight (aiohttp close behavior on in-flight requests is timing-dependent).

### PR3 detail (WI3/AC1)
- `_event_handlers/_handler.py` S3 branch (~341-367): `function_name = getattr(event_error, "integration_name", None) or rice_id or self._FUNCTION_NAME`; add `origin_rice_id=rice_id`, `file_path=file_path` (both in scope). The SQS-DLQ path already sets origin fields (`:525-526`).
- `_domain/_integrations/_wp_error_ticket_creation/_request.py:14`: add `file_path: Optional[str] = None` to ErrorDetails; `_ticket_template/_error_ticket_template_generator.py`: render an `S3 File:` line when present (mirror the origin_rice_id pattern).
- Audit the Kinesis ticket path: expected no-op ◆ — it already propagates per-error `integration_name` (`_data_streams/_handler.py:93-99`); it lacks origin fields entirely, which stays out of IN-I-2019 scope.
- PR-description note ◆: the mention-config lookup key (`_handler.py:349`, `settings.jira_mention_ids.get(function_name)`) changes from `s3_event_handler` to the rice id for these tickets; no rice-id entries exist in any env's `jira_mention_ids`, so no mention behavior changes.
- Fleet-wide note ◆: the `or rice_id` fallback changes the ticket function_name for EVERY S3-bound integration whose exceptions lack `integration_name` (~25 bindings) — tickets stop being named `s3_event_handler` fleet-wide (the point of the fix, since they become findable per integration), but Jira filters/dashboards keyed on `s3_event_handler` change behavior. Call it out in the PR description and the review-request message.
- Tests: S3 failure → ticket named IN-I-2019 with origin_rice_id + file path; template renders the file line; existing DLQ path unchanged.
- Deferred from PR1 (review finding, user call 2026-10-29 — lands in PR3 if its budget allows, otherwise a small PR4): bound the event-path ticket calls with the same `asyncio.wait_for(settings.jira_ticket_creation_timeout_seconds)` + attempt/timeout logs — S3 (`_event_handlers/_handler.py:368`), SQS (`:534`), and the Kinesis handler (`_data_streams/_handler.py`) currently await `wp_error_ticket_creation` unbounded, so a Jira hang there stalls a whole event batch until Lambda timeout.

## QA test scenarios

We generate data, run, verify, and post evidence per the jira-qa-evidence skill; QA validates. Structural evidence pointer where a scenario is not executable end-to-end.

- S1 (AC1, PR1, REST route, stage): force a REST-route failure via the no-matched-lines `ValueError` (`_inventory_snapshot.py:120-124`). Prerequisites ◆: (a) the roosevelt feature flag must be ON in the stage config (the ValueError exists only in the roosevelt branch — verify before the run); (b) the stage S3 prefix must hold a crafted FedEx file whose lines pass the allowed-subinventory/lock-code filters but carry bogus UPCs matching no ERP product, so `unique_lines` is non-empty with zero matches (an all-invalid or empty file returns a silent 200 'N/A - N/A' instead — verified at `:120`); (c) invoke via the stage Lambda function URL with IAM auth (per the lambda-function-url-invoke skill). Verify: OEH ticket names IN-I-2019 and carries the AWS request id; caller gets a JSON 500 body (not plain text); CW shows the ticket attempt/success step logs. Also capture end-to-end timing against pre-PR2 baselines ◆ (PR2 evidence: serialization roughly doubles dual-create latency; the OIC caller timeout is a watch item). Evidence: ticket link, response capture, CW console links. Structural: PR1 unit tests (raw-exception messages on both funnels, non-serializable args[0], timeout, success logging).
- S2 (AC2, PR2, structural — the AC's own named deliverable): the concurrent-create test shape + the concurrent-close test. Live complement: local run with the isolation flag forced OFF (prod parity) and a stubbed Oracle endpoint that 500s the AI definition create (adapter-boundary mock in the local container) → no RuntimeError, no detached-task warnings, deterministic failure. Evidence: test refs + local run log.
- S3 (AC2 regression, PR2, stage): the normal daily SFTP flow lands both AI and non-AI counts with items in the stage pod; capture run duration against pre-PR2 baselines. Then run the flow a SECOND time the same day ◆: the replay hits the date-based name collision and fails LOUDLY with a correctly-named IN-I-2019 ticket (the accepted interim until the follow-up ticket's recovery ships; verify the loaded counts are untouched before/after). Caveat ◆: stage has the isolation flag ON and flags are baked at packaging, so this run cannot reproduce the prod cascade — it is regression evidence only; the prod-parity failure exercise is S2's local run. Evidence: Oracle GETs (definitions + item counts) + CW run lines.
- S4 (AC1, PR3, stage): drop a malformed file on the IN-I-2019 S3 path → ticket names IN-I-2019, carries origin_rice_id and the S3 file path. Evidence: ticket fields.
- S5 (AC4 partial, PR1, stage/local): exercise each silent-success shape — an empty or all-invalid file (zero-match → 200 "N/A - N/A") and an incomplete file set (→ 200 "Received") — and verify each emits a WARNING-level line in CloudWatch. Evidence: CW log captures per shape.

Non-code:
- S11 (AC5, Jira): the orphan review-request comment with hard evidence (per-header name, creation run, countItems=0, schedule fields; target: the OEH ticket the user picks — OEH-88909 or OEH-89097; functional reviews EACH header and decides keep-or-purge per header). Evidence: the comment + functional's per-header replies. A requested purge is handled as its own follow-up (ESS InvCcPurgeCycleCountDetailsJob + validation).
- S12 (AC4 + AC3): DROPPED — the scope-confirmations comment (Q13) was resolved internally and never posted. The monitor and the self-heal park as open questions Q14/Q15 (future implementation, no commitment).

## QA / functional back-and-forth (post-implementation)

No exchanges yet. Post-implementation review cycles (comments, QA findings, rework) will be logged here.

## Questions — exact texts and response history

### Open

#### Q14 — Count-didn't-land monitor (WI5/AC4): is it needed at all?
- Context: AC4 asked for a monitor that alarms when no successful 3FED cycle count lands by the expected time. Descoped internally (user, 2026-10-28 ~15:30): "we only fix the issue here, no self heal, no alarm in scope." PR1's WARNING logs make silent days greppable, which is the interim coverage. The full monitor (success-marker + New Relic alert opening an OEH ticket, per the Q4/Q9 answers) is parked as a future implementation.
- Question: does the team want the full monitor built later, or are the WARNING logs enough?
- Where to ask: internal — the team ("any question is for us", user 2026-10-28).
- Response log: open.

#### Q15 — Disconnect self-recovery (WI4/AC3): is it needed at all?
- Context: AC3 asked for self-healing recovery (lookup-by-name, guarded purge + recreate, retry on disconnect). Out of scope (user, 2026-10-28 ~15:30: "No self heal in scope"). Interim behavior: a same-day replay after a partial commit fails loudly on the date-based name collision and opens a correctly-named ticket; a human cleans up by hand. The parked starting design lives in "Future implementation" above.
- Question: does the team want the self-healing recovery built later, or is the loud-collision + manual cleanup acceptable long-term?
- Where to ask: internal — the team ("any question is for us", user 2026-10-28).
- Response log: open.

#### Q16 — Orphan headers: functional per-header review (keep or purge each)
- Context: five 0-item orphan headers remain in prod from the failed runs (all five verified 0 items via `countItems` 2026-10-28 ~15:40; all five carry the daily "CC Schedule" schedule). User (2026-10-28 ~15:30): "Keep a note. We NEED to ask functional to review each one." User (2026-10-28 ~15:38): include hard evidence and post into "the OEH ticket that generates this conundrum."
- Question (as posted): the per-header review request with hard evidence — per header the id, name, creation timestamp with the originating run, `countItems` totalResults, subinventory count, and the schedule fields; plus today's landed non-AI count 300001040406623 (2,301 items, no AI twin) as the not-an-orphan contrast. Functional replies per header with keep or purge. A requested purge ships as its own follow-up (ESS InvCcPurgeCycleCountDetailsJob + validation), never in this ticket.
- Where to ask: an OEH ticket per user direction ("there are open tickets for my oncall week, in fact some of them reference this ticket", 2026-10-28 ~15:47). Ticket↔orphan mapping (verified live 2026-10-28 ~15:50): OEH-88827 (Triage, Luis) ↔ orphan 085 (10-24 09:31 run); OEH-88850 (Triage, Luis) ↔ orphan 952 (10-26 09:31 run); OEH-88909–88914 (Not Started, Michael Guanoluisa — current rotation, hands off) ↔ orphans 686+987 (10-26 14:03 backfill). Recommendation: post on OEH-88850 (the user's parked ticket, already the outage-family anchor citing OTCM-151550, its own run generated orphan 952).
- Response log: evidence-backed draft in `tmp/otcm151550_orphan_headers_comment.md`; pending user confirmation of OEH-88850 + approval to post.

### Answered

All presented in this chat on 2026-10-28; answers from the user the same day.

#### Q13 — Scope confirmations (AC4 + AC3): resolved INTERNALLY, comment never posted
- Context: AC4 asks for a monitor; AC3/WI4 asks for disconnect self-recovery. Both were directed out of this ticket's scope, and the original framing sought reporter sign-off via a Jira comment (draft: `tmp/otcm151550_scope_confirmations_comment.md`).
- Response log: 2026-10-28 ~15:30 — user: "Ok we made the ticket, so any question is for us." The comment to the reporter is dropped unposted. Verbatim decisions: Q1-equivalent (monitor) — "NO we only fix the issue here, no self heal, no alarm in scope. A success that returns without doing anything should be logged with WARNING level. Note in plan for future implementation and a question asking if needed." Q2-equivalent (self-heal) — "No self heal in scope. Note in plan for future implementation and a question asking if needed." Q3-equivalent (orphans) — "Keep a note. We NEED to ask functional to review each one." Outcomes: WARNING logs land in PR1; monitor and self-heal park as Q14/Q15; the orphan review goes to functional as Q16.

#### Q1 — Race fix: serialize vs shared-adapter concurrency bounding
- Question: fix the dual-create race by (c) serializing the two creates at integration level, or (d) bounding concurrency in the shared adapter's batch fan-out — what is the difference?
- Response log: 2026-10-28 — user asked "c vs d what is the diff"; clarified (c = the gather at `_inventory_snapshot.py:156`, integration-level serialize; d = the batch fan-out at `_oracle_create_cycle_count_definition_action.py:128`, shared-adapter bounding). Chose (c); (d) cut from scope.

#### Q2 — Same-day replay recovery semantics
- Question: on replay when the name already exists: (b) reuse the existing header and reload items, or (c) purge + recreate?
- Response log: 2026-10-28 — user asked the consequences of (c) vs (b); explained skip-if-landed treats the empty orphan 333 as landed, so the outage repeats. Chose (a) purge + recreate.

#### Q3 — Orphan headers cleanup
- Question: script/spike to delete the five empty orphan headers, or document-only?
- Response log: 2026-10-28 — user challenged "do we really need this? why?" → document-only (Jira comment). No deletion.

#### Q4 — Ticket-call timeout value
- Question: timeout for the Jira ticket call (30 s / 60 s / 90 s)?
- Response log: 2026-10-28 — (b), the repo-pattern default (~30 s via a new settings key).

#### Q5 — REST intake route
- Question: the REST `POST /fedex/cycle-count` route duplicates the SFTP route's work — keep or drop?
- Response log: 2026-10-28 — "so are there 2 routes? we shouldnt be dropping anything" → keep both routes.

#### Q6 — Shared session dict across invocations
- Question: `_sessions` is shared across invocations on a warm container — fix that defect in this ticket?
- Response log: 2026-10-28 — yes, fix the shared-adapter defect here (the `close_all_sessions` iteration fix in PR2).

#### Q7 — Proceed without the 10-25 400 body?
- Question: the exact 400 body from 10-25 was missing from CloudWatch — proceed on partial evidence?
- Response log: 2026-10-28 — "proceed". (The body was then recovered from New Relic anyway.)

#### Q8 — Isolation flag flip
- Question: turn `http-client-session-failure-isolation` ON in prod as part of the fix?
- Response log: 2026-10-28 — "leave the flag", then clarified: NO flag flip — it stays OFF in prod (ON in dev/stage/ott). Race fix carried by serialization + recovery; QA forces the flag OFF in local/QA runs for prod parity.

#### Q9 — Monitor alert channel
- Question: if a monitor is kept, alert via CloudWatch alarm/SNS or via the OEH ticket path?
- Response log: 2026-10-28 — OEH ticket, matching the repo pattern.

#### Q10 — Empty-file daily counts
- Question: the flow creates empty counts on days with no items — suppress that?
- Response log: 2026-10-28 — "does empty produce race conditions? FOCUS ONLY ON WHAT IS ASKED TO FIX: RACE CONDITIONS" → no; dropped from scope entirely.

#### Q11 — Monitor at all (WI5)
- Question: keep the WI5 monitor in this ticket's scope?
- Response log: 2026-10-28 — "monitor? why do we need a monitor?!?!?!?! DROP THAT FOCUS ON THE TICKET" → descope; external confirmation tracked as Q13.

#### Q12 — CloudWatch log access
- Question: proceed on New-Relic-only evidence?
- Response log: 2026-10-28 — "without CW? but you do have access to CW if you want to see logs?" → the full CW/NR/Oracle evidence haul above was performed the same day.

## Post-merge actions

- [ ] File the close-all in-flight safety follow-up ticket — after all PRs merge, before closing this plan. Confirmed 2026-10-29 by two independent investigators + adversarial review (user-directed pipeline): the flag-off failure recycle (`_http_client.py:106`) is a LIVE close-under-use hazard in prod (flag `false`) and on the custom-auth Lambda in every env (flag absent); remaining exposed fan-outs include IN-I-2019 preprocessing and the WMS-I-1010/1040 dual creates. Remedy: `http-client-session-failure-isolation` prod rollout analysis (soaked in dev/stage/ott since 2026-08-10) with a recycle-gap decision — NOT manager-side concurrency machinery. Draft ready at `tmp/otcm151550_close_all_followup_ticket.md` ("Analyze prod rollout of HTTP client session failure isolation"); file in OTCM and add this ticket's PR links at filing.
- [ ] File the per-create session follow-up ticket — after all PRs merge, before closing this plan. Pipeline complete 2026-10-29 (independent investigator CONFIRM-WITH-CHANGES; independent draft + refinement; adversarial review CHANGES-NEEDED → all 9 findings fixed). Draft at `tmp/otcm151550_per_create_session_followup_ticket.md` ("Restore parallel IN-I-2019 dual cycle-count create — per-create private sessions if the isolation flag stays off in prod"): two routes behind the flag ticket's go/no-go (GO: ~150-line domain-only restore; NO-GO: 3-PR session-scope build, ~790 lines). File in OTCM and add this ticket's PR links at filing.

Verbatim backup of the draft (2026-10-29, in case `tmp/` is lost):

```markdown
*Assumed project: OTCM — the Jira key is assigned at ticket creation.*
*Drafted 2026-10-29. To be filed after OTCM-151550's PRs merge — add their PR links to References then.*

# Title

Analyze prod rollout of HTTP client session failure isolation

# Context

OTCM-151550 fixed the IN-I-2019 cycle-count outage. One failed Oracle request closed every shared HTTP session while sibling requests were in flight on them. Both cycle-count definitions committed server-side while the client saw disconnects, and five empty orphan count headers stayed in prod. On 2026-10-28 the OTCM-151550 author decided the `http-client-session-failure-isolation` flag stays OFF in prod for that ticket's scope. This follow-up does not revisit that decision. It treats the prod flag as its own analyzed decision: soak evidence, a recycle-gap analysis, abort conditions, and an explicit go/no-go.

The mechanism is confirmed in code. Any request failure inside `HttpClient.request` (`_http_client.py:234`/`:236`, `:253-255`; auth-header-generation failures are deliberately excluded — no session was obtained, so there is nothing to recycle) runs `_handle_failed_request_sessions`. With the flag off it calls `close_all_sessions` (`_http_client.py:106`), which pops and closes every session in the shared registry with no lock and no in-flight count (`_session_management.py:113-127`). Sibling `asyncio.gather` children mid-request on those sessions are aborted; their failure handlers re-trigger the close, and one bad request cascades into a full integration failure. The Jira error-ticket POST rides the same registry (`_client_factory.py:92`), so a close can kill the ticket call too. OTCM-151550 attributed the 2026-10-25 ticket loss to the POST being abandoned at invocation shutdown — the invocation died 61 ms after the POST started, and the custom-auth Lambda's 3-second timeout makes the shutdown reading plausible. The flag removes close-under-use as a ticket-killer; it gives the ticket call no completion guarantee (that guarantee is PR2's mechanism, per PR #2848).

Blast radius: all Oracle REST adapters share one session (`oracle_erp`, `_client_factory.py:55`); BIP/SOAP readers share another (`oracle_soap_service`, `:77`). One close also kills the `atlassian`, `manhattan_*`, `easypost`, `helios`, `jpm`, `oracle_epm` and `opticom_*` sessions. 104 `asyncio.gather` fan-out call sites (91 files) run across the integrations and adapters (repo-wide count, tests excluded). The ones bound to these shared sessions include IN-I-2019 preprocessing (`_inventory_snapshot.py:343`, `_line_preprocessor.py:112`) and the WMS-I-1010/1040 concurrent dual creates. Exposure today: prod's main and events Lambdas (flag explicitly `false`, `_feature_flag_config/prod.yml:68-69`), and the custom-auth Lambda in every environment including prod (flag absent from all four `*_custom_auth.yml`; an absent flag reads as `false`). The stage/dev/ott main and events Lambdas run with the flag on, soaked since 2026-08-10.

OTCM-151550's PRs do not close this because they never touch the failure-recycle path. Pop-and-close removes the registry-iteration crash and makes mid-close registration deterministic; serialization removes the two racing cycle-count CREATEs. The preprocessing fan-outs stay concurrent, and the flag stays off where the outage happened.

Scope: isolation-flag analysis and rollout only. Manager-side concurrency machinery (leases, refcounts, per-run session scopes) is rejected: the flag already removes the only failure-triggered close-under-use trigger that fires while sibling work is in flight, at zero new code, versus new machinery in the repo's hottest shared layer.

The two investigations behind this ticket disagree or leave gaps in three places; the acceptance criteria account for all three.

1. REST teardown timing. One investigation verified against the pinned Mangum 0.17.0 source that the REST lifespan close (`_rest_api.py:13`) runs at the end of every REST invocation; the other described it as container teardown. The per-invocation reading has the source-level evidence.
2. Residual risk after the flip. One report says the close-under-use class effectively disappears; the other found a narrow leftover chain: a non-HTTP failure in a default-`gather` child leaves siblings mid-request, and the per-invocation teardown close (`_entry_points.py:265`, `_rest_api.py:13`) can still abort them.
3. Soak coverage. The dev/stage/ott soak never covered the custom-auth Lambda, which has no flag in any environment.

# Acceptance criteria

- [ ] Analysis artifact attached: a written analysis (on this ticket or a linked `.docs/` page) covering the close-under-use mechanism, the blast radius (shared session ids, fan-out sites, exposed Lambdas and environments), what a caller sees when a session closes under its request, and the residual close-under-use chain that survives the flip (leftover `gather` children aborted by the per-invocation teardown closes), its error signature, and why it is accepted. Pin the exact Oracle error text(s) from the 2026-10-25 incident and use them verbatim in the soak and watch queries.
- [ ] Soak evidence attached: New Relic and Jira analysis of dev/stage/ott since 2026-08-10 showing no poisoned-session persistence — no consecutive identical "HTTP Client Error" bursts per integration and no OEH tickets citing session invalidation. Query and results linked.
- [ ] Recycle-gap decision recorded: with the flag on, a failed request no longer recycles sessions, so a poisoned session keeps failing subsequent requests for the rest of the current invocation (and, when a session leaks past a close, across invocations until the next close). Either pair the flip with `DummyCookieJar` for `oracle_erp` and `oracle_soap_service` (validated against SOAP/MTOM and UCM flows, with tests) or document why that bounded persistence window is acceptable given the per-invocation and per-event closes.
- [ ] Custom-auth Lambda decision recorded: the flag is absent from all four `*_custom_auth.yml` files, so that Lambda runs the legacy close-all in every environment and has no soak. Either add the flag to the custom-auth configs in this rollout or document why it stays on the legacy behavior.
- [ ] Sequencing confirmed: OTCM-151550's serialization and pop-and-close ship first or in the same release, so the known in-invocation race is closed before the legacy close-all is retired.
- [ ] Go/no-go recorded on this ticket by the implementer with the team (as on OTCM-151550) before any flip tag, based on the criteria above. A no-go exit closes the ticket with the decision and rationale documented and no flip.
- [ ] Flip deployed: `_feature_flag_config/prod.yml` `http-client-session-failure-isolation: true` via the normal tag pipeline. Rollback is reverting the line and redeploying; the flag is static, read at container init.
- [ ] Contract note written: `.docs/architecture/` and the AGENTS.md cheat sheet state the new session-recycling contract — failures no longer recycle sessions; recycling happens per-event on the events Lambdas and per REST invocation; poisoning-recovery expectation per the recycle-gap decision.
- [ ] Post-rollout watch (2 weeks): OEH ticket rate for HTTP-client errors flat or down; zero "invalidated by another session" recurrences; no integration showing consecutive-run identical failures (the poisoned-persistence signature).
- [ ] Abort conditions honored: revert the flag line and redeploy on any watch breach — a rise in HTTP-client-error OEH tickets, any "invalidated by another session" recurrence, or consecutive-run identical failures in any integration.

# References

- OTCM-151550: https://warbyparker.atlassian.net/browse/OTCM-151550
- OTCM-151550 error-chain PR: [PR #2848](https://github.com/WarbyParker/monocle_integrations/pull/2848)
- Flag introduced under OTCM-135904 (2026-08-10): [PR #2353](https://github.com/WarbyParker/monocle_integrations/pull/2353)

Mechanism anchors:

- `monocle_integrations/_adapters/_http/_http_client.py:106` — flag-gated close-all, called from the failure arms at `:236` and `:253-255`
- `monocle_integrations/_adapters/_http/_session_management.py:113-127` — pop-and-close `close_all_sessions`; class-level registry at `:22`
- `monocle_integrations/_adapters/_http/_client_factory.py:55` — shared `oracle_erp` session; `:77` `oracle_soap_service`; `:92` Atlassian on the same registry
- `monocle_integrations/_entry_points.py:265` — per-event close
- `monocle_integrations/_api/_rest_api.py:13` — REST lifespan close (per invocation under Mangum 0.17.0)

Fan-out exposure examples:

- `monocle_integrations/_domain/_integrations/_wp_in_i_2019_fedex_inventory_snapshot/_inventory_snapshot.py:343`
- `monocle_integrations/_domain/_integrations/_wp_in_i_2019_fedex_inventory_snapshot/_steps/_line_preprocessor.py:112`
- `monocle_integrations/_domain/_integrations/_wp_wms_i_1010_wms_to_oracle_inventory_balances/_wms_inventory_balances.py:248`
- `monocle_integrations/_domain/_integrations/_wp_wms_i_1040_wms_to_oracle_wip_balances/_wp_wms_i_1040_wms_to_oracle_wip_balances.py:469`

Config keys:

- `monocle_integrations/_feature_flag_config/prod.yml:68-69` — `http-client-session-failure-isolation: false`
- `monocle_integrations/_feature_flag_config/stage.yml:70-71`, `dev.yml:70-71`, `ott.yml:70-71` — `true`
- Flag absent from `monocle_integrations/_feature_flag_config/{dev,stage,ott,prod}_custom_auth.yml`; an absent flag reads as `false` (`monocle_integrations/_adapters/_feature_toggles/_file_feature_flag_reader.py:52-57`)
- Custom-auth Lambda deployment: `infrastructure/us-east-1/main.tf:54-86` (`CUSTOM_AUTH = "true"` at `:71`)
```

## Process notes

- Implementation needs a fresh branch off `main` — the current checkout is on `OTCM-149147-ar-i-3018` with unrelated uncommitted changes.
- Per PR: fast checks → self-review skill → `tmp/pr_description.md` → user review → pr-review skill pre-opening → slow suites (full coverage gate + scoped API tests) → push → open → label → review-request message. Never commit/push without explicit approval.
- FSD v2.1 local copy is not Drive-synced (mtime 09-21) — add to the sync catalog (housekeeping, not part of these PRs).

## Closure

- 2026-11-03: TICKET CLOSED — QA moved OTCM-151550 to Done (Jira status Done, resolution Done). All three PRs merged (deployed to stage as `vstage432`); stage QA evidence posted (comment 977087, scenarios S1–S7 all Pass); the WI6 orphan review posted on OEH-88850 (comment 977051) and OEH-88827/OEH-88850 were Rejected the same morning the ticket closed. Residuals deferred at closure: the two post-merge follow-up tickets above (drafts ready, filing parked by user), the batch-budget follow-up (draft parked by user), and open questions Q14/Q15. Drafts moved 2026-11-04 to `notes/future-work/` (see that folder's README index). Plan archived verbatim at `notes/projects.IN-I-2019.OTCM-151550.plan.md`.