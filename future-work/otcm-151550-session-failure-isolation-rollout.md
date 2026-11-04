> Parked follow-up from OTCM-151550 (closed 2026-11-03; see `notes/projects.IN-I-2019.OTCM-151550.md`). Never filed; moved from `monocle_integrations/tmp/` on 2026-11-04. Re-verify every claim against the current repo before filing.

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
