# Pre-opening review triage — feat/OMG-3162-enable-shipments-stage

Light tier, 4 seats (Code x2, Requirements x2), run 20261027T1544. Verdicts: 3x SHIP-WITH-NITS, 1x SHIP.
Reports lived in /tmp/omg3162_stage_review/ (scratch, deleted after consolidation).

## Applied (auto-fix)

- 20261027T1544_1 — Stale doc comment on `SHIPMENTS_TOOL` (featureFlags.ts:20; code_2 SHOULD-FIX + requirements_1 NIT). Replaced with the sibling-style "Stage and dev only: ... absent in production."
- 20261027T1544_2 — Submit-time sort had no test that could fail (code_1 SHOULD-FIX, mutation-proven). Added "sorts the events on submit when an edited date changed the send order": types 2999 into event 1, submits, asserts the posted order is in_transit, delivery, pre_transit.
- 20261027T1544_3 — Focus test never pinned its date-edit precondition (code_2 SHOULD-FIX). Added `expect(firstDate).toHaveValue("2999-01-01T00:00")` after typing, in both timeline tests.
- 20261027T1544_4 — Flag test name omitted the production-never half (code_2 NIT). Renamed to "enables the shipments tool in development and on stage, never in production".
- 20261027T1544_5 — Caption assertion was topical drift inside the focus test (code_2 NIT). Moved it to the new submit test, where it belongs.
- 20261027T1544_6 — `addCustomEvent` comment overstated ("reads as the send order") (code_2 NIT). Now "a fresh list matches the send order".

## Follow-up (recorded, not in this PR)

- 20261027T1544_7 — Mouse user editing row B who clicks row A's Remove now drops focus to <body> (the deleted mousedown guard also suppressed the focus shift; code_1 NIT). Keyboard users unaffected; restoring the guard is the wrong fix. Proper fix: manage focus on removal (focus the Remove button at min(removedIndex, length-1) via a ref on the list). Logged in notes/projects.OMG-3162.md open items.

## Skipped (with reason)

- 20261027T1544_8 — Optional comment naming the jsdom revert-failure signature (requirements_2 NIT, marked optional). Skipped: maintainer-facing trivia about old-code behavior; the test name and comment already state intent.

## Verified clean by the seats (no action)

- No stale references to `sortTimeline`; `byEventDate` still used (add + submit).
- Flag blast radius: exactly two consumers (Sidebar entry, FeatureFlagRoute); production/default untouched; no config snapshots.
- Caption is strictly true in every state (submit always sorts; invalid dates disable submit).
- Revert potency executed in a scratch worktree: all three focus-test assertions fail against the pre-PR code.
- Flag AC wiring: hostname-based env detection gates stage/prod correctly.
