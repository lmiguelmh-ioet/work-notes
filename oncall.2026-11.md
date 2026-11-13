# ON-CALL: 2026-11-09 → 2026-11-16

- **Board**: [OEH list, 11-09 → 11-16, not Rejected/Resolved](https://warbyparker.atlassian.net/jira/software/c/projects/OEH/list?jql=project%20%3D%20%22OEH%22%0AAND%20created%20%3E%3D%20%222026-11-09%22%0AAND%20created%20%3C%3D%20%222026-11-16%22%0AAND%20status%20NOT%20IN%20(Rejected%2C%20Resolved)%0AORDER%20BY%20created%20DESC)
- **Playbooks**: [team.oncall](team.oncall.md) · monocle branch `on-call-agent-wip` → `on-call-agent/skills/`
- **Prev**: [oncall.2026-10](oncall.2026-10.md) · **Next**: —

## Ledger

- `11-10 03:03` · [OEH-91409](https://warbyparker.atlassian.net/browse/OEH-91409) · IN-I-2019 · serialized qty 683 vs 675 serials, item 846864072988 in Replen (8 blank-serial rows in the FedEx file) → C1 · pulled 11-10 (Triage + park comment 982419, Alexis asked on the recurring pattern) · count recreated 11-11 (`3FED AI Snapshot 2026-11-11`, header 300001052627077) · **Rejected** (evidence comment 983249) · post-close discovery 11-13: that count's import failed 511/3619 (→ OEH-91815); closure verify missed the import stage
- `11-11 03:21` · [OEH-91815](https://warbyparker.atlassian.net/browse/OEH-91815) · IN-I-2019 (import stage) · FEDEX_AI import failed 511/3619 sequences for the 11-11 count (load 132516630 / import 132516640) → C2 · **Rejected** 11-13 (comment 985309 → tracked in OEH-92944)
- `11-12 03:19` · [OEH-92338](https://warbyparker.atlassian.net/browse/OEH-92338) · IN-I-2019 · serialized qty 724 vs **19** serials, item 846864072902 in Replen → C1 (5th intake failure, far worse ratio) · **Rejected** 11-13 (comment 985310 → tracked in OEH-92944)
- `11-12 10:03` · [OEH-92508](https://warbyparker.atlassian.net/browse/OEH-92508) · IN-I-2019 · same-day re-upload 400s on the count-name collision (`3FED Snapshot 2026-11-12 already exists`) → C1 anti-pattern confirmed live · **Rejected** 11-13 (comment 985311 → tracked in OEH-92944)
- `11-13 03:12` · [OEH-92944](https://warbyparker.atlassian.net/browse/OEH-92944) · IN-I-2019 (import stage) · FEDEX_AI import failed 1024/1624 sequences for the 11-13 count (load 132752756 / import 132752768) → C2 · root cause found (zero-fill duplicates CLEN serials) · **Triage** 11-13 — the tracker ticket: fix list attached (attachment 370057, 513 serials), tracking comment 985312 (Alexis mentioned)

## Resolution clusters

### C1 — IN-I-2019 — serialized qty vs serial count mismatch (blank serials)

- **Tickets**: [OEH-91409](https://warbyparker.atlassian.net/browse/OEH-91409) (Rejected 11-11) · [OEH-92338](https://warbyparker.atlassian.net/browse/OEH-92338) (Rejected 11-13) · [OEH-92508](https://warbyparker.atlassian.net/browse/OEH-92508) (Rejected 11-13 — same-day re-upload collision) — 3 this rotation; same family as OEH-89046/89097/89352 from the October rotation
- **Signature**: `Serialized line quantity (N) does not match serial count (M) for item <upc> in subinventory Replen` on the SFTP route; the merged (item, subinventory) group has rows with a blank Serial Number
- **Playbook**: `on-call-agent/skills/in-i-2019-serial-mismatch` (new this rotation; `verify_day.py` gives the day-0/day-1 verdict — but see C2: a created count is not proof of a clean import)
- **Outcome**: park day 0 → the next daily full snapshot recreates the AI count → verify the import too → Reject. OEH-92508 confirms the same-day re-upload 400s on the count-name collision, live. Six intake failures in under three weeks (10-27, 10-28, 11-03, 11-10, 11-12 ×2)

### C2 — IN-I-2019 — FEDEX_AI import-stage rejections (new, 11-13)

- **Tickets**: [OEH-91815](https://warbyparker.atlassian.net/browse/OEH-91815) (511/3619 failed on the 11-11 count — Rejected 11-13) · [OEH-92944](https://warbyparker.atlassian.net/browse/OEH-92944) (1024/1624 failed on the 11-13 count — Triage, the tracker)
- **Signature**: summary `verify_cycle_count_import` — does NOT contain "IN-I-2019"; body says `error details found for N out of the M cycle count sequences` for 3FED / FEDEX_AI, with load/import ESS ids and a UCM log link (dID). M = the day's AI count entry count
- **Root cause** (11-13): our zero-fill dedupes per (UPC, subinventory) only, so the 511 serials FedEx tags CLEN (file → Cleaning, qty 1) while Oracle holds them in Replen also get a zero-fill Replen line at qty 0 → the serial enters the count twice → `INV_COUNT_CCEOI_INVALID_SERIAL`. The 1024 = 511×2 in-count pairs + 2 cross-day duplicates (already counted in the 11-11 count). All 14 items serial-controlled; item setup ruled out. Full report: monocle `tmp/in_i_2019_ess_import_rootcause.md`; fix list: OEH-92944 attachment 370057 (513 serials with item, UPC, both locations)
- **Outcome**: fix the zero-fill to skip serials the file lists under a different subinventory, and reconcile with FedEx why CLEN-tagged units sit in Replen — recurs on every successful count until addressed (tracking comment 985312). Stacks with C1: on days the intake succeeds, the import can still reject entries

## Knowledge delta

- New skill: `in-i-2019-serial-mismatch` (adversarial-reviewed, verified live on OEH-91409). Sibling `in-i-2019-snapshot-cleanup` rerouted: clean-and-reupload is no longer the default since OTCM-151489.
- Erratum 11-13: the skill's day-1 "no new IN-I-2019 ticket" JQL misses `verify_cycle_count_import` tickets — OEH-91815 existed 7.5h before OEH-91409 was Rejected. Fixed in the skill: day-1 verify now requires the import-callback check too (count created ≠ entries imported).
- OEH-92508 live-confirms the same-day re-upload count-name collision anti-pattern.
- Escalation routed out: recurring FedEx blank-serial defect (10-27, 10-28, 11-03, 11-10, 11-12) raised to Alexis Tomacruz on OEH-91409 — answer pending; 11-13 update: the import stage also rejects entries, so the pattern is worse than the intake question alone.
- Consolidation 11-13: OEH-91815/92338/92508 **Rejected** with pointer comments; OEH-92944 → Triage as the single tracker for the cascade, with the 513-serial fix CSV attached and Alexis mentioned on the tracking comment 985312.

## Open tickets

(One: [OEH-92944](https://warbyparker.atlassian.net/browse/OEH-92944), in Triage — the tracker for the whole IN-I-2019 cascade. Waiting on: the zero-fill fix work (ticket TBD), the FedEx CLEN-vs-Replen reconciliation, and Alexis's answer on the recurring pattern.)

## Handoff
