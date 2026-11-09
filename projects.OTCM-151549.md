# OTCM-151549 — no RICE: Spike — call Oracle Fusion with an IDCS token from Okta

- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-151549
- **RICE**: — (no RICE; spike feeding the SCM/FIN MCP tickets OTCM-151536 / OTCM-151537)
- **Repos**: none — unversioned scratch under `tickets/OTCM-151549/` (no PR by design)
- **Status** (as of 2026-11-09 17:00): Monday session DONE — `WP-OTCM-151549-SPIKE-CLI` (public Mobile client, id `80ca07a94d124a4487e8ed61877d46dd`) registered on the dev1 identity domain and mode B (auth-code + PKCE) PROVEN live. ID-JAG probed the same day: redemption is blocked on the inbound Identity Propagation Trust, and the IPT + confidential-app ask to Tony is drafted, ready to send (`tickets/OTCM-151549/tony_message_ipt.md`).
- **Plan**: [otcm-151549_idcs_token_spike_c229fcc1.plan.md](../monocle_integrations/.cursor/plans/otcm-151549_idcs_token_spike_c229fcc1.plan.md) (approved; archive at wrap-up)

## Outcome

- The spike proves whether a person's Okta login can become an Oracle IDCS access token that carries that person's Fusion job roles and data security, attributable to them. This unblocks the SCM (OTCM-151536) and FIN (OTCM-151537) MCP servers.
- PROVEN 2026-11-09 on dev1: a person's Okta SSO login becomes an IDCS access token via authorization-code + PKCE (public Mobile client, no secret), and Fusion applies that person's data security. Identity: `userinfo` returns `sub=ext.lmamani@warbyparker.com`. Enforcement differential vs the service-account baseline: workers 5 rows → 0 rows, suppliers 200 → 403. No backend-held impersonation key anywhere in the flow.
- The asks went out 2026-11-06 as a group message to Tony + captain (Caitlyn) + Gabriel after two adversarial review rounds. Answers: the Okta assignment routed via Freshservice (#184054, resolved same-day — all three non-prod pods); the IDCS client registration settled to Tony, live Monday 2026-11-09 9 AM ET; every Oracle environment is confirmed on OCI IAM identity domains — the ID-JAG future track's hard gate is OPEN.
- ID-JAG probed 2026-11-09: jwt-bearer redemption at the dev1 stripe returns an undifferentiated HTTP 400 for externally-issued assertions without an inbound trust, so the ask to Tony pivoted from the Mobile client to the Identity Propagation Trust plus a dedicated confidential app. Open last mile: whether a redeemed ID-JAG token can carry the FA scope (probe once the trust lands, else Oracle SR).
- Results draft: `spike/07_report_draft.md` — ship local stdio PKCE servers now; graduate to a remote confidential server when distribution/audit demands it; ID-JAG as the future track. Publish to Confluence only after explicit user approval.

## What shipped

Nothing merged — no PRs by design. Local deliverables under `tickets/OTCM-151549/`:

- `spike/okta_to_idcs.py` — both-mode script: mode B (auth-code + PKCE in Oracle FSCR's shape — loopback listener on 127.0.0.1:8765, browser auto-open, manual carry fallback; no token cache), mode A (Okta device flow → IDCS jwt-bearer, demoted to optional probe), shared legs (userinfo + ranked read-only Fusion GETs + tokenRelay probes), negative control, resume flags.
- `spike/mock_e2e_test.py` — offline E2E against local mock Okta/IDCS/FA with real RSA JWTs and JWKS; 3 cases green (A, B-listener, B-manual); mirrors probed real-stripe behavior (bearer-gated JWKS, generic issuer); designed for later promotion to real code.
- `spike/baseline_service_account.py` — service-account baseline, run live on dev1 2026-11-02; kept in its own file so the spike script carries no `oracle_oauth` references.
- `spike/README.md`, `spike/RUNBOOK.md` — how to run, verified values, troubleshooting.
- `registration_request.md` — the detailed ask set (superseded for routing by the group message; kept for the detailed wording).
- `group_message_registration.md` — the registration asks as sent 2026-11-06 (Tony + captain + Gabriel), after two adversarial review rounds.
- `monday_session_prep.md` — the Monday-session runbook: 12-step OCI click-path, evidence capture, Q&A both directions, failure fallbacks, post-session steps; now also carries the IPT setup guide.
- `tony_message_ipt.md` — the dev1 IPT + confidential-app ask to Tony (trust `WP-OKTA-IPT-DEV1`, app `WP-OKTA-XCHG-DEV1`), Slack-formatted, ready to send.
- `spike/07_report_draft.md` — spike results working draft: approaches register, trust-anchor analysis, token-verification subdetail, local-vs-remote MCP shapes, recommendation for OTCM-151536/151537.
- `spike/research_jwt_exchange.md` — research rounds 3/3b consolidation: JWT-exchange / ID-JAG evidence restricted to 2026-dated sources, GA status on both sides, full source register.
- `spike/research_user_context_api_paths.md`, `spike/research_saml2_grant_evidence.md`, `spike/research_nonbrowser_saml.md` — the earlier research panels' consolidations.
- `spike/evidence_dev1_20261109*/` — three live-run bundles from 2026-11-09: the proof run (09:14 ET), the token demo (09:18), the introspection/revocation probes plus the console screenshot (13:04).

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
11. Ship-now = local stdio MCP servers with auth-code + PKCE against the pod's identity domain; the remote hosted shape graduates later and upgrades the client to confidential (report recommendation, 2026-11-09).
12. The ID-JAG redemption leg needs a dedicated confidential client: Oracle's documented exchange authenticates with Basic `client_id:client_secret`; two independent reviews (2026-11-09) ruled the public client out — the IPT ask builds that app in.
13. Introspection and revocation are settled as not console-enableable for the public Mobile client (the endpoint rejects the client verbatim; the modern console exposes no Introspect flag — console walk with the IAM admin 2026-11-09); both token-lifecycle items ride the future confidential registration.
14. Trust-anchor analysis accepted: ID-JAG introduces no new compromise class — Okta is already the trust anchor via SAML federation, and revoking the inbound trust kills the path centrally in one move.

## Evidence

- 2026-11-02, local → dev1, service-account baseline (client credentials, user-provided `OIC_*` creds): workers 200/5 rows, suppliers 200/5, purchaseRequisitions 200/0, emps 403, purchaseOrders >90 s timeout, tokenRelay 404 on both paths. Artifacts: `tickets/OTCM-151549/spike/evidence_baseline/`.
- 2026-11-02, live probes folded into script and docs: real FA scope `urn:opc:resource:fa:instanceid=700741357urn:opc:resource:consumer::all`; token `aud` = pod URL + `urn:opc:resource:fa:instanceid=700741357`; `iss` = generic `https://identity.oraclecloud.com/`; JWKS endpoint 401 anonymous, 200 with any valid stripe bearer; userinfo 401 for client-credentials tokens.
- 2026-11-02, offline mock E2E: both modes green with real RSA JWTs/JWKS.
- 2026-11-06, endpoint self-tests (anonymous GETs): dev1 stripe discovery UNCHANGED post-identity-domain upgrade (`authorization_code`, `S256`, token auth `none`, generic issuer); stage identity domain discovered via the pod SSO redirect chain — `idcs-b7bad0ece4ec4783904462b854ef8572` (26C, `FAAppResource_11-13-26-07`), identical capabilities; mock e2e 3/3 green.
- 2026-11-06, registration thread (Tony + captain + Gabriel): #1 routes via Freshservice; #2 settled to Tony (or Joel), live Monday 9 AM ET; #3(a) "all of our oracle environments were updated" — identity domains everywhere; #3(b) unknown ("i'm not sure about part b").
- 2026-11-09 09:14 ET, live dev1 run of mode B (client `80ca07a94d124a4487e8ed61877d46dd`): Okta SSO → IDCS user-bound token; `userinfo` 200 with `sub=ext.lmamani@warbyparker.com`; Fusion differential vs the service-account baseline — workers 5 rows → 0 rows, suppliers 200 → 403. Artifacts: `spike/evidence_dev1_20261109/`.
- 2026-11-09, token-lifecycle probes on the live token: `userinfo` 200 (the holder-side active check works); `POST /oauth2/v1/introspect` 400 with the verbatim body "Client 80ca07a94d124a4487e8ed61877d46dd is not authorized to make introspect endpoint request"; `POST /oauth2/v1/revoke` 400 and the token stays valid. Console attempt found no Introspect flag for public Mobile apps (screenshot in bundle). Artifacts: `spike/evidence_dev1_20261109_introspect/`.
- 2026-11-09, ID-JAG probe: jwt-bearer redemption at the dev1 stripe with externally-issued assertions returns an undifferentiated HTTP 400 in every request shape tried; a missing inbound trust is not separately reported, so validating the config needs the admin side (the IPT ask) or an Oracle SR.
- 2026-11-09, research rounds 3/3b: ID-JAG is documented on both sides and GA'd within 90 days (Okta XAA GA 2026-08-17; OCI IAM identity-domain ID-JAG GA 2026-10-09 with Okta named as an accepted issuer); no public success report for FA scopes. Oracle deprecated password-based Fusion connectivity 2026-11-06, enforceable 2027-03-31.
- Jira evidence comment drafted (`spike/evidence_dev1_20261109/07_jira_comment_draft.md`), not yet posted.

## Test data

- No Oracle fixtures: the mock E2E generates its own RSA keys and users; baseline artifacts live under `tickets/OTCM-151549/spike/evidence_baseline/`.

## Open items

- Send `tony_message_ipt.md` to Tony (dev1 IPT + confidential app). Waiting back: the client id + secret (secret via a secure channel), the trust id, and the stored Username/Email values for `ext.lmamani@warbyparker.com` (feeds the trust's subject-mapping choice).
- Once the trust lands: re-run the ID-JAG redemption probe on dev1; if redemption works, test whether the token carries the FA scope (the open last mile; Oracle SR is the fallback).
- Positive 200-with-rows proof: one read-only dev1 job role for Luis (`spike/evidence_dev1_20261109/06_role_request.txt`).
- Token-lifecycle enablement (introspect, revoke) rides the future confidential registration — settled for the public client 2026-11-09.
- IDCS token-issuance audit events: location + export (Tony Q4, still unanswered).
- Post the Jira evidence comment on OTCM-151549 covering S1–S6 (draft ready); name the target status and stop — QA moves the ticket.
- Publish the results report to Confluence — only after explicit user approval.
- Surface to the team: Oracle's password-auth deprecation (enforceable 2027-03-31) affects monocle stage/prod, still on static Basic auth.
- Optional: repeat the run on stage (stripe discovered, same capabilities).

Completed:

- ~~Tony invite for Monday 2026-11-09 9 AM ET~~ — session held 2026-11-09.
- ~~Freshservice #184054~~ RESOLVED 2026-11-06 — all three non-prod pod apps assigned (dev1, stage, dev2).
- ~~Monday session registration~~ — `WP-OTCM-151549-SPIKE-CLI` registered and activated on the dev1 identity domain (client id `80ca07a94d124a4487e8ed61877d46dd`).
- ~~Run mode B live on dev1~~ — done 2026-11-09 09:14 ET; proven (see Evidence).
- ~~Draft the two-track results report~~ — `spike/07_report_draft.md` drafted 2026-11-09; Confluence publish pending approval.

## Artifacts

- Ticket folder: `tickets/OTCM-151549/` (`group_message_registration.md`, `monday_session_prep.md`, `tony_message_ipt.md`, `registration_request.md`, `spike/` with script, mock, baseline, docs, research consolidations, results draft, `evidence_baseline/`, `evidence_dev1_20261109*/`).
- Plan: `monocle_integrations/.cursor/plans/otcm-151549_idcs_token_spike_c229fcc1.plan.md`.
- Related tickets: [OTCM-151536](https://warbyparker.atlassian.net/browse/OTCM-151536) (SCM MCP), [OTCM-151537](https://warbyparker.atlassian.net/browse/OTCM-151537) (FIN MCP) — both blocked by this spike.
