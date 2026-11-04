> Parked follow-up from OTCM-151550 (closed 2026-11-03; see `notes/projects.IN-I-2019.OTCM-151550.md`). Never filed; moved from `monocle_integrations/tmp/` on 2026-11-04. Entry condition: work starts only after the isolation-rollout draft records its go/no-go. Re-verify every claim against the current repo before filing.

*Assumed project: OTCM — the Jira key is assigned at ticket creation.*
*Drafted 2026-10-29. To be filed after OTCM-151550's PRs merge — add their PR links to References then. Entry condition: work starts only after the isolation-flag rollout follow-up ticket records its go/no-go decision.*

# Title

Restore parallel IN-I-2019 dual cycle-count create — per-create private sessions if the isolation flag stays off in prod

# Context

OTCM-151550's PR2 (`52fc0764b`) fixed the 2026-10-25 3FED cycle-count outage by serializing the IN-I-2019 AI/non-AI dual create through `create_counts_sequentially` (`_create_counts_sequentially.py:14-47`). That removed the outage vector at the cost of doubling create latency on the route — one create's duration per snapshot file, sum instead of max. PR2 named per-create private sessions the candidate long-term fix to restore parallelism safely, contingent on the isolation-flag decision, and deferred them to a follow-up: this ticket.

Full parallelism requires that no failure-triggered `close_all_sessions` can abort a sibling create's in-flight request. Today any request failure inside `HttpClient.request` runs `_handle_failed_request_sessions` (auth-header-generation failures excluded: no session was obtained, so there is nothing to recycle), and with the `http-client-session-failure-isolation` flag off it calls `close_all_sessions` (`_http_client.py:106`, called from `:236` and `:253-255`), which pops and closes every session in the shared registry (`_session_management.py:22`, `:113-128`). Two routes remove that hazard: the isolation-flag prod rollout (the sibling follow-up ticket) makes failure-triggered closes disappear entirely; per-create private sessions make the two creates registry-exempt so the legacy close cannot reach them.

An independent investigation (verdict CONFIRM-WITH-CHANGES) found the private-session mechanism feasible and architecturally sound — a ContextVar-scoped, registry-exempt session override hooked into the single session-resolution funnel `HttpSessionFactory.get_session` works with zero port/adapter signature changes and propagates correctly into `asyncio.gather` children — but gated its necessity on the flag ticket. If the flag rolls out (GO), the machinery is redundant and the parallelism restore collapses to a small domain-only change: flag ON means no failure-triggered close-all exists (`_http_client.py:102-105`), capture-and-raise means both creates complete before the helper returns so the per-invocation teardown closes (`_entry_points.py:265`, `_api/_rest_api.py:13`) have no detached children to abort, Lambda single-concurrency prevents cross-invocation sharing, and the repo spawns no fire-and-forget tasks. Only if the flag stays OFF in prod (NO-GO) are per-create sessions the sole safe parallel path. This ticket is therefore written as two routes behind an explicit entry condition.

## Route A — flag ticket exits GO (domain-only, ~150 lines)

Implement `create_counts_concurrently` in `_wp_common_create_cycle_count_integration` — `asyncio.gather` plus capture-and-raise with the exact error contract of `create_counts_sequentially` (`_create_counts_sequentially.py:14-47`: both counts always attempted, a failure captured so the other count still runs, AI error raised first, a dual failure logging the dropped non-AI error as a warning) — and switch the two call sites (REST `_inventory_snapshot.py:160`, SFTP `_steps/_cycle_count_creator.py:89`). No HTTP-layer changes. Default `gather` does NOT suffice: it raises on the first failure and leaves the sibling running detached, which the per-invocation teardown closes would abort — capture-and-raise is what closes that window.

## Route B — flag ticket exits NO-GO (per-create private sessions; three PRs, ~790 lines total)

