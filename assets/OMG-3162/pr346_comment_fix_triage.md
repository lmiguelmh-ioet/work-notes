# Light panel triage — PR #346 comment-fix diff (append-on-Add)

Run id: 20261027T1557 · Light tier (Code ×2, Requirements ×2) · 2026-10-27
Diff reviewed: uncommitted Sniffany-thread fix (`addCustomEvent` appends; new
timeline-order test). Verdicts: 1× SHIP, 3× SHIP-WITH-NITS. All four seats
verified: no code path relied on add-time sorting, the submit sort is the only
`.sort` left in the modal, and re-adding the sort fails the new test.

| Cluster | Finding | Seats | Disposition |
|---|---|---|---|
| 20261027T1557_1 | New test under-asserts row preservation: `.at(-1)` pins only the last row; a replace-instead-of-append regression would slip past this test (caught elsewhere by the submit test) | all 4 | **Applied** — captures `presetDates` before Add and asserts the full array `toEqual([...presetDates, "2020-01-01T00:00"])` |
| 20261027T1557_2 | Optional focus-symmetry assertion (Add button keeps focus); non-discriminating today — the button lives outside the keyed list, so append cannot move it | code_2 | **Skipped** — asserted invariant is safe by construction; test would pin nothing that can break |
| 20261027T1557_3 | Ticket text says `/v1/test/shipments/{n}/carrier-events` but the client posts `/v1/test/fulfillment-requests/{id}/carrier-events` | requirements_2 | **Follow-up already tracked** — pre-existing merged code (#337); the contract-correction comment to Gabriel/Miguel is an open item in `notes/projects.OMG-3162.md` |

Fast gates after the applied fix: 15/15 in the modal file, eslint/prettier/tsc
clean.
