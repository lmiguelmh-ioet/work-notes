# OMG-3162 — omg-ui: Add a stage shipment table with a fake-delivery modal

- **Ticket**: https://warbyparker.atlassian.net/browse/OMG-3162
- **RICE**: — (OMG platform work, no RICE id)
- **Repos**: `omg-ui` (the PR); `order-management-gateway` holds the contract (OMG-3160 read, OMG-3161 carrier-events)
- **Status** (2026-10-29): **DONE** — QA moved the ticket to Done 2026-10-28 16:45 local (as [OTCM-151727](https://warbyparker.atlassian.net/browse/OTCM-151727), resolution Done; verified in Jira 2026-10-29). File frozen. Everything shipped and live on stage: the tool (#337 + #346, `v0.2.102`) and the QA-feedback round (#357, `v0.2.114`). Prod keeps `shipmentsTool` off. Surviving follow-ups under Open items.
- **Plan**: [projects.OMG-3162.plan](projects.OMG-3162.plan.md) (archived verbatim 2026-10-29)

## Outcome

- QA gets a Tools → Shipments page to find a stage shipment by number and drive it to delivered, without touching Oracle or monocle directly.
- The `shipmentsTool` flag is on in dev and, as of #346's merge, on stage; off in prod. OMG-3160's read is live on stage and its wire shape matches the client.

## What shipped

- omg-ui [PR #337](https://github.com/WarbyParker/omg-ui/pull/337) — **MERGED** 2026-10-27 (5 commits, 41 files, +1650/−166). Shipments table page, fake-delivery modal, shared carrier-events client + UI, `shipmentsTool` flag with nav gating. Branch `feat/OMG-3162-shipments-tool`.
- Commits: `6144d9a` (the tool), `bfe0af4` (Bugbot fix: WMS result on a light card), `e8d44c1` (UX refinement + Preview-only mode + close gate, driven by two independent UX/FE review rounds), `96e83a5` (Sniffany review fixes: shared `filterNavigation` traversal, dev-forced preview, timeline blur sort, plus 5 light-panel hardening fixes), `f5b8f83` (OMG-3160 contract correction: four shipment header fields widened to `string | null`).
- omg-ui [PR #346](https://github.com/WarbyParker/omg-ui/pull/346) — **MERGED** 2026-10-27 16:13 (2 commits, 5 files, +48/−23; Bugbot post-push scan: low risk, no findings). `1e94def`: `stage.shipmentsTool: true`; blur re-sort deleted in favor of the existing submit-time sort; Remove-button mousedown guard deleted with it. `ec63d07`: Add appends instead of re-sorting the timeline (Sniffany thread [r4394030090](https://github.com/WarbyParker/omg-ui/pull/346#discussion_r4394030090), answered [r4394106104](https://github.com/WarbyParker/omg-ui/pull/346#discussion_r4394106104)). Branch `feat/OMG-3162-enable-shipments-stage`.
- omg-ui [PR #357](https://github.com/WarbyParker/omg-ui/pull/357) — **MERGED** 2026-10-28 17:46 UTC (squash `e26474fe`), deployed via tag `v0.2.114` (cut 12:47 local on the merge commit; tag CD). 2 commits, 4 files, +174/−15; `enhancement`. QA feedback round: all 8 data columns sortable, the button column labeled "Actions". `b15f001`: the two asks. `8a836a3`: light-panel fixes — line-column keys carry the dotted path (the key→path map deleted), per-column sort tests, QA note on the inert-on-stage line columns. Branch `feat/OMG-3162-sortable-shipment-columns`.

## Decisions

### Functional clarifications (Q&A)

1. The submit side needs no new endpoint: an OMG-fulfilled shipment's number doubles as the FR external id that the merged OMG-3161 route keys on (`POST /v1/test/fulfillment-requests/{externalId}/carrier-events`, omg PR #2876).

### Design decisions (ours)

1. Gate with a `shipmentsTool` feature flag (FeatureFlagRoute + nav filter), not env checks — the repo's per-environment gating pattern; stage re-enable becomes a one-line config flip.
2. Stage flag stays `false` until OMG-3160 deploys: the read endpoint 404s today, so a live nav entry would hand QA a broken page.
3. Shared modules instead of duplication: `api/carrierEvents` client (moved out of wms-test), `components/carrierEvents` presets + result cards, `utils/dates.ts` `toDateTimeLocal` (three hand-rolled copies eliminated).
4. The Dialog X accessible name is "Dismiss", not "Close" — "Close" collided with footer Close buttons in getByRole/getByLabelText queries.
5. The client targets the OMG-3160 ticket text (8 fields + optional `trackingNumber`); the top-level envelope is assumed to be a bare array — the one point not verifiable until the backend deploys.
6. The modal locks fully while a send is in flight, closing included: a failure landing after an unmount would vanish silently (FE reviewer finding; replaced the deliberate "Close stays live" behavior and its test).
7. The modal uses a fixed frame (fixed header and footer, `min-h-0 flex-1 overflow-y-auto` middle) instead of a root-scrolling dialog with a sticky footer, after content kept bleeding past the footer and the scrollbar over the rounded border. Per-instance className overrides only; the shared `DialogContent` is untouched.
8. A Preview-only submit posts `dryRun: true` and keeps the timeline (no clear, no table refresh): nothing was sent, so there is nothing to reset.
9. Real sends are gated on `wmsCarrierEvents`, the same flag the WMS Test page uses: where it is off (dev), the modal forces Preview checked+disabled and always posts `dryRun: true`, since dev OMG cannot reach monocle (Sniffany finding).
10. Timeline date edits re-sort on blur, not per keystroke — per-keystroke sorting would move the row while the editor tabs through datetime segments. Remove buttons `preventDefault` their mousedown so a blur re-sort cannot shift a row under the cursor and retarget the click.
11. Test files that stub the feature-flag provider restore the JSON-backed provider in `afterEach` (the repo idiom, three precedents); vitest's per-file isolation makes leaks impossible today, but the restore keeps any future shared-worker run order-independent.
12. Miguel's OMG-3160 contract correction (2026-10-27, Slack): `initialShipDate`, `shipFromOrganization`, `customer`, `shipToLocation` come back null for a shipment with no lines. Types widened to `string | null`; the table's existing `"-"` fallback renders them. This supersedes the OMG-3160 field table, which shows all four as always-present strings.
13. Submit-time-only sort replaced the blur re-sort (Sniffany's deferred Low on #337): the blur re-sort moved the focused row's DOM node and dropped keyboard focus to `<body>`. Submit already sorted before sending; the caption now reads "Sent earliest first when you submit." and the Remove-button mousedown guard, which existed only to protect the blur sort, went with it.
14. The OMG-3160 envelope is a bare array — verified live on stage 2026-10-27 (decision 5's one unverified point). The client's assumption held; no UI change was needed.
15. Sorting reuses the house idiom (`sortByKey`/`nextSortState` from `@utils`, DataTable's `sortable` + controlled sort props). The stacked line columns sort by the shipment's first line only, and the column key carries the dotted path (`lines.0.orderNumber`) — both the sort helper and DataTable traverse dots, so a key→path map would store the same fact twice (panel finding).

## Evidence

- Local gates pre-push (2026-10-26, updated for `e8d44c1`): full unit suite 4470/4470 (390 files), production build green, eslint 0 errors, typecheck clean.
- Local gates pre-push (2026-10-27, `96e83a5`): full unit suite 4473/4473 (390 files), production build green, eslint 0 errors, typecheck clean. Scoped suites ran 3 consecutive clean passes after the flake-hardening fix.
- Reviews: 12-seat full panel (17 findings applied, `_14`/`_19` skipped) plus a 3-seat light panel on the fix round (all findings applied). Two independent UX-expert/senior-FE rounds on the modal (spacing/labels, big-result overflow) — all applied findings listed in the chat; live-verified by the user against the local stub.
- Reviews (2026-10-27, human round): Sniffany left 4 threads (1 Medium, 3 Low); all verified true, fixed in `96e83a5`, and answered on the PR. A 4-seat light panel (Code ×2, Requirements ×2) then reviewed the fix delta: 4× SHIP-WITH-NITS, 5 findings applied (flag-restore idiom, `previewRequested` rename, Remove-button mousedown guard, test hardening, hoisted `byEventDate`), 3 consciously skipped (Sidebar two-pass composition, wrapper-test restructure, NaN cosmetic order). Requirements seat revert-tested each new test and proved it pins its fix.
- Stage verification (2026-10-27): OMG-3160 live behind CF Access (cloudflared token, the omg-ui `get-cf-token.sh` pattern). The bare list returns exactly 50 shipments; `?shipmentNumber=L0ZHA78DBK` returns one fully populated row (LLAS, tracking `SIML0ZHA78DBK`, 2 lines on `TQ0YJK009Z`). `customer` and `trackingNumber` are null on 49/50, key always present. Saved in `assets/OMG-3162/omg3160_verify/`.
- Local gates pre-push (2026-10-27, `1e94def`): full unit suite 4565/4565 (392 files), production build green, eslint 0 errors, typecheck clean.
- Reviews (2026-10-27, #346): 4-seat light panel, 3× SHIP-WITH-NITS + 1× SHIP; 6 findings applied (triage in `assets/OMG-3162/stage_enable_review_triage.md`), 1 follow-up logged (Remove-click focus), 1 skipped.
- Comment round (2026-10-27, #346): Sniffany's Low — Add still re-sorted the whole timeline — verified true and fixed in `ec63d07` (append; new test pins full row preservation). A 4-seat light panel reviewed the fix diff (1× SHIP, 3× SHIP-WITH-NITS; triage in `assets/OMG-3162/pr346_comment_fix_triage.md`): one unanimous finding applied, one skipped, one already tracked. Gates 4566/4566, build green; reply posted (r4394106104).
- Local gates pre-push (2026-10-28, #357, `8a836a3`): full unit suite 4771/4771 (402 files), production build green, eslint 0 errors, typecheck clean.
- Reviews (2026-10-28, #357): 4-seat light panel (Code ×2, Requirements ×2) + 2 triage seats; no blockers. All three gray findings implemented per user call (dotted keys, 8-column `it.each` + numeric-collation + multi-line pins, QA handoff note in the PR body). Triage record: `assets/OMG-3162/triage_plan.yaml`.

## Test data

- No Oracle fixtures needed — unit tests use in-memory fixtures; the tool itself creates the QA data once live.

## Open items

Ticket closed by QA 2026-10-28; these follow-ups survive closure.

- ~~Stage visibility waits on the next omg-ui tag deploy~~ **DONE 2026-10-27**: `v0.2.102` deployed to stage 16:40 (tag CD `frontend-push-stage`); the live bundle verified to carry the flag flip and the new caption. Tools → Shipments is visible on stage.
- **v0.2.102 prod gate** (manual approval, parked): prod keeps `shipmentsTool` off, so approving is low-risk for this ticket, but approve in tag order with Emma's queued `v0.2.101` or prod rolls back to the older bundle. Emma's `#345` merged to main after the tag and rides the NEXT release.
- **`nowForInput` nit** (the one leftover from the #337 follow-up; the blur focus-drop fix shipped in #346): inline the one-line wrapper in `src/pages/wms-test/CarrierEventsPanel.tsx`.
- **Remove-click focus follow-up** (found by the #346 panel): a mouse user who edits a date and then clicks another row's Remove drops focus to `<body>` — the deleted mousedown guard had a second effect. Keyboard path unaffected; the fix is focus management on removal (focus the list via a `<ul>` ref). User veto still possible.
- Ask Miguel to update OMG-3160's field table to mark the four nullable fields, so the ticket text catches up with his finding.
- Post the OMG-3162 contract-correction comment to Gabriel/Miguel: the ticket text says `/v1/test/shipments/{n}/carrier-events`; the merged OMG-3161 route is `POST /v1/test/fulfillment-requests/{externalId}/carrier-events`.
- Optionally share the OMG-3160 stage-verification evidence as a Jira comment for Miguel/QA (user undecided).
- Monocle tracker-guard defect (`_belongs_to_another_tracker` can silently drop simulated events after tracker sync) — OTCM ticket not yet filed (user undecided).
- Panel findings `_14` and `_19` consciously skipped.

## Artifacts

- PRs: [#337](https://github.com/WarbyParker/omg-ui/pull/337) (merged), [#346](https://github.com/WarbyParker/omg-ui/pull/346) (merged), [#357](https://github.com/WarbyParker/omg-ui/pull/357) (merged, deployed `v0.2.114`)
- Review triage record: `assets/OMG-3162/triage_plan.yaml`
- Related tickets: [OMG-3160](https://warbyparker.atlassian.net/browse/OMG-3160) (shipments read, In Review — deployed to stage), [OMG-3161](https://warbyparker.atlassian.net/browse/OMG-3161) (carrier-events route, merged)
- PR description scratch: deleted; the final texts live on the PRs
- Stage verification evidence: `assets/OMG-3162/omg3160_verify/`
