# OTCM-151549 — no RICE: Spike — call Oracle Fusion with an IDCS token from Okta

- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-151549
- **RICE**: — (no RICE; spike feeding the SCM/FIN MCP tickets OTCM-151536 / OTCM-151537)
- **Repos**: none — unversioned scratch under `tickets/OTCM-151549/` (no PR by design)
- **Status** (as of 2026-11-02): In flight — all human-independent work done and validated; blocked on the IDCS/Okta registrations before the live Okta-user runs.
- **Plan**: [otcm-151549_idcs_token_spike_c229fcc1.plan.md](../monocle_integrations/.cursor/plans/otcm-151549_idcs_token_spike_c229fcc1.plan.md) (approved; archive at wrap-up)

## Outcome

- The spike proves whether a person's Okta login can become an Oracle IDCS access token that carries that person's Fusion job roles and data security, attributable to them. This unblocks the SCM (OTCM-151536) and FIN (OTCM-151537) MCP servers.
- All human-independent work is done: registration request ready to route, both-mode spike script green on an offline mock E2E, service-account baseline proven live on dev1.
- The live Okta-user runs wait on the IDCS/Okta registrations (human ask, drafted and ready).

## What shipped

Nothing merged — no PRs by design. Local deliverables under `tickets/OTCM-151549/`:

- `spike/okta_to_idcs.py` — both-mode script: mode A (Okta device flow → IDCS jwt-bearer), mode B (auth-code + PKCE, manual carry), shared legs (userinfo + ranked read-only Fusion GETs + tokenRelay probes), negative control, resume flags.
- `spike/mock_e2e_test.py` — offline E2E against local mock Okta/IDCS/FA with real RSA JWTs and JWKS; both modes green; mirrors probed real-stripe behavior (bearer-gated JWKS, generic issuer); designed for later promotion to real code.
- `spike/baseline_service_account.py` — service-account baseline, run live on dev1 2026-11-02; kept in its own file so the spike script carries no `oracle_oauth` references.
- `spike/README.md`, `spike/RUNBOOK.md` — how to run, verified values, troubleshooting.
- `registration_request.md` — the five asks to Gabriel/IAM admin, in tight (Slack) and detailed (Jira) versions.

## Decisions

### Functional clarifications (Q&A)

1. Pod for the proof: dev1 (`fa-evdi-dev1-saasfaprod1.fa.ocs.oraclecloud.com`, stripe `idcs-7c787f6dbe004e7fb7952a6fe3da17d5`) — Luis, chat, 2026-11-02.
2. Scope: test ALL viable flows, not just one; publish results as a Confluence page only after explicit user approval — Luis, chat, 2026-11-02 (round-4 directive).
3. Spike code lives unversioned in `tickets/OTCM-151549/spike/`; no PR — Luis, chat.
4. The mock service gets designed for later promotion to real code — Luis, chat ("we can later promote that mock service to code").
5. Baseline creds provided by the user as `OIC_*` vars in `~/projects/ioet/.env.dev1`; token URL host verified to be the dev1 FA stripe — Luis, chat.

### Design decisions (ours)

1. Mode A uses the Okta device-authorization flow into the IDCS jwt-bearer grant, with an access-token→id-token assertion fallback: which assertion the trust accepts stays unknown until the registrations answer.
2. Mode B uses authorization-code + PKCE with manual code carry and a dead redirect — no localhost listener, so it needs no reachable callback.
3. `decode_verified` accepts the generic IDCS issuer `https://identity.oraclecloud.com/` and takes a `jwks_bearer` parameter — both probed live (JWKS 401s anonymous; FA-stripe tokens carry the generic iss, not the stripe URL).
4. The baseline sits in a separate file so the spike script stays free of `oracle_oauth` references and the S5 proof (no monocle shared account) remains clean.
5. Evidence artifacts trim PII; 90 s per-request timeout plus per-candidate transport-error resilience, because dev1 collection GETs can exceed 90 s.
6. The mock E2E mirrors probed real-stripe behavior so the first live run exercises code already green offline.

## Evidence

- 2026-11-02, local → dev1, service-account baseline (client credentials, user-provided `OIC_*` creds): workers 200/5 rows, suppliers 200/5, purchaseRequisitions 200/0, emps 403, purchaseOrders >90 s timeout, tokenRelay 404 on both paths. Artifacts: `tickets/OTCM-151549/spike/evidence_baseline/`.
- 2026-11-02, live probes folded into script and docs: real FA scope `urn:opc:resource:fa:instanceid=700741357urn:opc:resource:consumer::all`; token `aud` = pod URL + `urn:opc:resource:fa:instanceid=700741357`; `iss` = generic `https://identity.oraclecloud.com/`; JWKS endpoint 401 anonymous, 200 with any valid stripe bearer; userinfo 401 for client-credentials tokens.
- 2026-11-02, offline mock E2E: both modes green with real RSA JWTs/JWKS.
- No Jira evidence comment yet (posts after the live runs).

## Test data

- No Oracle fixtures: the mock E2E generates its own RSA keys and users; baseline artifacts live under `tickets/OTCM-151549/spike/evidence_baseline/`.

## Open items

- Route `tickets/OTCM-151549/registration_request.md` to Gabriel/IAM admin — blocked on the human send. Five asks: jwt-bearer trust capability question, Flow A registrations, Flow B public client `WP-OTCM-151549-SPIKE-CLI`, audit evidence pull, audit-bar ratification.
- Pre-run role inventory from the functional admin — needed to prove the Fusion read applied the person's roles.
- Run both modes live on dev1 once registrations land; iterate on errors; collect evidence artifacts.
- Draft the results report; create the Confluence page only after explicit user approval (space/parent still open).
- Post the Jira evidence comment on OTCM-151549 covering S1–S6; name the target status and stop (QA moves the ticket).

## Artifacts

- Ticket folder: `tickets/OTCM-151549/` (`registration_request.md`, `spike/` with script, mock, baseline, docs, `evidence_baseline/`).
- Plan: `monocle_integrations/.cursor/plans/otcm-151549_idcs_token_spike_c229fcc1.plan.md`.
- Related tickets: [OTCM-151536](https://warbyparker.atlassian.net/browse/OTCM-151536) (SCM MCP), [OTCM-151537](https://warbyparker.atlassian.net/browse/OTCM-151537) (FIN MCP) — both blocked by this spike.