With the legacy close-all live in prod, per-create sessions are the only safe parallel path: a failed request still runs `close_all_sessions` (`_http_client.py:106`), which pops only registered sessions — both creates' private sessions survive and the sibling's in-flight POST is not aborted. The mechanism, verified feasible by the investigation: a ContextVar holding per-session-id private sessions, checked at the head of `HttpSessionFactory.get_session` (`_session_management.py:171-213`) — the funnel every request of every client type passes through (`_http_client.py:189-193`). On a hit, refresh the auth header via the existing `_apply_authorization_header` (`:154-161`) and return the private session; on a miss (the default everywhere), fall through to the current registry path unchanged. Because one shared `RestClient` (`session_id="oracle_erp"`) is built once and injected into 34 adapter injection sites and the session is resolved per request rather than held by the client, the override needs no changes to any port, adapter, facade method, or domain signature — and an `oracle_erp` override never touches `atlassian` or the SOAP session, so the Jira error-ticket POST keeps its shared session. ContextVar propagation into `gather` children was verified empirically and has repo precedent (`_utils/_context.py:4-5`; `_wp_in_i_2017b_fedex_pick_ship_inbound/_steps/_payload_reference_context.py:1-20`).

PR split (repo target ≤ ~400 changed lines per PR including tests):

| PR | Contents | Est. lines | Depends on |
|---|---|---|---|
| 1. `Add per-scope private HTTP session mechanism` | `_session_management.py` ContextVar + async context manager + `get_session` head branch + one shared session builder extracted from `add_session` (`:103-110`); `HttpClient.private_session_scope()` delegate; exports. Inert — nothing calls it. Tests: scope creates an unregistered session, prefers private, refreshes the auth header, closes on success/exception/cancellation, `close_all_sessions` blind to it, no-scope path identical | ~330 (≈90 code + ≈240 tests) | entry condition |
| 2. `Wire Oracle session scope port into cycle-count integrations` | New small `_domain/_ports` ABC (the dependency rule forbids `_domain` importing `_adapters`); facade ctor param + `_entry_points` + `Adapters` wiring; optional `CreateCycleCount.__init__` kwarg (default `None` → today's behavior for the other three integrations) | ~180 | PR1 |
| 3. `Restore parallel IN-I-2019 dual create on private sessions` | `create_counts_concurrently` (gather + per-create scope + capture-and-raise) + the two call sites + tests (parallel proof, per-create isolation, AI-first error contract, scope-per-create assertions). Small and revertable — the only behavior change | ~280 | PR2 |

PR titles carry this ticket's Jira key, assigned at filing.

Design constraints, each carried into the acceptance criteria:

- The session scope must be entered INSIDE each create coroutine, never around the outer `gather` — a scope set around the whole gather binds one private session shared by both creates: still close-immune, but silently not per-create. Tests must assert two distinct sessions.
- Extract one session builder shared with `add_session` so private and registered construction cannot drift (210 s timeout at `:106`, `certifi_connector()` at `:108`, cookie-jar factory).
- Auth cost is ~zero: the OAuth token caches on the strategy instance, not the session (`_oracle_token_strategy.py:47-49`), and prod runs static Basic auth (`oracle-oauth2: false`, `prod.yml:88-89`); the only real cost is one TLS handshake per create.
- The create flow is pure REST on `oracle_erp` — definition POST, batch items POST, and the transactions import as a REST `erpintegrations` POST in both flavors; the only SOAP call in the flow is the rollback purge ESS submit (`_oracle_scheduled_job.py:32-72`).
- The async context manager owns open and close; `finally` covers exceptions and cancellation, and capture-and-raise leaves no detached children, so the per-invocation closes never see a private session. A misused scope would leak an unregistered session the per-invocation closes are blind to — prevented by construction (the CM is the only entry point) and covered by tests.

## Honest limits — neither route fixes

1. The disconnect-ambiguity orphan: if Oracle commits the definition POST but the client sees a failure, the flow raises with no purge — the purge rollback only runs on transaction-import failure (`_create_cycle_count.py:251-261`), and no cycle-count ID exists to purge after a lost definition response. The empty orphan header can recur. That needs WI4 lookup-before-create / purge-recreate, parked future work.
2. ESS/FBDI submit ambiguity: an `erpintegrations` POST lost after commit still submits the import job.
3. Whole-flow retry duplicates: a re-run creates fresh definitions; there is no dedup.
4. (Route B only) Flag-off close-under-use outside the create segment: private sessions protect only the create on `oracle_erp`. The preprocessing fan-outs stay on shared sessions — e.g. `_validate_and_complete_counts`' per-subinventory gather (`_inventory_snapshot.py:335-343`), which rides the SOAP session via the report client — and remain exposed while the flag is off in prod. The WMS-I-1010/1040 concurrent dual creates on shared `oracle_erp` (`_wms_inventory_balances.py:248`) also stay exposed; they are out of this ticket's scope. Route A removes this vector with the flip itself.
5. Oracle-side semantics of parallel creates: not addressed and not implicated — the outage was client-side (`_create_counts_sequentially.py:20`).

Jira-ticket POST delivery is likewise out of scope: its completion guarantee belongs to PR2's mechanism, not to sessions.

# Scope

1. Wait for the isolation-flag rollout ticket's recorded go/no-go (its acceptance criteria require that decision).
2. GO: implement `create_counts_concurrently` (gather + capture-and-raise, AI-first error contract identical to `create_counts_sequentially`) and switch the two call sites. No HTTP-layer changes.
3. NO-GO: additionally implement the ContextVar-scoped private-session mechanism (PRs 1–3 above) and ride it in the helper.

# Non-goals

- WI4 recovery (lookup-before-create / purge-recreate) — the disconnect-ambiguity orphan is parked future work.
- The isolation-flag rollout itself — the sibling ticket owns it; this ticket never changes the prod flag state.
- Manager-side concurrency machinery rejected by OTCM-151550 and the sibling ticket (leases, refcounts, permanent per-run session scopes) — the ContextVar scope ships only on the NO-GO route, where the flag decision leaves the legacy close-all live; the GO route ships no session machinery at all.
- ESS-submit ambiguity and whole-flow retry dedup.
- The SOAP report flows.
- The other three `CreateCycleCount` integrations (`_monocle_integrations.py:501`, `:787`, `:838`) — they keep today's behavior on the shared session.
- Recycling semantics of private sessions — a failed request's private session is not recycled mid-create; the scope discards it at create end.

# Acceptance criteria

- [ ] 1. Entry condition met: the isolation-flag rollout ticket's go/no-go decision is recorded and linked on this ticket, and the chosen route (A: domain-only restore / B: per-create private sessions) is stated here. No implementation PR opens before that link exists.
- [ ] 2. Parallel dual create restored on both IN-I-2019 routes (REST `_inventory_snapshot.py:160`, SFTP `_steps/_cycle_count_creator.py:89`) through one shared `create_counts_concurrently` helper, with the capture-and-raise error contract preserved: both creates always attempted, a failure captured so the other create still runs, the AI error raised first, and a dual failure logging the dropped non-AI error as a warning.
- [ ] 3. Failure-injection proof attached (test or documented dry-run evidence): a failed request in create A while create B is mid-POST leaves B's request completing — the close-under-use abort vector closed. Route A runs it with the flag ON (no failure-triggered close-all exists to abort B); Route B runs it with the flag OFF (B rides a registry-exempt private session the close cannot reach).
- [ ] 4. (Route B only) Session isolation: private sessions never appear in `HttpSessionManager._sessions`; a unit test proves `close_all_sessions` cannot close a private session mid-request; a test proves the two creates ride two distinct private sessions — the scope is entered inside each create coroutine, never around the outer gather.
- [ ] 5. (Route B only) No-scope paths byte-identical: the ContextVar branch sits at the head of `HttpSessionFactory.get_session` and falls through to the registry path unchanged when no scope is set; the existing `_adapters/_http` suites (`_session_management_unit_test.py`, `_http_client_unit_test.py`) pass unmodified; the private branch reuses `_apply_authorization_header` for auth parity; one shared session builder prevents construction drift.
- [ ] 6. (Route B only) No leaks: the scope's async context manager closes the private session on success, exception, and cancellation, with a test per path; the API/adapters test fixtures (`_api/_test/conftest.py:293`, `_adapters/_fixtures.py:79`) need no changes, and no test leaks a private session across cases.
- [ ] 7. Untouched neighbors: the other three `CreateCycleCount` integrations keep today's behavior unchanged (single create for IN-I-2022C, concurrent dual creates for WMS-I-1010/1040) through the optional kwarg default `None`; an `oracle_erp` scope never affects the `atlassian` or `oracle_soap_service` sessions.
- [ ] 8. Docs updated: AGENTS.md cheat sheet and `.docs/architecture/` state the session-scope contract on Route B (ContextVar scope, registry-exempt, entered per create coroutine), or the serialization note is restated as parallel-with-capture-and-raise on Route A.
- [ ] 9. Quality gates: 100% unit coverage on new code, mypy strict, line length 99; PR split per the route table (Route B: mechanism inert, then wiring, then a small revertable activation PR; Route A: one small PR).

# Abort conditions

- The flag ticket's decision changes before Route B's activation PR merges — re-scope to Route A. Route B's first two PRs are inert by design (nothing calls the mechanism), so stopping leaves no behavior change.
- The no-scope path cannot be kept byte-identical — any existing `_adapters/_http` suite needs modification to pass. Stop: do not ship a mechanism that alters default behavior in the repo's hottest shared layer (12 client types; 104 `asyncio.gather` sites across 91 files).
- A reachable path that skips the scope context manager's `finally` is found — a private session could leak unregistered (GC "Unclosed client session" warning and a dangling connection on a warm container, which the per-invocation closes never see). Stay serialized (the status quo) rather than ship a leaky scope.

# References

- OTCM-151550: https://warbyparker.atlassian.net/browse/OTCM-151550
- OTCM-151550 error-chain PR: [PR #2848](https://github.com/WarbyParker/monocle_integrations/pull/2848)
- OTCM-151550 session-race fix (PR2, the serialized state this ticket restores parallelism from): commit `52fc0764b`
- Sibling follow-up: the isolation-flag prod rollout ticket (`tmp/otcm151550_close_all_followup_ticket.md` — link its Jira key once filed); this ticket's entry condition is its recorded go/no-go
- Flag introduced under OTCM-135904 (2026-08-10): [PR #2353](https://github.com/WarbyParker/monocle_integrations/pull/2353)
- Independent investigation behind this ticket: per-create private HTTP sessions for the IN-I-2019 dual create, verdict CONFIRM-WITH-CHANGES (2026-10-29)

Mechanism anchors:

- `monocle_integrations/_adapters/_http/_http_client.py:106` — flag-gated close-all, called from the failure arms at `:236` and `:253-255`; the per-request `get_session` call at `:189-193`
- `monocle_integrations/_adapters/_http/_session_management.py:171-213` — `HttpSessionFactory.get_session`, the single session-resolution funnel the ContextVar branch hooks; registry at `:22`; pop-and-close `close_all_sessions` at `:113-128`; session construction in `add_session` at `:103-110`; `_apply_authorization_header` at `:154-161`
- `monocle_integrations/_domain/_integrations/_wp_common_create_cycle_count_integration/_create_counts_sequentially.py:14-47` — the capture-and-raise error contract to preserve; `:20` the "second create poisons both runs" note
- Call sites: `monocle_integrations/_domain/_integrations/_wp_in_i_2019_fedex_inventory_snapshot/_inventory_snapshot.py:160` (REST) and `.../_steps/_cycle_count_creator.py:89` (SFTP)
- `monocle_integrations/_domain/_integrations/_wp_common_create_cycle_count_integration/_create_cycle_count.py:251-261` — purge rollback runs only on transaction-import failure (the orphan limit)
- `monocle_integrations/_adapters/_http/_http_token/_generator_strategies/_oracle_token_strategy.py:47-49` — OAuth token caches on the strategy instance
- `monocle_integrations/_adapters/_oracle/_oracle_scheduled_job.py:32-72` — the flow's only SOAP call (rollback purge ESS submit)
- `monocle_integrations/_entry_points.py:265` — per-event close; `monocle_integrations/_api/_rest_api.py:13` — REST lifespan close (per invocation under Mangum 0.17.0)
- ContextVar precedent: `monocle_integrations/_utils/_context.py:4-5`; `monocle_integrations/_domain/_integrations/_wp_in_i_2017b_fedex_pick_ship_inbound/_steps/_payload_reference_context.py:1-20`

Config keys:

- `monocle_integrations/_feature_flag_config/prod.yml:68-69` — `http-client-session-failure-isolation: false` (prod, the Route B condition); `stage.yml:70-71`, `dev.yml:70-71`, `ott.yml:70-71` — `true`
- `monocle_integrations/_feature_flag_config/prod.yml:88-89` — `oracle-oauth2: false` (static Basic auth in prod, so re-auth cost per create is literally zero)
