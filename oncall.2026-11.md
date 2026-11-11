# ON-CALL: 2026-11-09 → 2026-11-16

- **Board**: [OEH list, 11-09 → 11-16, not Rejected/Resolved](https://warbyparker.atlassian.net/jira/software/c/projects/OEH/list?jql=project%20%3D%20%22OEH%22%0AAND%20created%20%3E%3D%20%222026-11-09%22%0AAND%20created%20%3C%3D%20%222026-11-16%22%0AAND%20status%20NOT%20IN%20(Rejected%2C%20Resolved)%0AORDER%20BY%20created%20DESC)
- **Playbooks**: [team.oncall](team.oncall.md) · monocle branch `on-call-agent-wip` → `on-call-agent/skills/`
- **Prev**: [oncall.2026-10](oncall.2026-10.md) · **Next**: —

## Ledger

- `11-10 03:03` · [OEH-91409](https://warbyparker.atlassian.net/browse/OEH-91409) · IN-I-2019 · serialized qty 683 vs 675 serials, item 846864072988 in Replen (8 blank-serial rows in the FedEx file) → C1 · pulled 11-10 (Triage + park comment 982419, Alexis asked on the recurring pattern) · healed 11-11 (`3FED AI Snapshot 2026-11-11`, header 300001052627077) · **Rejected** (evidence comment 983249) · closure re-verified 11-11 10:55: both 11-11 legs exist (AI 300001052627077 08:03:27, non-AI 300001052615551 08:03:31), ticket Rejected, both comments on it

## Resolution clusters

### C1 — IN-I-2019 — serialized qty vs serial count mismatch (blank serials)

- **Tickets**: [OEH-91409](https://warbyparker.atlassian.net/browse/OEH-91409) (Rejected) — 1 this rotation; same family as OEH-89046/89097/89352 from the October rotation (all Rejected after the next daily run)
- **Signature**: `Serialized line quantity (N) does not match serial count (M) for item <upc> in subinventory Replen` on the SFTP route; the merged (item, subinventory) group has rows with a blank Serial Number
- **Playbook**: `on-call-agent/skills/in-i-2019-serial-mismatch` (new this rotation; `verify_day.py` gives the day-0/day-1 verdict)
- **Outcome**: park day 0 (non-AI count landed, AI count is the only gap) → the next daily full snapshot recreates the AI count → Reject. Four failures in two weeks, each a different item — recurring FedEx-side file data quality; Alexis Tomacruz asked on OEH-91409 what to do about the pattern

## Knowledge delta

- New skill: `in-i-2019-serial-mismatch` (adversarial-reviewed, verified live on OEH-91409). Sibling `in-i-2019-snapshot-cleanup` rerouted: clean-and-reupload is no longer the default since OTCM-151489.
- Escalation routed out: recurring FedEx blank-serial defect (10-27, 10-28, 11-03, 11-10) raised to Alexis Tomacruz on OEH-91409 — answer pending.

## Open tickets

(None — OEH-91409 closed 11-11. Alexis's answer on the recurring FedEx blank-serial pattern is pending but tracked as a follow-up, not a ticket.)

## Handoff
