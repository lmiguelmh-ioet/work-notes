# OTCM-151549 — no RICE: Spike — call Oracle Fusion with an IDCS token from Okta

- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-151549
- **RICE**: — (no RICE; spike feeding the SCM/FIN MCP tickets OTCM-151536 / OTCM-151537)
- **Repos**: none — unversioned scratch under `tickets/OTCM-151549/` (no PR by design)
- **Status** (as of 2026-11-06 16:35): #1 DONE — Freshservice #184054 resolved; Luis has all three non-prod Okta apps (dev1, stage, dev2). Only #2 remains: the IDCS Mobile client, live with Tony Monday 2026-11-09 9 AM ET. Prep doc ready, self-tests green.
- **Plan**: [otcm-151549_idcs_token_spike_c229fcc1.plan.md](../monocle_integrations/.cursor/plans/otcm-151549_idcs_token_spike_c229fcc1.plan.md) (approved; archive at wrap-up)

## Outcome

- The spike proves whether a person's Okta login can become an Oracle IDCS access token that carries that person's Fusion job roles and data security, attributable to them. This unblocks the SCM (OTCM-151536) and FIN (OTCM-151537) MCP servers.
- The asks went out 2026-11-06 as a group message to Tony + captain (Caitlyn) + Gabriel after two adversarial review rounds. Answers: the Okta assignment routed via Freshservice (#184054, resolved same-day — all three non-prod pods); the IDCS client registration is Tony's (or Joel's), live Monday 2026-11-09 9 AM ET; every Oracle environment is confirmed on OCI IAM identity domains — the ID-JAG future track's hard gate is OPEN (whether ID-JAG tokens can carry the FA scope stays open — probe / Oracle SR).
- The live Okta-user run waits on Monday's registration plus the Freshservice assignment. Prep: `monday_session_prep.md` (12-step OCI click-path, Q&A both directions, fallbacks); endpoint self-tests green.

## What shipped

Nothing merged — no PRs by design. Local deliverables under `tickets/OTCM-151549/`:

- `spike/okta_to_idcs.py` — both-mode script: mode B (auth-code + PKCE in Oracle FSCR's shape — loopback listener on 127.0.0.1:8765, browser auto-open, manual carry fallback; no token cache), mode A (Okta device flow → IDCS jwt-bearer, demoted to optional probe), shared legs (userinfo + ranked read-only Fusion GETs + tokenRelay probes), negative control, resume flags.
- `spike/mock_e2e_test.py` — offline E2E against local mock Okta/IDCS/FA with real RSA JWTs and JWKS; 3 cases green (A, B-listener, B-manual); mirrors probed real-stripe behavior (bearer-gated JWKS, generic issuer); designed for later promotion to real code.
- `spike/baseline_service_account.py` — service-account baseline, run live on dev1 2026-11-02; kept in its own file so the spike script carries no `oracle_oauth` references.
- `spike/README.md`, `spike/RUNBOOK.md` — how to run, verified values, troubleshooting.
- `registration_request.md` — the detailed ask set (superseded for routing by the group message; kept for the detailed wording).
- `group_message_registration.md` — the registration asks as sent 2026-11-06 (Tony + captain + Gabriel), after two adversarial review rounds.
- `monday_session_prep.md` — the Monday-session runbook: 12-step OCI click-path, evidence capture, Q&A both directions, failure fallbacks, post-session steps.
- `spike/research_user_context_api_paths.md`, `spike/research_saml2_grant_evidence.md`, `spike/research_nonbrowser_saml.md` — the research panels' consolidations (rounds 1–3).

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
7. No backend-held key mints user assertions — identity flows from the real per-login Okta authentication (Luis, 2026-11-06). Self-signed JWT user assertions rejected.
8. Ship-now = mode B in Oracle FSCR's exact shape (loopback listener, browser auto-open, manual carry fallback); deliberate deviation: no token cache (FSCR persists tokens). FSCR audited 2026-11-06 @ `28016957`: zero key material, pure-stdlib REST — cite it pinned as documentation, never vendor it (one commit, no tests/CI).
9. saml2-bearer dropped after three zero-evidence rounds; the 11-05 dedicated-SAML-app DM to captain was withdrawn inside the group message.
10. Registration routing: captain (Caitlyn Durning) per Tony's pointer — Gabriel does not own it. The asks went as one group message (2026-11-06), Luis's tightened edit.

## Evidence

- 2026-11-02, local → dev1, service-account baseline (client credentials, user-provided `OIC_*` creds): workers 200/5 rows, suppliers 200/5, purchaseRequisitions 200/0, emps 403, purchaseOrders >90 s timeout, tokenRelay 404 on both paths. Artifacts: `tickets/OTCM-151549/spike/evidence_baseline/`.
- 2026-11-02, live probes folded into script and docs: real FA scope `urn:opc:resource:fa:instanceid=700741357urn:opc:resource:consumer::all`; token `aud` = pod URL + `urn:opc:resource:fa:instanceid=700741357`; `iss` = generic `https://identity.oraclecloud.com/`; JWKS endpoint 401 anonymous, 200 with any valid stripe bearer; userinfo 401 for client-credentials tokens.
- 2026-11-02, offline mock E2E: both modes green with real RSA JWTs/JWKS.
- 2026-11-06, endpoint self-tests (anonymous GETs): dev1 stripe discovery UNCHANGED post-identity-domain upgrade (`authorization_code`, `S256`, token auth `none`, generic issuer); stage identity domain discovered via the pod SSO redirect chain — `idcs-b7bad0ece4ec4783904462b854ef8572` (26C, `FAAppResource_11-13-26-07`), identical capabilities; mock e2e 3/3 green.
- 2026-11-06, registration thread (Tony + captain + Gabriel): #1 routes via Freshservice; #2 settled to Tony (or Joel), live Monday 9 AM ET; #3(a) "all of our oracle environments were updated" — identity domains everywhere; #3(b) unknown ("i'm not sure about part b").
- No Jira evidence comment yet (posts after the live runs).

## Test data

- No Oracle fixtures: the mock E2E generates its own RSA keys and users; baseline artifacts live under `tickets/OTCM-151549/spike/evidence_baseline/`.

## Open items

- Tony invite for Monday 2026-11-09 9 AM ET (Luis sends).
- ~~Freshservice #184054~~ RESOLVED 2026-11-06 — all three non-prod pod apps assigned (dev1, stage, dev2).
- Monday session: register + ACTIVATE `WP-OTCM-151549-SPIKE-CLI` on dev1's identity domain; capture the client_id (OAuth configuration → General Information, NOT the Application ID), the console-added scope string, and any console deltas from the FSCR click-path; ask Tony the role-inventory and audit-event routing (the dropped ask 4).
- Run mode B live on dev1 after the session — needs BOTH the client_id and the Okta assignment; iterate on errors; collect evidence artifacts.
- Post the Jira evidence comment on OTCM-151549 covering S1–S6; name the target status and stop (QA moves the ticket).
- Draft the two-track results report (`07_report_draft.md`): ship auth-code+PKCE now; track ID-JAG — gate open (identity domains everywhere), last mile (FA scope on ID-JAG tokens) still open (probe / Oracle SR). Confluence page only after explicit user approval.

## Artifacts

- Ticket folder: `tickets/OTCM-151549/` (`group_message_registration.md`, `monday_session_prep.md`, `registration_request.md`, `spike/` with script, mock, baseline, docs, research consolidations, `evidence_baseline/`).
- Plan: `monocle_integrations/.cursor/plans/otcm-151549_idcs_token_spike_c229fcc1.plan.md`.
- Related tickets: [OTCM-151536](https://warbyparker.atlassian.net/browse/OTCM-151536) (SCM MCP), [OTCM-151537](https://warbyparker.atlassian.net/browse/OTCM-151537) (FIN MCP) — both blocked by this spike.
