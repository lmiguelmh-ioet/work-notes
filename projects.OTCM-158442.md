# OTCM-158442 — OIC MCP server in monocle-mcp

- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-158442
- **RICE**: — (no RICE; OIC track of the MCP epic OTCM-158710)
- **Repos**: monocle-mcp
- **Status** (as of 2026-11-24): In flight — #21 and #22 merged, PR 3 open as #24, PR 4 open as #27, PR 5 open as #31
- **Plan**: [tickets/OTCM-158442/plan.md](../tickets/OTCM-158442/plan.md)

## Outcome

- In flight. Read-only OIC tools on the inherited FastMCP mount, Okta (IDCS)
  authorization-code + PKCE login, memory-only AES-GCM sessions.

## What shipped

- PR [#21](https://github.com/WarbyParker/monocle-mcp/pull/21) — Oracle config + IDCS client — MERGED.
- PR [#22](https://github.com/WarbyParker/monocle-mcp/pull/22) — encrypted memory-only session store — MERGED (squash `15b10bc`; 20-finding review, 7 fixes as one hardening commit; conflicts with main's #9 CI/coverage wave resolved as `22072a3`).
- PR [#24](https://github.com/WarbyParker/monocle-mcp/pull/24) — Okta login/callback routes — OPEN (5 light review rounds, comment cleanup, two main merges, coverage pin for `_verified_user`; includes the OAuth query scrub; 459 unit tests + 1 xfailed, 100% coverage green; a same-day scrub/SDK descope, `7cfc8de`, was reverted by `16cfb98` after the SDK proved to predate the PR, introduced in #7).
- PR [#27](https://github.com/WarbyParker/monocle-mcp/pull/27) — dev-only entry point for local runs — OPEN. Shape changed from the plan's config-gated `dev_user` (option A, parked as stash + patch) to a `.dockerignore`-excluded `dev_server.py` per user direction. Three light review rounds (15 panel seats + 6 triage verdicts): 14 findings implemented, 7 skipped as the documented indirection/residual class. Hardening commit `11d950b` pushed 2026-11-23; 402 unit tests + 1 xfailed, 100% coverage green.
- PR [#31](https://github.com/WarbyParker/monocle-mcp/pull/31) — OIC client routes + error taxonomy — OPEN. 7-seat panel, 16 triage findings resolved (5 implemented, 3 cosmetic accepted, rest follow-ups recorded in plan.md). Per user direction (option C), `parse_retry_after` deduped out of both `_errors.py` twins into shared `common/src/clients/_retry_after.py`, including the monocle naive-`now` guard (unreachable at runtime). 3-seat delta review SHIP ×3, zero findings. Commit `df0a4d5`; 467 unit tests + 1 xfailed, 100% coverage green.

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

## Evidence

- None yet. QA scenarios S1–S13 run post-implementation; S7's evidence is PR 3's ADA/BOB full-flow unit tests.

## Test data

- `AccessIssuer` ADA/BOB fake identities (`common/src/auth/fake_access.py`); mock IDCS transport.

## Open items

- Q7 — spike client needs the OIC scope + this app's redirect URIs; ask drafted at `tickets/OTCM-158442/tony_message_idcs.md`, awaiting Tony's reply. Blocks the dev manual run and stage, not PRs.
- Q8 — stage Access app + hostname (OTCM-158707 track); also owns the replica-affinity pin.
- PR 3 ([#24](https://github.com/WarbyParker/monocle-mcp/pull/24)) open 2026-11-20 with the `enhancement` label; awaiting review. Main merged 2026-11-20 (#13 EKS infra, clean, `720e764`). Bugbot round 1 (High: OAuth secrets in telemetry) answered; a follow-up correction notes the scrub's restoration (`16cfb98`), making the finding moot.
- PR 4 ([#27](https://github.com/WarbyParker/monocle-mcp/pull/27)) open with the `enhancement` label; hardening commit `11d950b` pushed 2026-11-23 after three light review rounds.
- PR 5 ([#31](https://github.com/WarbyParker/monocle-mcp/pull/31)) open 2026-11-24 with the `enhancement` label; awaiting review. Next: PR 6 of the plan (origin-locked OIC client), branched off PR 5's tip until #31 merges.

## Artifacts

- Plan: `tickets/OTCM-158442/plan.md`
- IDCS ask draft: `tickets/OTCM-158442/tony_message_idcs.md`
