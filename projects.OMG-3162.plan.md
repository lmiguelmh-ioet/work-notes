# OMG-3162 — Stage shipment table with a fake-delivery modal

Ticket: https://warbyparker.atlassian.net/browse/OMG-3162
Repo: `WarbyParker/omg-ui` (local: `~/projects/ioet/omg-ui`), branch per PR off `main`.
Audience: the Scorpio UI agent / QA on stage. The page calls OMG only — never Oracle or
monocle directly.

## Settled contract (from discovery + independent verification)

The page uses two OMG endpoints:

1. **Table read** — `GET /v1/test/shipments[?shipmentNumber=]` per OMG-3160. **Not built
   yet** (Miguel Munoz owns OMG-3160, status Created, no PR). Documented response item:
   `shipmentNumber`, `initialShipDate`, `shipFromOrganization`, `customer`,
   `shipToLocation`, `trackingNumber?`, `lines[]{orderNumber, orderType, lineStatus}`;
   max 50 items. We build against this contract; stage verification waits for Miguel's
   deploy.
2. **Fake deliver** — `POST /v1/test/fulfillment-requests/{externalId}/carrier-events`
   (OMG-3161, merged in PR #2876), called with `externalId` = the row's `shipmentNumber`.
   **Not** the shipments-keyed URL the ticket names — that URL was never built. Verified
   identity: OMG names the Manhattan shipment with the FR external id at dispatch
   (`adapters/src/wms/manhattan/mapper.py:179,221`), and the WMS-I-1006 ship confirm
   creates the Oracle shipment under that same number
   (`monocle _ship_confirm_sales_orders.py:421,205`). Request:
   `{containerId?, estimatedDeliveryDate?, events[] (min 1), dryRun?}`; response:
   `{orderId, fulfillmentRequestExternalId, target, dryRun, sent[]{shipmentId,
trackingNumber, containerId, payload, monocleResponse}}`; errors: 404 unknown or
   superseded id, 409 no shipped box with a tracking number yet, 422 naive dates/empty
   events, 502 monocle failure with partial-progress detail.

Known caveats:

- The identity covers shipments dispatched from an OMG FR (Manhattan and Flare/FedEx
  paths alike — see the review note below). Rows for Helios/SF-fulfilled shipments
  will 404 on submit; the page shows the returned error (AC) and a short hint in the
  modal that fake delivery works for OMG-fulfilled shipments only.
- **Open defect (not ours to fix in this plan):** monocle's tracker-id guard
  (`_belongs_to_another_tracker`, OTCM-145863, merged 2026-10-21) silently drops
  simulated events once tracker sync has stamped the reference (`trk_<uuid>` ≠
  `trk_omg_sim_<shipmentId>`). Fake delivery on stage works only between ship confirm and
  the next tracker-sync run until that is fixed. Affects OMG-3418 too. See Q4.
- Ticket paths `frontend/src/...` are the retired monorepo layout; the real layout is
  `src/...` (omg-ui).

## Requirements (ticket acceptance criteria)

- AC1: opening the page lists up to 50 shipments in the ticket's columns.
- AC2: searching by shipment number replaces the table with that result.
- AC3: Fake deliver opens the modal; the Delivery preset submits the three-event preset.
- AC4: the page never calls Oracle or monocle directly (OMG only).
- AC5: the Tools entry is not shown on a production build (and the API routes exist only
  for `ENV` local/stage — backend concern, Miguel's ticket).

Modal contents (ticket): estimated delivery date+time; preset buttons Pre-Transit /
Acceptance / Delivery; custom event (status `pre_transit` | `in_transit` | `delivery` +
datetime + Add); timeline of events, each removable; Submit; show success or error and
leave the modal open on failure. Presets: Pre-Transit = one `pre_transit` at now;
Acceptance = + `in_transit` one minute later; Delivery = + `delivery` one minute after.

Table columns (ticket, from the Edit Shipment screen): Shipment, Initial Ship Date,
Ship-from Organization, Customer, Ship-to Location, Order, Order Type, Line Status, and
an action column. One row per shipment; multi-line shipments stack each line's
order/orderType/lineStatus in the row.

## Design decisions

- **Page home:** `src/pages/tools/shipments/` (`Shipments.tsx` + columns/helpers +
  tests), exported from `src/pages/tools/index.ts` — matches the other Tools pages
  (`lineLookup`, `items`). Standard light Tools-page styling per the `ItemsList.tsx`
  pattern: `PageHeader` from `@components/PageHeader` (NOT `@ui` — independent-review
  correction), `Card`, `TextInput`, `Button`, `DataTable`, `ColumnDefinition` from
  `@ui`, `ApiError` from `@components/common/apiError/ApiError`; NOT the wms-test
  dark theme.
- **Route:** `TOOLS_SHIPMENTS: "/tools/shipments"` in `src/routes/paths.ts`; registered
  in `src/routes/appRoutes.tsx` behind `FeatureFlagRoute` (`off={<NotFoundError />}`) —
  the PR #295 pattern.
- **Feature flag:** new `shipmentsTool` in `src/config/featureFlags.json`
  (default false; development true; stage true; production false) +
  `FEATURE_FLAGS.SHIPMENTS_TOOL` in `src/utils/featureFlags.ts`. Off in production ⇒
  AC5. The Sidebar Tools entry is rendered only when the flag is on: compute
  `useFeatureFlag(FEATURE_FLAGS.SHIPMENTS_TOOL)` inside `Sidebar()` and filter the item
  in the existing `visibleSections` memo (keeps `navigationSections` static for its other
  consumers). Note: the route gating is the PR #295 pattern, but the Sidebar filter is
  NEW — wms-test never had a Sidebar entry, so there is no precedent; expect the
  existing Sidebar tests to need updates (independent-review note).
- **Shared carrier-events module:** move `src/pages/wms-test/carrierEvents.ts` →
  `src/api/carrierEvents/carrierEvents.ts` (new `index.ts` re-export; wms-test imports
  updated — both import sites, including `CarrierEventsPanel.test.tsx`). It already
  carries the Helios presets, `buildCarrierEvents`, `carrierEventsPath`, and the
  response types the modal needs. No behavior change; wms-test keeps working
  (regression surface, QA-S7).
- **Shipments API client:** new `src/api/shipments/` — `types.ts` (`TestShipment`,
  `TestShipmentLine`, `CarrierEventsRequest`), `shipments.ts`
  (`fetchTestShipments(shipmentNumber?)` → `GET /v1/test/shipments`;
  `postCarrierEvents(externalId, body)` → the merged route), `index.ts`. `apiFetch`
  only, never raw `fetch`. The table fetches with TanStack `useQuery`
  (`queryKey: ["test-shipments", shipmentNumber ?? ""]`), mirroring existing list pages.
- **Table:** `DataTable` with `ColumnDefinition<TestShipment>` and
  `showPagination={false}` (server caps at 50 rows; no client paging). The three line
  columns render stacked per-line values; the action column renders the per-row
  "Fake deliver" `Button`. Loading → `loading` prop skeleton. Error → `ApiError`
  inside a `Card` with a Retry button calling `query.refetch()` (the
  `ItemsList.tsx:133-148` pattern — `DataTable` has NO `errorNotice` prop;
  independent-review correction). Empty → an explicit empty-state `Card` (DataTable
  has no built-in empty state), including the search-returned-nothing case. A caption
  notes "showing up to 50 shipments".
- **Modal:** `FakeDeliveryModal.tsx` on the `@ui` Dialog primitives (radix). State: list
  of events `{status, date}`, estimated delivery datetime, sending/result/error.
  Preset buttons replace the timeline from a base time (default now, editable — the
  Helios "now" semantics); custom Add appends; each timeline row has a remove button.
  Submit disabled when the timeline is empty. Body:
  `{estimatedDeliveryDate: new Date(value).toISOString(), events}` (both ISO with
  offset — the backend 422s naive datetimes; guard the conversion against an empty
  estimated-delivery input, which throws `RangeError` — omit the field instead).
  On success: render `sent[]` (tracking
  number, container, monocle response, payload in a collapsible) and reset the timeline.
  On failure (`ApiHttpError`): show `error.message`, keep the modal open and the
  timeline intact. Modal copy notes fake delivery works for OMG-fulfilled shipments
  (non-OMG rows 404).
- **Comment language:** omg-ui AGENTS.md — code comments never name tickets/people;
  commit/PR subjects must not lead with verb-or-adjective words (e.g. use "Add", "Fix").

## PR plan

**One PR.** Decision (Luis, 2026-10-26): the ~400-line split limit is a monocle
constraint; omg-ui ships this ticket as a single PR.

| Field          | Value                                                                                                                                                                                                                                    |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Proposed title | `[OMG-3162] feat(shipments): add the stage shipment table with the fake-delivery modal`                                                                                                                                                  |
| Repo / branch  | omg-ui / `feat/OMG-3162-shipments-tool`                                                                                                                                                                                                  |
| Contents       | Everything in "Design decisions": the `carrierEvents.ts` move to `src/api/carrierEvents/`, the new `src/api/shipments/` client, the `shipmentsTool` flag, the Tools page + route + Sidebar entry, the `FakeDeliveryModal`, and all tests |
| Est. lines     | ~1100 with tests — exceeds the ~400 guideline deliberately; exception confirmed by the user                                                                                                                                              |

Sequencing notes:

- The PR merges behind the flag — no dependency on Miguel's OMG-3160 to merge or to
  run unit tests. Only **stage verification** waits on (a) OMG-3160 deployed and
  (b) the monocle tracker-guard fix (Q4).
- omg-ui deploys via tag CD (`frontend-push`); the page reaches stage on the next tag
  after merge — coordinate the verification window with Miguel's deploy.
- The PR touches wms-test imports: regression surface is the WMS Test page (QA-S7).
- Commit messages carry the `[OMG-3162]` key first; subjects follow the repo rule
  (never lead with an ambiguous verb/adjective word).
- Per repo + house gates: fast checks (scoped vitest, `npm run lint`,
  `npm run typecheck`) during iteration; full `npm run test:run` + `npm run build`
  before the push. PR body per repo skill (`.cursor/skills/wp-pr-body`) once the
  description is drafted to `tmp/pr_description.md`.

## Independent plan review (2026-10-26)

One blind generalPurpose seat verified all 8 load-bearing claims against the code
(brief and report: `/tmp/omg3162_plan_review/`, removed after consolidation).
**Verdict: CONVERGES — no blocking findings.** Two factual corrections applied to
this plan: `PageHeader` comes from `@components/PageHeader` (not `@ui`), and
`DataTable` has no `errorNotice` prop (use the `ApiError`-in-`Card` pattern from
`ItemsList.tsx:133-148`). Non-blocking suggestions applied: `showPagination={false}`,
explicit empty state, `RangeError` guard on the estimated-delivery conversion,
`CarrierEventsPanel.test.tsx` included in the module move, Sidebar filter marked as
precedent-free with test updates expected, empty-search QA row added (QA-S12).
Extra finding: the shipment-number identity is broader than first claimed — the
Flare/FedEx confirmation path also names the Oracle shipment with the FR external id
(`_flare_confirmation_builders.py:47-49,86`), so those rows share the contract too.

## QA test scenarios

We are the testers; QA verifies posted evidence. Evidence posted to OMG-3162 per the
`jira-qa-evidence` skill.

Requirement matrix:

| Scenario | Covers     | Setup / run                                                                                                                                                                            | Expected                                                                                                                                      | Evidence                                                        |
| -------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| QA-S1    | AC1        | Stage, after OMG-3160 deploys: open `/tools/shipments`                                                                                                                                 | Up to 50 rows; all 8 columns; multi-line rows stack line values                                                                               | Screenshot + the `GET /v1/test/shipments` JSON                  |
| QA-S2    | AC2        | Same session: search a known shipment number                                                                                                                                           | Table replaced by the single matching row                                                                                                     | Screenshot + request URL with `shipmentNumber`                  |
| QA-S3    | AC3        | Stage, OMG-fulfilled shipped row (after monocle guard fix): Fake deliver → Delivery preset → Submit                                                                                    | Three events sent (`pre_transit`, `in_transit`, `delivery`); `sent[]` per box; monocle writes the delivery date; OMG shipment turns delivered | Response JSON + order detail (delivered) + Oracle shipment view |
| QA-S4    | AC4        | Code/unit level: every call goes through `apiFetch` `/v1/...`                                                                                                                          | No raw `fetch`, no Oracle/monocle hosts                                                                                                       | PR diff + unit tests                                            |
| QA-S5    | AC5        | Production build/config: `shipmentsTool` false in production; prod deploy check                                                                                                        | No Sidebar entry; `/tools/shipments` renders NotFound                                                                                         | Config diff + prod screenshot                                   |
| QA-S6    | Modal spec | Unit: presets replace the timeline one minute apart; custom Add appends; remove drops; empty timeline disables Submit; failure keeps modal open with the error; success shows `sent[]` | As spec'd                                                                                                                                     | vitest output in PR                                             |

Design-derived edge cases (second group):

| Scenario | Covers                                         | Run                                                                               | Expected                                             |
| -------- | ---------------------------------------------- | --------------------------------------------------------------------------------- | ---------------------------------------------------- |
| QA-S7    | Regression: carrierEvents move                 | Existing wms-test vitest files + stage smoke of the WMS Test carrier-events panel | WMS Test page unchanged                              |
| QA-S8    | Non-OMG-fulfilled row submit                   | Stage (or unit with 404)                                                          | Error shown, modal stays open, timeline intact       |
| QA-S9    | Ship confirm not yet consumed                  | Stage timing window (or unit with 409)                                            | 409 text shown ("run the ship confirm first")        |
| QA-S10   | `estimatedDeliveryDate` + naive-datetime guard | Unit: body sent with ISO offset datetimes                                         | Backend accepts (no 422)                             |
| QA-S11   | Tracker-guard window                           | Stage after guard fix: fake deliver AFTER tracker sync has run                    | Delivery still lands (the defect's regression check) |
| QA-S12   | Empty search                                   | Unit + stage: search a shipment number that does not exist                        | Explicit empty state, no error                       |

## QA / functional back-and-forth (post-implementation)

_Append one dated entry per exchange: the verbatim ask (who, where), what was run and
its exact scope, the finding (pod evidence), the reply posted (verbatim), the open ask._

_(no entries yet)_

## Questions — exact texts and response history

### Open

#### Q4 — monocle tracker-guard defect: where does the fix ticket live?

- **Context:** the guard added by OTCM-145863 (merged 2026-10-21) silently drops the
  simulator's events once tracker sync has stamped the tracking reference
  (`vendor_tracker_id = trk_<uuid>` ≠ the simulator's `trk_omg_sim_<shipmentId>`).
  Fake delivery on stage works only between ship confirm and the next tracker-sync
  run. Affects the shipped OMG-3418 as well. Verified in monocle
  (`_update_delivery_date_step.py:208-216,262-267`; `_mock_payloads.py:88`;
  `_config/stage.yml:49`).
- **Exact wording as presented (2026-10-26, chat):** "Monocle defect: file our own OTCM
  ticket for the tracker-guard fix (recommended — it's our repo and it blocks QA
  verification of both UI features), or just report it via the OMG-3162 comment and let
  Gabriel route it?"
- **Where to ask / posted:** asked in chat, awaiting Luis. Fix-direction note for the
  ticket: let `trk_omg_sim_`-prefixed events match references outside prod (an empty
  tracker id won't work — the publish path to OMG requires it).
- **Response log:**
  - 2026-10-26 — asked; user moved to planning without answering. OPEN.

### Answered

#### Q1 — Scope: do we build the backend list endpoint too, or only the omg-ui page?

- **Context:** `GET /v1/test/shipments` (OMG-3160) did not exist — no PR, status
  Created. Without it the page can't load data and AC1/AC2 can't be verified
  end-to-end.
- **Exact wording as presented (2026-10-26, chat):** "(a) We implement OMG-3160 first
  (backend PR), then this page — recommended if it's ours to take; (b) someone else owns
  OMG-3160 — we build the page against its documented contract and merge behind the
  flag, verifying on stage once it lands; (c) build the page with mocked data only."
- **Where to ask / posted:** asked in chat.
- **Response log:**
  - 2026-10-26 — Luis: "this will be a new endpoint in OMG, Miguel is working on this
    OMG-3160". RESOLVED (option b): Miguel Munoz owns OMG-3160; we build only the page,
    against his documented contract; stage verification waits for his deploy.

#### Q2 — Fake-delivery contract: shipment-keyed (ticket) vs FR-keyed (merged backend)?

- **Context:** the ticket names `POST /v1/test/shipments/{shipmentNumber}/carrier-events`;
  OMG-3161 merged as `POST /v1/test/fulfillment-requests/{externalId}/carrier-events`
  (PR #2876), and OMG's model does not store Oracle shipment numbers.
- **Exact wording as presented (2026-10-26, chat):** "(a) Recommended: add the ticket's
  exact route ... reading the shipment's tracking numbers from the same Fusion read
  OMG-3160 establishes ...; or (b) have OMG-3160 return FR external ids per line and let
  the page call the merged FR-keyed route — awkward for multi-order shipments."
- **Where to ask / posted:** asked in chat.
- **Response log:**
  - 2026-10-26 — Luis: "does the new ticket solve the question?" (i.e. does OMG-3160
    close the gap). Answered: no — it covers the read side only; the submit endpoint
    question stayed open.
  - 2026-10-26 — Luis asked for an independent agent check of the proposed
    shipment-keyed POST. Ran one blind seat (generalPurpose; brief without our
    proposal). The agent DIVERGED: the gap is illusory — the Oracle shipment number IS
    the FR external id by construction. I falsified each load-bearing claim against the
    code (all confirmed): `mapper.py:179,221` (Manhattan `shipment_id` = FR external
    id); `_ship_confirm_sales_orders.py:421,205` (Oracle shipment created under that
    number); `_belongs_to_another_tracker` guard present; stage mock tracker id
    `trk_<uuid>`; `stage.yml` sync enabled. RESOLVED: no new endpoint — the page calls
    the merged FR-keyed route with `externalId = shipmentNumber`. Both my (a) and the
    ticket's URL are dropped; the ticket-comment correction to Gabriel/Miguel carries
    this.

#### Q3 — Neither repo is cloned locally. Where do they go?

- **Context:** the ioet workspace had no `omg-ui` or `order-management-gateway`; house
  rules require asking before creating root-level directories.
- **Exact wording as presented (2026-10-26, chat):** "Clone both to
  `~/projects/ioet/omg-ui` and `~/projects/ioet/order-management-gateway` and add them
  to `ioet.code-workspace` (recommended ...), or elsewhere?"
- **Where to ask / posted:** asked in chat.
- **Response log:**
  - 2026-10-26 — Luis: "clone them". RESOLVED: both cloned to the ioet root over SSH
    and added to `ioet.code-workspace`; OMG got a `.venv-host` (Python 3.14.7, full
    `uv sync`) wired as the folder interpreter; `.venv-host/` in `.git/info/exclude`;
    interpreter line in the tracked `.vscode/settings.json` hidden via
    `skip-worktree`; global git config gained
    `url."git@github.com:".insteadOf "https://github.com/"` (needed for the
    `omg-catalog-client` git dependency; disclosed to the user).

## Assumption / suggestion register (phase-2, all confirmed or standing)

- A1 — target repo is `WarbyParker/omg-ui` (`src/...`), not the old monorepo
  `frontend/`. CONFIRMED (OMG-3418 landed in omg-ui PR #295).
- A2 — modal built per the ticket spec, reusing the shared carrier-events module; no
  changes to `WMSTest.tsx` / `CarrierEventsPanel.tsx` behavior. STANDING.
- A3 — route + Sidebar entry gated by a per-environment flag, off in production (AC5).
  STANDING (named `shipmentsTool`, per S1).
- A4 — no helios checkout needed; the ticket's modal spec + the ported presets suffice.
  STANDING.
- A5 — no RICE/FSD for this ticket; discovery ran on the ticket + linked tickets +
  merged code. CONFIRMED by the user (proceeded).
- S1 — own flag `shipmentsTool` rather than reusing `wmsTestTools`. ADOPTED.
- S2 — tests mirror `CarrierEventsPanel.test.tsx` (mock `apiFetch`). ADOPTED.
- O1/O2 — backend-dependency risks: mitigated — the contract is frozen (merged route +
  OMG-3160's documented fields); only stage verification waits on Miguel and the
  monocle fix.
