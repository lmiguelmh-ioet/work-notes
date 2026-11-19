# OTCM-158442 — OIC MCP server in monocle-mcp

- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-158442
- **RICE**: — (no RICE; OIC track of the MCP epic OTCM-158710)
- **Repos**: monocle-mcp
- **Status** (as of 2026-11-19): In flight — PRs 1–2 open, PR 3 starting
- **Plan**: [tickets/OTCM-158442/plan.md](../tickets/OTCM-158442/plan.md)

## Outcome

- In flight. Read-only OIC tools on the inherited FastMCP mount, Okta (IDCS)
  authorization-code + PKCE login, memory-only AES-GCM sessions.

## What shipped

- PR [#21](https://github.com/WarbyParker/monocle-mcp/pull/21) — Oracle config + IDCS client — OPEN.
- PR [#22](https://github.com/WarbyParker/monocle-mcp/pull/22) — encrypted memory-only session store — OPEN (20-finding review; 7 fixes landed as one hardening commit).

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
3. `redirect_slashes=False` on the main router; `/oauth/*` query scrub on spans and uvicorn access logs.
4. `IdcsClient` constructor https refusal + `oic_base_url` https pin deferred from #21's review — lands in PR 3 (PR 9 fallback).

## Evidence

- None yet. QA scenarios S1–S13 run post-implementation; S7's evidence is PR 3's ADA/BOB full-flow unit tests.

## Test data

- `AccessIssuer` ADA/BOB fake identities (`common/src/auth/fake_access.py`); mock IDCS transport.

## Open items

- Q7 — spike client needs the OIC scope + this app's redirect URIs; ask drafted at `tickets/OTCM-158442/tony_message_idcs.md`, awaiting Tony's reply. Blocks the dev manual run and stage, not PRs.
- Q8 — stage Access app + hostname (OTCM-158707 track); also owns the replica-affinity pin.
- PR 3 (login/callback routes) in progress.

## Artifacts

- Plan: `tickets/OTCM-158442/plan.md`
- IDCS ask draft: `tickets/OTCM-158442/tony_message_idcs.md`
