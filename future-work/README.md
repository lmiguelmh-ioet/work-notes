# Future work — parked ticket drafts

Draft Jira tickets parked as proposals. None of these is filed. When bandwidth
opens: pick one, re-verify its claims against the current repo (each draft was
written against the checkout of its drafting date, and code drifts), file it
in Jira, and delete the draft here — the Jira ticket and a `projects.*.md`
file become the record from then on.

| Draft | Source | Drafted | Notes |
|---|---|---|---|
| [Session failure isolation rollout](otcm-151550-session-failure-isolation-rollout.md) | OTCM-151550 | 2026-10-29 | Analysis + soak + go/no-go for flipping `http-client-session-failure-isolation` on in prod. Its decision unblocks the per-create draft below. |
| [Per-create private sessions](otcm-151550-per-create-private-sessions.md) | OTCM-151550 | 2026-10-29 | Restore the parallel IN-I-2019 dual create. Entry condition: starts only after the isolation rollout records its go/no-go. |
| [Batch ticket-time budget](otcm-151550-batch-ticket-time-budget.md) | OTCM-151550 (PR #2854 review finding) | 2026-11-02 | Cap total Jira ticket-call time per event batch so a Jira outage cannot starve a DLQ batch. Independent of the two above. |
| [Per-order import completeness](otcm-153073-per-order-import-completeness.md) | OTCM-153073 stage verification | 2026-11-04 | RMCS-I-3001: fail import verification when an imported order has no contract status rows. OTCM-153073 shipped the status mapping only; the whole-load zero-row guard was cut and folds in here as decision D1. |
| [Identify submission alerting](otcm-153073-identify-submission-alerting.md) | OTCM-153073 stage verification | 2026-11-04 | RMCS: alert when verified loads are not identified as contracts. Catches the 2026-11-04 failure mode (callback crashed, Identify never submitted). |
