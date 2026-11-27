# OTCM-158442 — OIC MCP server in monocle-mcp

- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-158442
- **RICE**: — (no RICE; OIC track of the MCP epic OTCM-158710)
- **Repos**: monocle-mcp
- **Status** (as of 2026-11-27): In flight — #21, #22 and #31 merged; #27 open off-stack; stack #39 open seven deep: #24 → #35 → #37 → #38 → #40 → #41 → #42. Plan rows 1–9 shipped; row 10 (activity-stream tool) waits on the live S2 probe
- **Plan**: [tickets/OTCM-158442/plan.md](../tickets/OTCM-158442/plan.md)

## Outcome

- In flight. Read-only OIC tools on the inherited FastMCP mount, Okta (IDCS)
  authorization-code + PKCE login, memory-only AES-GCM sessions.

## What shipped

- PR [#21](https://github.com/WarbyParker/monocle-mcp/pull/21) — Oracle config + IDCS client — MERGED.
- PR [#22](https://github.com/WarbyParker/monocle-mcp/pull/22) — encrypted memory-only session store — MERGED (squash `15b10bc`; 20-finding review, 7 fixes as one hardening commit; conflicts with main's #9 CI/coverage wave resolved as `22072a3`).
- PR [#24](https://github.com/WarbyParker/monocle-mcp/pull/24) — Okta login/callback routes — OPEN (5 light review rounds, comment cleanup, two main merges, coverage pin for `_verified_user`; includes the OAuth query scrub; 459 unit tests + 1 xfailed, 100% coverage green; a same-day scrub/SDK descope, `7cfc8de`, was reverted by `16cfb98` after the SDK proved to predate the PR, introduced in #7).
- PR [#27](https://github.com/WarbyParker/monocle-mcp/pull/27) — dev-only entry point for local runs — OPEN. Shape changed from the plan's config-gated `dev_user` (option A, parked as stash + patch) to a `.dockerignore`-excluded `dev_server.py` per user direction. Three light review rounds (15 panel seats + 6 triage verdicts): 14 findings implemented, 7 skipped as the documented indirection/residual class. Hardening commit `11d950b` pushed 2026-11-23; 402 unit tests + 1 xfailed, 100% coverage green.
- PR [#31](https://github.com/WarbyParker/monocle-mcp/pull/31) — OIC client routes + error taxonomy — MERGED (origin/main `029efe4`). 7-seat panel, 16 triage findings resolved (5 implemented, 3 cosmetic accepted, rest follow-ups recorded in plan.md). Per user direction (option C), `parse_retry_after` deduped out of both `_errors.py` twins into shared `common/src/clients/_retry_after.py`, including the monocle naive-`now` guard (unreachable at runtime). 3-seat delta review SHIP ×3, zero findings. Commit `df0a4d5`; 467 unit tests + 1 xfailed, 100% coverage green.
- PR [#35](https://github.com/WarbyParker/monocle-mcp/pull/35) — origin-locked OIC bearer auth + retry policy (PR 6a) — OPEN. `OicBearerAuth` (origin check before any session lookup or decryption; decrypts at send time; `OicNoSessionError` translation) + jittered `Retry-After` floor. Two light review rounds (10- then 12-finding triage); user-directed closing commit dropped the explanatory comments.
- PR [#37](https://github.com/WarbyParker/monocle-mcp/pull/37) — origin-locked OIC client (PR 6b) — OPEN. `OicClient` on httpx2 (GET retries with backoff, `Authorization` popped in `finally`), 41 client tests incl. the deliberate 429-retry divergence and the dev.yml pod-URL pin. One light review round, one nit resolved 1C SKIP.
- PR [#38](https://github.com/WarbyParker/monocle-mcp/pull/38) — tool client injection (PR 7) — OPEN. `Clients` bag in `tools/ports.py` (framework carries no system names per user direction): `ToolContext.clients`, per-spec `errors` hook, `make_application(oic=, sessions=)` hooks. 5-seat panel + 11-cluster triage + 2-seat delta review; the `_errors_refusals` validation removed on final user review as enforcement overhead.
- PR [#40](https://github.com/WarbyParker/monocle-mcp/pull/40) — OIC auth and inventory tools (PR 8) — OPEN. `oic_auth_status` (session read only), `oic_list_integrations`, `oic_get_integration` + `Sessions` Protocol and `Clients.oic_host`. Panel triage applied 10 findings; commit `12e3e83`, +870/−16 over 12 files.
- PR [#41](https://github.com/WarbyParker/monocle-mcp/pull/41) — monitoring and error tools (PR 9) — OPEN, tip `22a9674` force-pushed 2026-11-27. `oic_list_monitoring_instances`, `oic_get_monitoring_instance`, `oic_list_errors`, `oic_get_error` + shared `_oic_monitoring.py` wire models (camelCase-only since the live probe). 2-seat panel pre-commit (record `monocle-mcp/tmp/pr9_review/triage_plan.yaml`), then three light-review rounds over the amended diff (records `monocle-mcp/tmp/pr41_42_push_review/triage_plan{,_r2,_r3}.yaml`): totals prefer `totalRecordsCount` over the page-capped `totalResults`, 10000-cap hedges, nullable error status from the live errors shape, kebab aliases dropped per independent verification. 797 tests, 100% coverage.
- PR [#42](https://github.com/WarbyParker/monocle-mcp/pull/42) — registered callback port + signed-in page polish — OPEN, tip `975f4ee` force-pushed 2026-11-27 (7 commits rebased onto #41's `22a9674`). Signed-in page renders from a Jinja2 template with token details and fixed multi-value rows; `WP_ORACLE_REDIRECT_URI` override; OIC requests routed through a configured instance; dev config points at oictest2's design-time endpoint; auth status shows the OIC instance.

## Decisions

### Functional clarifications (Q&A)

1. No FSD; the OTCM-151549 spike is the design input (user, chat, 2026-11-18).
2. Read-only tools only; first phase is the 7 monitoring reads + `oic_auth_status` (user, chat, 2026-11-18).
3. Memory-only encrypted session; no durable store, no refresh token (user, chat, 2026-11-18).
4. Hosted; the callback is a new URL on the existing FastAPI app (user, chat, 2026-11-18).
5. Reuse the spike's public PKCE client `WP-OTCM-151549-SPIKE-CLI` on the dev1 stripe (user, chat, 2026-11-18).

### Design decisions (ours)

1. 9-PR split: PRs 1, 2, 4, 5 independent; PR 3 the behavior change; PRs 7–9 stacked on the OTCM-158702 stack.
2. Callback behind Access with an email match (not a public path); email normalized once at bind; email as GCM AAD.
3. `redirect_slashes=False` on the main router. The `/oauth/*` query scrub (spans + uvicorn access logs) stays in PR 3 (user, chat, 2026-11-20): a same-day descope (`7cfc8de`) assumed `opentelemetry-sdk` was PR-introduced, but the SDK predates the PR (added with the Access middleware in #7), so `16cfb98` restored the scrub.
4. `IdcsClient` constructor https refusal + `oic_base_url` https pin deferred from #21's review — lands in PR 3 (PR 9 fallback).
5. PR 4 shape: a dev-only entry point excluded from the deployed image over a shipped config-gated `dev_user` (user, chat, 2026-11-20) — no dev-user handling ships at all; option A parked (stash + patch at `tickets/OTCM-158442/parked-dev-user-config-gate.patch`).
6. Dev identity hardcoded as `dev@localhost`, not config: a config field would reintroduce dev-user surface into the shipped config model (user, chat, 2026-11-20).
7. The verifier-injection pin is an AST call check; `functools.partial` and the wider indirection class (wrapper chains, rebinding, getattr) stay documented review-owned residuals instead of growing the pin per spelling (review rounds 2–3, 2026-11-23).
8. Shared client code lives as flat modules under `common/src/clients/`, matching repo precedent (`auth/cloudflare_access.py`, `monocle/_retry.py`), not as a new package: `parse_retry_after` moved to `_retry_after.py` in PR 5 (user, chat, 2026-11-24 — "option C"). The remaining twin extraction (composable `RouteTemplate` + monocle guards + route-test backfill) is the post-PR-6 PR.
9. The tool-injection vehicle is a `Clients` bag in `tools/ports.py` — the framework carries no system names; a new system client is a new bag field and the registry/server signatures do not move (user, chat, 2026-11-25).
10. The single physical stack model: one chain #24 → #35 → #37 → #38 → #40 → #41 (GitHub stack #39), not absorb-the-conflict; each lower squash-merge is followed by merging `origin/main` into the branch above (user, chat, 2026-11-25).
11. `oic_get_instance_activity_stream` deferred to plan row 10: the docs deprecate `activityStream` and give `activityStreamDetails` no schema, so the payload shape must be observed on the live S2 probe before the model is written (user, chat, 2026-11-26 — "option A"). The same probe narrows the `_oic_monitoring.py` kebab/camel `AliasChoices`, the errors envelope's `total-records-count`, the name-filter semantics and `expand=connection`.
12. The live probe narrowed the wire casing: OIC monitoring/errors answers are camelCase-only (integrations, monitoring and errors captures), so the kebab `AliasChoices` were dropped from `_oic_monitoring.py` despite the kebab docs; an independent reviewer re-derived the same call from the captures and the public docs (user, chat, 2026-11-27).

## Evidence

- Live probe 2026-11-27 (oictest2, stage OAuth client on the a7fa stripe): all six OIC tools, 19 calls green; captures at `/tmp/oic_live_test/` (integrations, monitoring, errors — all camelCase). Details in `tickets/OTCM-158442/monday_oic_registration_prep.md`. QA scenarios S1–S13 run post-implementation; S7's evidence is PR 3's ADA/BOB full-flow unit tests.

## Test data

- `AccessIssuer` ADA/BOB fake identities (`common/src/auth/fake_access.py`); mock IDCS transport.

## Open items

- Q7 — spike client needs the OIC scope + this app's redirect URIs; ask drafted at `tickets/OTCM-158442/tony_message_idcs.md`, awaiting Tony's reply. Blocks the dev manual run and stage, not PRs.
- Q8 — stage Access app + hostname (OTCM-158707 track); also owns the replica-affinity pin.
- **Local E2E with real Okta tokens** (user, 2026-11-26): run the full stack locally against the real Access app + real IDCS — needs a local config carrying the real stage Access AUD and the IDCS client, and a real sign-in through `/oauth/login`. Being scoped now.
- PR 3 ([#24](https://github.com/WarbyParker/monocle-mcp/pull/24)), PR 4 ([#27](https://github.com/WarbyParker/monocle-mcp/pull/27), off-stack) and stack #39 ([#24](https://github.com/WarbyParker/monocle-mcp/pull/24) → [#35](https://github.com/WarbyParker/monocle-mcp/pull/35) → [#37](https://github.com/WarbyParker/monocle-mcp/pull/37) → [#38](https://github.com/WarbyParker/monocle-mcp/pull/38) → [#40](https://github.com/WarbyParker/monocle-mcp/pull/40) → [#41](https://github.com/WarbyParker/monocle-mcp/pull/41)) all open, awaiting review.
- Row 10: `oic_get_instance_activity_stream` after the live S2 probe (the probe still owes the activity-stream shape, name-filter semantics and `expand=connection`; the casing question is settled — camelCase-only, kebab aliases dropped).

## Artifacts

- Plan: `tickets/OTCM-158442/plan.md`
- IDCS ask draft: `tickets/OTCM-158442/tony_message_idcs.md`
