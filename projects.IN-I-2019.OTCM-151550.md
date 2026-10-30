# OTCM-151550 — IN-I-2019: Fix cycle count outage (3FED)
- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-151550
- **RICE**: IN-I-2019
- **Repos**: monocle_integrations
- **Status**: PR1 and PR2 merged; PR3 #2854 open, CI running (as of 2026-10-30)
- **Plan**: [in-i-2019_outage_fix plan](https://github.com/WarbyParker/monocle_integrations) (local: `monocle_integrations/.cursor/plans/in-i-2019_outage_fix_a56f355a.plan.md`)

## Background — the integration and the outage

**The business process.** Warby Parker stores frames in a FedEx warehouse (facility code 3FED). Every day, FedEx sends files listing what they believe is on the shelves. To check reality against the books, Oracle creates a cycle count: a task that says "go count these items in this corner of the warehouse." Each cycle count has a header (the envelope: name, date, which part of the warehouse) and items (the contents: which products to count).

**What IN-I-2019 does.** It automates the daily cycle count. Every day it reads the FedEx files and creates two cycle counts in Oracle: one for the AI subinventory and one for the non-AI subinventory (two logical areas of the warehouse). Then it loads the items into each. It has two intake routes: a REST route and an SFTP-to-S3 file route.

**What broke (2026-10-23 to 10-25).** Runs failed three days in a row. No 3FED cycle count landed in Oracle since 10-24. The investigation found three bugs:
1. A race condition. The integration fires both creates at the same time. A shared cleanup routine (`close_all_sessions`) can kill the other request's network connection mid-flight, and can itself crash with `RuntimeError: dictionary changed size during iteration`.
2. A broken error-ticket path. When a run fails, the code should auto-open a Jira ticket (an OEH ticket — the team's alarm). A typing bug made the ticket call crash, so the alarm never rang. The one Jira POST that did go out was abandoned mid-flight when the invocation shut down.
3. Useless ticket names. Tickets from the file-watcher route were all named `s3_event_handler` with no request id. Nobody could tell which integration failed or trace the run.

**What this ticket fixes.** Those three bugs, in three PRs (error-chain hardening, dual-create serialization, event-route ticket identity). The ticket's acceptance criteria also asked for three extras: self-healing recovery (AC3), a count-didn't-land monitor (AC4), and orphan-header cleanup (AC5). The extras are where the scope questions lived; their outcomes are under Decisions.

## Outcome
- In flight. Plan approved 2026-10-28 after two adversarial review rounds. PR1 (error-chain survival) and PR2 (dual-create serialization) merged 2026-10-29. PR3 opened as #2854 on 2026-10-30 with ticket identity and the bounded ticket-call helper (docs excluded). The ticket-creation retry and DLQ redelivery hardening was descoped before opening and parked as a follow-up candidate. The close-all in-flight safety question was confirmed a live prod hazard and parked as a follow-up ticket, to be filed after the PRs merge.

## What shipped
- PR1: [monocle#2848](https://github.com/WarbyParker/monocle_integrations/pull/2848) (merged 2026-10-29) — error text preserved (`message=str(error)`), Jira ticket call bounded (`asyncio.wait_for`, 30 s default), silent-success WARNING logs, FedEx 422 description contract preserved.
- PR2: [monocle#2851](https://github.com/WarbyParker/monocle_integrations/pull/2851) (merged 2026-10-29) — dual create serialized via the shared `create_counts_sequentially` helper; `close_all_sessions` is deterministic pop-and-close. Review round: the timeout skip keys on a request-budget marker (`HttpClientTimeoutError` at `_raise_client_error`), and dual failures raise one `ExceptionGroup`.
- PR3: [monocle#2854](https://github.com/WarbyParker/monocle_integrations/pull/2854) (opened 2026-10-30) — event-route error tickets carry RICE id + file path (S3 configuration-id fallback, SQS DLQ queue-RICE-id fallback, non-dict body normalization); one shared bounded ticket-call helper across the three event routes; Kinesis traceback string fix.

## Decisions
### Functional clarifications (Q&A)
1. Monitor (AC4) in this ticket? → NO — "we only fix the issue here, no self heal, no alarm in scope" (user, Cursor chat, 2026-10-28). Silent-success paths log at WARNING instead (PR1). Full monitor parked; open question whether it is needed (plan Q14).
2. Self-healing recovery (AC3) in this ticket? → NO — out of scope (user, Cursor chat, 2026-10-28). Interim: same-day replay fails loudly with a correctly-named ticket; manual cleanup. Parked design in plan; open question whether it is needed (plan Q15).
3. Orphan headers (AC5)? → keep and note; functional reviews EACH of the 5 headers and decides keep-or-purge per header (user, Cursor chat, 2026-10-28). Review request posts as a Jira comment; any purge is its own follow-up.
4. Scope questions are internal, not routed to the reporter — "we made the ticket, so any question is for us" (user, Cursor chat, 2026-10-28). The drafted Q13 comment to Emilio was never posted.
5. Race fix approach → serialize the dual create at integration level (user, Cursor chat, 2026-10-28). No isolation-flag flip in prod.

### Design decisions (ours)
1. `close_all_sessions` becomes pop-and-close by identity. The current code iterates the live `_sessions` view (the proven `dictionary changed size` RuntimeError) and then `clear()`s, which leaks sessions added mid-close.
2. The ticket call gets `asyncio.wait_for` (~30 s) plus step logs. Hang-hardening only: the 10-25 kill completed in ~33 ms, so no timeout could have fired; the logs make any recurrence visible.
3. Event-route tickets gain `origin_rice_id` and `file_path`, and the function-name fallback gains `or rice_id`. Fleet-wide effect: ~25 S3-bound integrations' tickets stop being named `s3_event_handler`.
4. Serialization carries the ticket-call completion mechanism: no concurrent close-all during the Jira POST, because the `atlassian` session lives in the shared registry.
5. Error description uses `str(getattr(exc, "message", exc))`, not `exc.args[0]`. Where the two differ, args[0] is always worse: aiohttp `RequestInfo` (crash + header leak), `OSError` errno int, empty-args IndexError. Verified by three independent analyses (orchestrator + two blind investigators, 2026-10-29).
6. `RequestValidationError` keeps the errors array the 422 always shipped (Option A; user, Cursor chat, 2026-10-29). `str(exc)` leaked raise-site file paths into the partner response. Encoding is `json.dumps(default=str)`, not `jsonable_encoder`: the light review panel proved the encoder itself raises on some ctx values (2026-10-29).
7. The session manager stays dumb: deterministic pop-and-close, with callers holding the no-concurrent-registration invariant. Manager-side machinery (leases, refcounts, per-run scopes) rejected 2026-10-29 after two independent investigations plus adversarial review. The prod isolation-flag rollout becomes its own analyzed go/no-go follow-up ticket (confirmed live hazard: flag-off recycle in prod; custom-auth Lambda unprotected in every env).
8. The dual-create serialization lives in ONE shared helper (`create_counts_sequentially` in `_wp_common_create_cycle_count_integration`), not two hand-copied blocks (light review panel, 2026-10-29). Race semantics must agree on both routes; the helper makes agreement structural.
9. The timeout skip keys on a request-budget marker, not a bare `TimeoutError` chain-walk. `_raise_client_error` raises `HttpClientTimeoutError` only when the direct cause is a timeout, so a wrapped 10s token-fetch timeout cannot trigger the skip (light review panel finding; user approved the mechanism, Cursor chat, 2026-10-29).
10. A dual create failure raises one `ExceptionGroup` carrying both errors, so the Jira ticket renders both tracebacks via `traceback.format_exception` (user chose ExceptionGroup over `add_note`, Cursor chat, 2026-10-29).
11. Ticket-creation retry (3 attempts, jittered backoff) and DLQ redelivery via `batchItemFailures` (with the Terraform ESM flag and `batch_size = 1`) were implemented and panel-reviewed, then dropped from PR3 (user, Cursor chat, 2026-10-29). Parked as a follow-up candidate (`tmp/pr3_review/triage_plan_delta.yaml`). Consequence: a DLQ message whose ticket call fails is still consumed silently, and one Jira blip loses a ticket.

## Evidence
- Full verified chain in the plan (CloudWatch prod logs, New Relic 3902898, read-only Oracle prod GETs, 2026-10-28): the 10-25 REST run's AI items got a 400 on a committed parent; the disconnects hit the non-AI batches after the legacy close-all; the Jira POST was abandoned mid-flight; the finally path crashed JSON serialization.
- Orphan headers (read-only prod GETs, 2026-10-28 ~15:40): all five verified 0 items via `countItems`. All five carry AutomaticallySchedule = Yes / Daily / "CC Schedule" — not just the 10-25 one as first believed. 085 "FEDEX Snapshot 2026-10-24" (10-24 09:31 UTC), 333 "FEDEX Snapshot 2026-10-25" (10-25 09:32), 952 "FEDEX Snapshot 2026-10-26" (10-26 09:31), 686 "3FED Snapshot 2026-10-26" (10-26 14:03, the OEH-88909 backfill run), 987 "3FED AI Snapshot 2026-10-26" (same run).
- Today's run (2026-10-28 08:12 UTC): landed the non-AI count "3FED Snapshot 2026-10-28" (header 300001040406623) with 2,301 items, then failed on a serial-quantity data error (OEH-89097 — a different defect class from the race). The AI twin was never created. A same-day reprocess will collide with that header by name.
- Integration failures are live while the fix is unshipped: OEH-89097 opened 2026-10-28 04:13.

## Test data
- TBD per the plan's QA matrix: a crafted FedEx file on the stage S3 prefix (lines passing the subinventory/lock-code filters with bogus UPCs) forces the no-match ValueError; empty and incomplete file sets exercise the new WARNING logs.

## Open items
- PR3 #2854 (ticket identity + bounded ticket-call helper) — open, CI running. The one local `make test-api` failure (`test__two_items_processed_concurrently_create_exactly_one_tracker`) is pre-existing: it fails identically on the merge-base.
- The Samsung AP-I-1071 event-test failure from the full `make test-api` run was concurrent-suite interference, not PR3 code: the test passes alone and the full `_event_handlers` suite passes 53/53 on the branch.
- Close-all follow-up ticket — draft ready at `tmp/otcm151550_close_all_followup_ticket.md` (verbatim backup in the plan's post-merge action); file in OTCM after the PRs merge, adding the PR links.
- WI6 orphan review-request comment (Q16) — evidence-backed draft ready; recommendation is OEH-88850 (the user's parked on-call ticket whose run generated orphan 952; OEH-88909–88914 belong to the current rotation, hands off); pending approval to post.
- Q14 (monitor needed?) and Q15 (self-heal needed?) — open, internal, parked.

## Artifacts
- Plan: `monocle_integrations/.cursor/plans/in-i-2019_outage_fix_a56f355a.plan.md`
- Related notes: [projects.IN-I-2019L.OTCM-139198](projects.IN-I-2019L.OTCM-139198.md) (legacy route retirement)
