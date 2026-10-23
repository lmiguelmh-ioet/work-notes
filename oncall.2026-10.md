# ON-CALL: 2026-10-19 → 2026-10-26

- **Board**: [OEH list, 10-19 → 10-26, not Rejected/Resolved](https://warbyparker.atlassian.net/jira/software/c/projects/OEH/list?jql=project%20%3D%20%22OEH%22%0AAND%20created%20%3E%3D%20%222026-10-19%22%0AAND%20created%20%3C%3D%20%222026-10-26%22%0AAND%20status%20NOT%20IN%20(Rejected%2C%20Resolved)%0AORDER%20BY%20created%20DESC)
- **Playbooks**: [team.oncall](team.oncall.md) · monocle branch `on-call-agent-wip` → `on-call-agent/skills/` (30 skills, synced with main 2026-10-22)
- **Prev**: `projects.md` → ON-CALL: AGO25-AGO31 (pre-convention) · **Next**: —

## Ledger

- `10-20 13:26` · [OEH-88425](https://warbyparker.atlassian.net/browse/OEH-88425) · WMS-I-1005 · pick confirm failure → C1 · pulled · Resolved (parent)
- `10-20 13:27` · [OEH-88426](https://warbyparker.atlassian.net/browse/OEH-88426) · WMS-I-1005 · pick confirm failure → C1 · pulled · Rejected (dup of OEH-88425)
- `10-20 13:27` · [OEH-88427](https://warbyparker.atlassian.net/browse/OEH-88427) · WMS-I-1005 · pick confirm failure → C1 · pulled · Rejected (dup of OEH-88425)
- `10-20 13:28` · [OEH-88429](https://warbyparker.atlassian.net/browse/OEH-88429) · WMS-I-1005 · pick confirm failure → C1 · pulled · Rejected (dup of OEH-88425)
- `10-21 15:01` · [OEH-88586](https://warbyparker.atlassian.net/browse/OEH-88586) · WMS-I-1005 · pick confirm failure → C1 · pulled · Rejected (dup of OEH-88425)
- `10-21 16:26` · [OEH-88620](https://warbyparker.atlassian.net/browse/OEH-88620) · IN-I-2017A · receiving inbound failure → already put away (concurrent-completion race) · pulled · Rejected
- `10-22 02:02` · [OEH-88627](https://warbyparker.atlassian.net/browse/OEH-88627) · GL-I-1060 · payroll to Anaplan failure → untriaged · pulled · Not Started
- `10-22 06:11` · [OEH-88628](https://warbyparker.atlassian.net/browse/OEH-88628) · WMS-I-1031 · production status update failure → untriaged · pulled · Not Started
- `10-22 08:17` · [OEH-88631](https://warbyparker.atlassian.net/browse/OEH-88631) · Comerica → EPM (ARCS) · bank rec failure → untriaged · pulled · Not Started

## Resolution clusters

### C1 — WMS-I-1005 — pick confirmation failure burst

- **Tickets**: [OEH-88425](https://warbyparker.atlassian.net/browse/OEH-88425) (parent — Resolved) · [OEH-88426](https://warbyparker.atlassian.net/browse/OEH-88426) · [OEH-88427](https://warbyparker.atlassian.net/browse/OEH-88427) · [OEH-88429](https://warbyparker.atlassian.net/browse/OEH-88429) · [OEH-88586](https://warbyparker.atlassian.net/browse/OEH-88586) (Rejected as dups) — 5 total
- **Signature**: order 1192224 (TO/LSLO) — WMS picked more than the open remainder per item; "Overpicked lines found" false positive (picked == SUM(requested) per item; remainder lines still Released to warehouse)
- **Playbook**: new `wms-i-1005-overpick` skill (branch `on-call-agent-wip`, commit pending) — Branch A corrected-payload replay at remainders; never plain-reprocess
- **Outcome**: resolved 10-23 — replay `POST /wms/pick-confirmation` HTTP 201 (uuid `3856d2c6-0499-4efd-83b1-8cea885ba989`), 3 remainder lines → Staged; parent Resolved with evidence attachments + comment, 4 dups Rejected. Root cause: overpick check compares running picked totals vs open remainder per item — OTCM bug pending. Watch for a follow-up `PickConfirmNotAllowedError` ticket → reject pointing to OEH-88425

## Knowledge delta

- Skill `in-i-2017a-receiving` created from OEH-88620 triage (branch `on-call-agent-wip`, commit pending): two-stage receiving verification — linesToPutAway + inboundShipments + errored-receipts + pending-putaway reports; reject-if-complete per OEH-65095.
- Skill candidate for Comerica → EPM (ARCS) bank rec: no skill covers EPM/ARCS failures. Trigger TBD after OEH-88631 triage.
- Prod monocle Lambda invoker: AWS profile `oic4` (`oic-monocle-integrations-lambda-prod`) — `oic`/`oic3` 403 on prod. User keys live in Secrets Manager `oic-monocle-integrations/ENV/lambda_user_keys`. Prod URL in `notes/urls.md`.
- OEH workflow quirk: terminal `Resolved` status is reached via the transition named **Complete** (id 231) from `Promote to Production`; the transition named "Resolved" (id 141) only loops back to Testing. Path: Not Started → Triage → In Progress → Test → Testing → Complete.

## Handoff
