# ON-CALL: 2026-10-19 → 2026-10-26

- **Board**: [OEH list, 10-19 → 10-26, not Rejected/Resolved](https://warbyparker.atlassian.net/jira/software/c/projects/OEH/list?jql=project%20%3D%20%22OEH%22%0AAND%20created%20%3E%3D%20%222026-10-19%22%0AAND%20created%20%3C%3D%20%222026-10-26%22%0AAND%20status%20NOT%20IN%20(Rejected%2C%20Resolved)%0AORDER%20BY%20created%20DESC)
- **Playbooks**: [team.oncall](team.oncall.md) · monocle branch `on-call-agent-wip` → `on-call-agent/skills/` (30 skills, synced with main 2026-10-22)
- **Prev**: `projects.md` → ON-CALL: AGO25-AGO31 (pre-convention) · **Next**: —

## Ledger

- `10-20 13:26` · [OEH-88425](https://warbyparker.atlassian.net/browse/OEH-88425) · WMS-I-1005 · pick confirm failure → C1 · pulled · Not Started
- `10-20 13:27` · [OEH-88426](https://warbyparker.atlassian.net/browse/OEH-88426) · WMS-I-1005 · pick confirm failure → C1 · pulled · Not Started
- `10-20 13:27` · [OEH-88427](https://warbyparker.atlassian.net/browse/OEH-88427) · WMS-I-1005 · pick confirm failure → C1 · pulled · Not Started
- `10-20 13:28` · [OEH-88429](https://warbyparker.atlassian.net/browse/OEH-88429) · WMS-I-1005 · pick confirm failure → C1 · pulled · Not Started
- `10-21 15:01` · [OEH-88586](https://warbyparker.atlassian.net/browse/OEH-88586) · WMS-I-1005 · pick confirm failure → C1 · pulled · Not Started
- `10-21 16:26` · [OEH-88620](https://warbyparker.atlassian.net/browse/OEH-88620) · IN-I-2017A · receiving inbound failure → untriaged · pulled · Not Started
- `10-22 02:02` · [OEH-88627](https://warbyparker.atlassian.net/browse/OEH-88627) · GL-I-1060 · payroll to Anaplan failure → untriaged · pulled · Not Started
- `10-22 06:11` · [OEH-88628](https://warbyparker.atlassian.net/browse/OEH-88628) · WMS-I-1031 · production status update failure → untriaged · pulled · Not Started
- `10-22 08:17` · [OEH-88631](https://warbyparker.atlassian.net/browse/OEH-88631) · Comerica → EPM (ARCS) · bank rec failure → untriaged · pulled · Not Started

## Resolution clusters

### C1 — WMS-I-1005 — pick confirmation failure burst

- **Tickets**: [OEH-88425](https://warbyparker.atlassian.net/browse/OEH-88425) · [OEH-88426](https://warbyparker.atlassian.net/browse/OEH-88426) · [OEH-88427](https://warbyparker.atlassian.net/browse/OEH-88427) · [OEH-88429](https://warbyparker.atlassian.net/browse/OEH-88429) · [OEH-88586](https://warbyparker.atlassian.net/browse/OEH-88586) (all Not Started) — 5 total
- **Signature**: TBD at triage — 4 landed in a 2-minute burst on 10-20 13:26–13:28, suggesting one upstream incident
- **Playbook**: `wms-i-1005-pick-confirm` skill (branch `on-call-agent-wip`) — reject if lines Interfaced/Staged/Canceled; reprocess from S3 Error payload if Released to warehouse
- **Outcome**: open

## Knowledge delta

- Skill candidate `in-i-2017a-receiving`: OEH-88620 is IN-I-2017A (receiving); only a 2017B ship-confirm skill exists. Trigger TBD after triage.
- Skill candidate for Comerica → EPM (ARCS) bank rec: no skill covers EPM/ARCS failures. Trigger TBD after OEH-88631 triage.

## Handoff
