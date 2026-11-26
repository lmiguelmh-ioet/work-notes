# OTCM-151549 — no RICE: Spike — call Oracle Fusion with an IDCS token from Okta

- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-151549
- **RICE**: — (no RICE; spike feeding the SCM/FIN MCP tickets OTCM-151536 / OTCM-151537)
- **Repos**: none — unversioned scratch under `tickets/OTCM-151549/` (no PR by design)
- **Status** (as of 2026-11-17 12:45): ID-JAG track unblocked on the Oracle side — Tony created the trust `WP-OKTA-IPT-DEV1` (id `6697bfebd7d74f939ba7b3047220d72f`, active) and the confidential exchange client `0fc395d6920946e6b6f551ab3dd53c5a` (secret delivered) on 2026-11-17. One queued fix: the trust's issuer went in scheme-less; patch if the real token's `iss` carries `https://` (expected). The Okta-side work routes via [TECHSERV-14930](https://warbyparker.atlassian.net/browse/TECHSERV-14930) (filed 2026-11-17, assigned Caitlyn Durning): issuer confirmation, the token-minting app `WP-OTCM-151549-XCHG-DEV1`, the `sub`-claim question. Next: the app lands → mint + decode a real token → patch the trust → redemption probe.
- **Plan**: [otcm-151549_idcs_token_spike_c229fcc1.plan.md](../monocle_integrations/.cursor/plans/otcm-151549_idcs_token_spike_c229fcc1.plan.md) (approved; archive at wrap-up)

## Outcome

- The spike proves whether a person's Okta login can become an Oracle IDCS access token that carries that person's Fusion job roles and data security, attributable to them. This unblocks the SCM (OTCM-151536) and FIN (OTCM-151537) MCP servers.
- PROVEN 2026-11-09 on dev1: a person's Okta SSO login becomes an IDCS access token via authorization-code + PKCE (public Mobile client, no secret), and Fusion applies that person's data security. Identity: `userinfo` returns `sub=ext.lmamani@warbyparker.com`. Enforcement differential vs the service-account baseline: workers 5 rows → 0 rows, suppliers 200 → 403. No backend-held impersonation key anywhere in the flow.
- The asks went out 2026-11-06 as a group message to Tony + captain (Caitlyn) + Gabriel after two adversarial review rounds. Answers: the Okta assignment routed via Freshservice (#184054, resolved same-day — all three non-prod pods); the IDCS client registration settled to Tony, live Monday 2026-11-09 9 AM ET; every Oracle environment is confirmed on OCI IAM identity domains — the ID-JAG future track's hard gate is OPEN.
- ID-JAG redemption track: probed 2026-11-09 (undifferentiated HTTP 400 without an inbound trust), so the ask to Tony pivoted from the Mobile client to the Identity Propagation Trust plus a dedicated confidential app — both created on the dev1 identity domain 2026-11-17 (values on record in `monday_session_prep.md`). The Okta-side token-minting app is in flight via TECHSERV-14930. Open last mile: whether a redeemed token can carry the FA scope (probe once the app lands, else Oracle SR).
- Results draft: `spike/07_report_draft.md` — ship local stdio PKCE servers now; graduate to a remote confidential server when distribution/audit demands it; ID-JAG as the future track. Confluence draft page created 2026-11-17 under OT → OIC Spikes ([draft 10714644510](https://warbyparker.atlassian.net/wiki/pages/resumedraft.action?draftId=10714644510&draftShareId=08d5e31a-3d35-40dc-a2e5-5386808a469e)) from `spike/07_report_confluence.md` — the restructured publish version, minus the token-verification subdetail, the recommendation, and the open items. Evidence zip `spike/evidence_dev1_20261109_bundles.zip` (58 KB) ready; page published by Luis 2026-11-17. The MCP attachment upload failed (v2 `attachment-upload` 401s a valid media token at the edge; raw media-API path 403s), so the zip goes on the page by drag-in / Attachments UI.

## What shipped

Nothing merged — no PRs by design. Local deliverables under `tickets/OTCM-151549/`:

- `spike/okta_to_idcs.py` — both-mode script: mode B (auth-code + PKCE in Oracle FSCR's shape — loopback listener on 127.0.0.1:8765, browser auto-open, manual carry fallback; no token cache), mode A (Okta device flow → IDCS jwt-bearer, demoted to optional probe), shared legs (userinfo + ranked read-only Fusion GETs + tokenRelay probes), negative control, resume flags.
- `spike/mock_e2e_test.py` — offline E2E against local mock Okta/IDCS/FA with real RSA JWTs and JWKS; 3 cases green (A, B-listener, B-manual); mirrors probed real-stripe behavior (bearer-gated JWKS, generic issuer); designed for later promotion to real code.
- `spike/baseline_service_account.py` — service-account baseline, run live on dev1 2026-11-02; kept in its own file so the spike script carries no `oracle_oauth` references.
- `spike/README.md`, `spike/RUNBOOK.md` — how to run, verified values, troubleshooting.
- `registration_request.md` — the detailed ask set (superseded for routing by the group message; kept for the detailed wording).
- `group_message_registration.md` — the registration asks as sent 2026-11-06 (Tony + captain + Gabriel), after two adversarial review rounds.
- `monday_session_prep.md` — the Monday-session runbook: 12-step OCI click-path, evidence capture, Q&A both directions, failure fallbacks, post-session steps; now also carries the IPT setup guide.
- `tony_message_ipt.md` — the dev1 IPT + confidential-app ask to Tony (trust `WP-OKTA-IPT-DEV1`, app `WP-OKTA-XCHG-DEV1`), sent 2026-11-09; executed by Tony 2026-11-17.
- `caitlyn_message_okta.md` — the Okta-side ask (app, issuer confirmation, claim question): merged from 3 independent drafts + 2 adversarial reviews (2026-11-09), reshaped to the Tony step format and re-verified by 2 forensic reviewers (2026-11-17, fixes applied).
- `freshservice_okta_app_ticket.md` — the intake-ticket draft; filed by Luis as [TECHSERV-14930](https://warbyparker.atlassian.net/browse/TECHSERV-14930) 2026-11-17 (assigned Caitlyn Durning, Backlog).
- `spike/07_report_draft.md` — spike results working draft: approaches register, trust-anchor analysis, token-verification subdetail, local-vs-remote MCP shapes, recommendation for OTCM-151536/151537.
- `spike/07_report_confluence.md` — the Confluence publish version (2026-11-17): same content restructured (Summary → Background and goal → Approaches evaluated → Security analysis → Deployment shapes), minus the token-verification subdetail, the recommendation, and the open items.
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
15. The trust's issuer went in scheme-less (`warbyparker.okta.com/oauth2/default`) because the create command was executed verbatim without the scheme; the fix flow is decode a real token first, then patch the issuer if it carries `https://` (issuer is editable, only `name` is immutable) — before any redemption probe (2026-11-17).
16. The Okta-side work routes via TECHSERV-14930 at the Okta team's request (2026-11-17); the claim question is optional in the ask — Luis decodes his own token once the app lands, so no token ever changes hands.
17. The Okta app carries both grants up front (Device Authorization primary, Authorization Code + PKCE fallback) so a device-flow snag does not cost a second ticket; the loopback redirect URI is a form requirement under PKCE, disclosed as spike-scoped with deactivation after the probe rounds (2026-11-17, verifier-informed).

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
- 2026-11-17 15:10 UTC, Tony executed the IPT create in Cloud Shell: trust `WP-OKTA-IPT-DEV1` id `6697bfebd7d74f939ba7b3047220d72f` (active, type JWT, OCID recorded in `monday_session_prep.md`), redeeming client `0fc395d6920946e6b6f551ab3dd53c5a` (client-credentials only; secret delivered), provisional `sub`→`userName` mapping, `allow-impersonation false`, JWKS endpoint with scheme. Deltas: the endpoint needed `:443`; the issuer went in scheme-less — patch decision pending a real token decode.
- 2026-11-17, Caitlyn message verified by 2 forensic reviewers (word/sentence SEND-WITH-FIXES — applied; steps/need SEND) and filed as TECHSERV-14930 with the same three asks (issuer confirmation, app, claim question).
- Jira evidence comment drafted (`spike/evidence_dev1_20261109/07_jira_comment_draft.md`), not yet posted.

## Test data

- No Oracle fixtures: the mock E2E generates its own RSA keys and users; baseline artifacts live under `tickets/OTCM-151549/spike/evidence_baseline/`.

## Open items

- [TECHSERV-14930](https://warbyparker.atlassian.net/browse/TECHSERV-14930) (Caitlyn): issuer confirmation, Client ID of `WP-OTCM-151549-XCHG-DEV1`, claim answer if known. Then: mint + decode a real token, patch the trust issuer (expected) and mapping (if needed), run the redemption probe (Basic `0fc395d6920946e6b6f551ab3dd53c5a:<secret>`); if redemption works, test whether the token carries the FA scope (Oracle SR is the fallback).
- Tony's Username/Email report for `ext.lmamani@warbyparker.com` (feeds the `mail`-mapping fallback — likely needed: the custom-AS default `sub` is expected to be the raw `lmamani@warbyparker.com`).
- Positive 200-with-rows proof: one read-only dev1 job role for Luis (`spike/evidence_dev1_20261109/06_role_request.txt`).
- Token-lifecycle enablement (introspect, revoke) rides the future confidential registration — settled for the public client 2026-11-09.
- IDCS token-issuance audit events: location + export (Tony Q4, still unanswered).
- Post the Jira evidence comment on OTCM-151549 covering S1–S6 (draft ready); name the target status and stop — QA moves the ticket.
- Surface to the team: Oracle's password-auth deprecation (enforceable 2027-03-31) affects monocle stage/prod, still on static Basic auth.
- Optional: repeat the run on stage (stripe discovered, same capabilities).

Completed:

- ~~Tony invite for Monday 2026-11-09 9 AM ET~~ — session held 2026-11-09.
- ~~Freshservice #184054~~ RESOLVED 2026-11-06 — all three non-prod pod apps assigned (dev1, stage, dev2).
- ~~Monday session registration~~ — registered and activated on the dev1 identity domain 2026-11-09 as **`MCP Test Dev1`** (the click-path's proposed name was `WP-OTCM-151549-SPIKE-CLI`; Tony named it at creation — console searches must use `MCP Test Dev1`), client id `80ca07a94d124a4487e8ed61877d46dd`; "Enforce grants as authorization" was CHECKED on the create screen, so Luis's user was assigned post-activation from the app's Users tab. Per-step execution record: `tickets/OTCM-151549/monday_session_prep.md` (✅/⏭️ markers).
- ~~Run mode B live on dev1~~ — done 2026-11-09 09:14 ET; proven (see Evidence).
- ~~Draft the two-track results report~~ — `spike/07_report_draft.md` drafted 2026-11-09; updated for publish 2026-11-17.
- ~~Send `tony_message_ipt.md` to Tony~~ — sent 2026-11-09.
- ~~Tony IPT + confidential app~~ — executed 2026-11-17 15:10 UTC (trust `6697bfebd7d74f939ba7b3047220d72f`, client `0fc395d6920946e6b6f551ab3dd53c5a`, secret delivered).
- ~~Caitlyn Okta-side ask~~ — verified 2026-11-17; filed as TECHSERV-14930 (Caitlyn's team asked for a ticket).
- ~~Confluence publish approval~~ — granted 2026-11-17; Luis publishes the report.

## Artifacts

- Ticket folder: `tickets/OTCM-151549/` (`group_message_registration.md`, `monday_session_prep.md`, `tony_message_ipt.md`, `caitlyn_message_okta.md`, `freshservice_okta_app_ticket.md`, `registration_request.md`, `spike/` with script, mock, baseline, docs, research consolidations, results draft, `evidence_baseline/`, `evidence_dev1_20261109*/`).
- Plan: `monocle_integrations/.cursor/plans/otcm-151549_idcs_token_spike_c229fcc1.plan.md`.
- Related tickets: [OTCM-151536](https://warbyparker.atlassian.net/browse/OTCM-151536) (SCM MCP), [OTCM-151537](https://warbyparker.atlassian.net/browse/OTCM-151537) (FIN MCP) — both blocked by this spike; [TECHSERV-14930](https://warbyparker.atlassian.net/browse/TECHSERV-14930) (WP IT intake for the Okta-side items, assigned Caitlyn Durning).
