> Parked follow-up from OTCM-151550 (closed 2026-11-03; see `notes/projects.IN-I-2019.OTCM-151550.md`). Raised as a review finding on PR #2854 (agustin-freire-wp, 2026-10-30); user deferred creation 2026-11-02. Moved from `monocle_integrations/tmp/` on 2026-11-04. Re-verify every claim against the current repo before filing.

# Summary

Bound Jira error-ticket creation time in the S3 and SQS event handlers so a Jira outage cannot starve a DLQ batch

# Description

## Context

`monocle_integrations` runs as a single AWS Lambda that serves the REST API and the Kinesis, S3, and SQS event handlers. When event processing fails, the handlers open a Jira error ticket through the `wp_error_ticket_creation` integration. This ticket comes from a review finding on PR #2854 (agustin-freire-wp, 2026-10-30, "Not a blocker for this PR"). All file paths and line numbers below were verified on the repo.

## Problem

The S3 and SQS event handlers open one Jira ticket **per failed record**, one call after another:

- `monocle_integrations/_event_handlers/_handler.py`, `SQSEventHandler.__call__`: the `for event in records:` loop (line 498) creates a ticket per DLQ record in the `dead_letter_queue` branch (lines 531–589).
- Same file, `S3EventHandler.__call__`: the per-record error branch creates a ticket per failed S3 record (lines 330–398).

Each ticket call is capped individually: `asyncio.wait_for(..., timeout=self.settings.jira_ticket_creation_timeout_seconds)`, and `jira_ticket_creation_timeout_seconds` defaults to 30 seconds (`monocle_integrations/_adapters/_settings.py`, line 33).

Nothing caps the **total** time an invocation can spend on ticket calls:

- The four DLQ event-source mappings in `infrastructure/us-east-1/main.tf` set no `batch_size`, so they use the SQS event-source-mapping default of 10:
  - `lms_sync_dlq_sqs_event_handler` (lines 342–346)
  - `tracking_reference_sync_dlq_sqs_event_handler` (lines 366–371)
  - `oracle_invoices_flow_dlq_sqs_event_handler` (lines 389–393)
  - `delivery_events_dlq_sqs_event_handler` (lines 403–407)
- The events Lambda (`module.monocle_integrations_events_handler_lambda`, `main.tf` lines 88–93) runs with `lambda_timeout_seconds = 240` in stage, prod, and ott (`infrastructure/us-east-1/config/tfenv-stage.json`, `tfenv-prod.json`, `tfenv-ott.json`).

Worst case: 10 records x 30 seconds = 300 seconds > 240 seconds. During a Jira outage, a full DLQ batch burns the whole invocation hanging on ticket calls, and Lambda kills the function mid-batch. The real case is worse than the worst case: two DLQ branches do per-record work **after** the ticket call — `tracking_reference_sync` runs `fail_tracking_reference` and `oracle_invoices_flow` runs `_move_invoice_file_to_error` (`_handler.py` lines 588–594) — so the ticket calls also starve the follow-up processing.

The Kinesis handler and the API exception decorator are not affected. They open one summarized ticket per invocation (`monocle_integrations/_data_streams/_handler.py` lines 112–114; `monocle_integrations/_api/_handlers/_exception_handlers/_base_exception_handlers.py` around line 244).

## Impact

- **SQS (no data loss, but stalled draining and duplicate tickets).** The four DLQ mappings do not set `function_response_types = ["ReportBatchItemFailures"]` (the non-DLQ mappings in the same file do). A timeout-killed invocation therefore re-queues the **whole** batch. The batch loops: every retry burns up to 240 seconds hanging on Jira, no message leaves the queue, and DLQ draining stalls until Jira recovers. When Jira recovers, records ticketed before the kill are processed again and open duplicate tickets.
- **S3 (verify-before-claiming note).** The handler catches per-record errors and returns normally, so an ordinary per-record failure does not retry the S3 event — the ticket is the remediation path. The failure mode here is the timeout kill itself: S3 invokes Lambda asynchronously, the repo sets no `aws_lambda_function_event_invoke_config`, so AWS retries a failed async invocation (default: up to 2 retries). A Jira outage can therefore cause the whole S3 event to be re-delivered, re-running integrations for records that already succeeded and opening duplicate tickets once Jira is back. Unlike SQS, we do not control how many records an S3 event carries.
- **Operational noise.** A Jira outage plus a backed-up DLQ can produce a burst of duplicate OEH tickets after recovery, on top of the outage itself.

## Options analysis

### (a) Batch-level ticket-time budget in the S3/SQS handlers

Track elapsed invocation time in the per-record loop. Before each ticket call, check that the remaining budget can fit one more bounded call (30 seconds) plus headroom for the rest of the loop. When the budget is exhausted, stop opening per-record tickets for the rest of the batch.

