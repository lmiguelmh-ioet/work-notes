# OTCM-139198 — IN-I-2019L: Retire IN-I-2019L / FEDEX_LEGACY
- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-139198
- **RICE**: IN-I-2019L (related: IN-I-2019)
- **Repos**: monocle_integrations
- **Status**: all 3 PRs ready for review; PRs 2 and 3 merge-gated (as of 2026-10-12)
- **Plan**: [projects.IN-I-2019L.OTCM-139198.plan](projects.IN-I-2019L.OTCM-139198.plan.md)

## Outcome
- IN-I-2019L cycle-count callbacks fail with a controlled HTTP 400 instead of an unhandled 500.
- The rejection ships enabled: `retire-in-i-2019l` is true in dev, stage, prod, and ott.
- The legacy `FEDEX_LEGACY` mapping stays until PR 2 deletes it after a 30-day zero-callback window.
- After PR 2 merges, PR 3 removes the retirement mechanism and the dead `ProviderRICEId` enum. The factory's generic unknown-id error becomes the permanent tombstone.

## What shipped
- [PR #2700](https://github.com/WarbyParker/monocle_integrations/pull/2700) — flag, gate, 400 handler, lifecycle logs. Open, `enhancement` label.
- [PR #2704](https://github.com/WarbyParker/monocle_integrations/pull/2704) — deletes the FEDEX_LEGACY enum members, factory entry, and legacy tests. Ready for review, stacked on #2700, `enhancement` label.
- [PR #2705](https://github.com/WarbyParker/monocle_integrations/pull/2705) — removes the retire-in-i-2019l flag machinery and the unused ProviderRICEId enum. Ready for review, stacked on #2704, `enhancement` label.

## Decisions
### Functional clarifications (Q&A)
1. Retired-id callback maps to a controlled 400, not the ticketed 500 → approved (user, plan approval in Cursor chat).
2. Flag starts true in every environment, not false → approved (user, Cursor chat 2026-10-12; zero-traffic evidence in Jira comment 957876).
3. PR 2 merges only after deploy plus 30 days of zero IN-I-2019L callbacks → approved (user, plan approval in Cursor chat).
4. OTCM-139197's `when_off` cleanup must not absorb `retire-in-i-2019l` → exclusion comment to post (user, plan approval in Cursor chat).
5. PR 2 opened as a draft PR so the merge gate is mechanical, not prose → approved (user, Cursor chat 2026-10-12; pre-opening review recommendation).
6. Endgame: PR 3 removes the flag machinery and the dead `ProviderRICEId` enum after PR 2 merges → approved (user, Cursor chat 2026-10-12).
7. PR 3 ships as a direct implementation (no best-of-2) and opens as a draft stacked on #2704 → approved (user, Cursor chat 2026-10-12).

### Design decisions (ours)
1. `RetiredRiceIdError` subclasses `CycleCountCallbackError`; an undecorated `BadRequestExceptionHandler` returns 400. Expected rejections must not open Jira tickets.
2. The retired id stays a literal constant in the gate. PR 2 deletes the enum member, and the gate must outlive it.
3. The RICE-id equality check short-circuits before the flag await. The ~15 active integrations never query the flag service.
4. Start and rejection log lines keep the retired id measurable in CloudWatch during the PR 2 window.
5. The API test module defaults the flag off with an autouse fixture. The API conftest reads the real env ymls, which now carry `true`.
6. PR 2 accepts the flag-off fallback to the factory's unknown-id error (500 + error ticket). The flag is true in every environment, so the path stays unreachable.
7. The `ProviderRICEId` deletion waits for PR 3. The enum was already dead, and the ticket names only its `FEDEX_LEGACY` member.

## Evidence
- Zero IN-I-2019L matches across all three prod Lambdas over 30 days (CloudWatch). Jira comment 957876 on OTCM-139198.

## Test data
- None. The gate is flag-driven; existing API fixtures post IN-I-2019L payloads.

## Open items
- PR 2 (#2704): ready for review. Merges only after #2700 deploys to prod plus 30 days of zero IN-I-2019L callbacks.
- PR 3 (#2705): ready for review. Merges after PR 2 merges.
- OTCM-139197 exclusion comment. To draft; folds in the PR 3 endgame note.

## Artifacts
- Plan archive: [projects.IN-I-2019L.OTCM-139198.plan](projects.IN-I-2019L.OTCM-139198.plan.md)
- Skills updated this ticket: `pr-best-of-n` (slow suites run only pre-push), `pr-workflow` (description rules: no process content, STE prose).