- Fixes the root cause for both S3 and SQS, regardless of batch size or per-record work.
- Precedent in the codebase: PR #2851's cycle-count create path skips the non-AI count when the AI create exhausts its request time budget (`monocle_integrations/_domain/_integrations/_wp_common_create_cycle_count_integration/_create_counts_sequentially.py`, lines 44–50).
- Open design questions (for grooming):
  - What happens to records whose tickets are skipped: error-level log only, or one aggregate ticket per invocation summarizing the skipped records (the Kinesis handler already builds a per-invocation summary)?
  - Where the budget comes from: the Lambda context's remaining time (needs plumbing into the handlers) or wall-clock elapsed since invocation start.
  - How much headroom to reserve for post-ticket per-record work (`fail_tracking_reference`, `_move_invoice_file_to_error`) and for returning the batch response.
  - Whether the budget should also lower `jira_ticket_creation_timeout_seconds` adaptively, or stay a simple stop flag.

### (b) Cap `batch_size` on the four DLQ event-source mappings (Terraform only)

Set an explicit `batch_size` on the four DLQ mappings. For example, `batch_size = 5` bounds ticket time at 5 x 30 = 150 seconds, leaving 90 seconds of headroom inside the 240-second timeout.

- One-line change per mapping, no application code, ships immediately.
- Does not cover S3 payloads, whose record count we do not control.
- Does not protect against future growth in per-record work; the cap is only as safe as the arithmetic of the day it was chosen.

### Recommendation

Do **(b) now as immediate hardening, then (a) as the robust fix**. (b) removes the SQS worst case with a Terraform-only change and near-zero regression risk, so it should not wait for design work. (a) fixes the actual defect — unbounded aggregate ticket time — and keeps holding if batch sizes, the ticket timeout, or per-record work change later. Shipping (b) first also de-risks (a): the handler change can take the time it needs to answer the open questions above instead of rushing.

## Acceptance criteria

1. Terraform sets an explicit `batch_size` of 5 (or the value chosen in grooming) on all four DLQ event-source mappings: `lms_sync_dlq_sqs_event_handler`, `tracking_reference_sync_dlq_sqs_event_handler`, `oracle_invoices_flow_dlq_sqs_event_handler`, `delivery_events_dlq_sqs_event_handler`.
2. The chosen `batch_size` satisfies: `batch_size` x `jira_ticket_creation_timeout_seconds` (30s) + documented headroom < `lambda_timeout_seconds` (240s). The arithmetic is stated in the PR description.
3. `SQSEventHandler` and `S3EventHandler` stop opening per-record tickets once the remaining invocation budget cannot fit one more bounded ticket call plus headroom. A unit test with a hanging `wp_error_ticket_creation` and a full batch of 10 records proves the handler finishes the batch inside the budget (the existing `jira_ticket_creation_timeout_seconds=0.01` hang pattern in `_event_handlers/_handler_unit_test.py` is the model).
4. Every record whose ticket is skipped is logged at error level with its queue ARN or S3 file key, and the grooming-decided fallback (log-only or one aggregate ticket per invocation) is implemented and unit-tested.
5. The Kinesis handler and the API exception decorator still open exactly one ticket per invocation/request; their existing tests pass unchanged.
6. Unit-test coverage stays at 100% per the repo gate (`make check-coverage`).

## References

- Finding: PR #2854 review thread — https://github.com/WarbyParker/monocle_integrations/pull/2854#discussion_r4424763074
- SQS per-record ticket branch: `monocle_integrations/_event_handlers/_handler.py` lines 498, 531–589
- S3 per-record ticket branch: `monocle_integrations/_event_handlers/_handler.py` lines 330–398
- Ticket timeout setting: `monocle_integrations/_adapters/_settings.py` line 33 (`jira_ticket_creation_timeout_seconds: int = 30`)
- DLQ event-source mappings: `infrastructure/us-east-1/main.tf` lines 342–346, 366–371, 389–393, 403–407 (no `batch_size`, no `function_response_types`; SQS default batch size is 10)
- Events Lambda timeout: `infrastructure/us-east-1/main.tf` lines 88–93; `infrastructure/us-east-1/config/tfenv-{stage,prod,ott}.json` (`lambda_timeout_seconds: 240`)
- Kinesis single-ticket behavior: `monocle_integrations/_data_streams/_handler.py` lines 112–114
- Time-budget precedent (PR #2851): `monocle_integrations/_domain/_integrations/_wp_common_create_cycle_count_integration/_create_counts_sequentially.py` lines 44–50

## Out of scope

- Changing the Kinesis or API ticket behavior (already one ticket per invocation).
- Enabling `ReportBatchItemFailures` / partial-batch responses on the DLQ mappings. Related, but a separate decision: it changes retry semantics for the DLQ consumers and does not bound ticket time by itself.
- Changing the 240-second Lambda timeout or the 30-second per-ticket timeout default (raised only as grooming questions for option (a)).
- Jira outage detection or alerting; this ticket only bounds what a Jira outage costs an invocation.
