---
name: OTCM-139198 retire IN-I-2019L
overview: "Retire the temporary RICE id IN-I-2019L / FEDEX_LEGACY from the cycle-count callback path per OTCM-139198. PR 1 adds a retire-in-i-2019l feature flag that rejects IN-I-2019L callbacks with a controlled 400 instead of a 500 (flag ships true in all four envs — approved deviation from the inert-deploy plan). PR 2 physically deletes the enum entry, factory entry, ProviderRICEId.FEDEX_LEGACY, and the temporary tests, and is prepared but merged only after the flag is true in prod plus a 30-day zero-traffic window. PR 3 (endgame, after PR 2 merges) removes the retirement mechanism and the dead ProviderRICEId enum, leaving the factory's generic unknown-id error as the permanent tombstone. The 30-day evidence check (scope item 1) is already done and posted on the ticket: zero IN-I-2019L matches across all three prod Lambdas."
todos:
  - id: "1"
    content: Branch OTCM-139198-retire-in-i-2019l off latest main in monocle_integrations
    status: completed
  - id: "2"
    content: "PR 1: add RetiredRiceIdError + 400 handler mapping, FeatureFlagService method, WpCycleCountCallback gate, flag false in 4 env yml files"
    status: completed
  - id: "3"
    content: "PR 1 tests: callback unit tests (flag on/off) + API test asserting 400 for IN-I-2019L"
    status: completed
  - id: "4"
    content: "PR 1: fast checks (unit tests on touched modules, check-format), dev-container provenance check first"
    status: completed
  - id: "5"
    content: "PR 1: draft description to tmp/pr_description.md, pre-opening review, then coverage gate + API suite before push (with user approval)"
    status: completed
  - id: "6"
    content: Draft exclusion comment for OTCM-139197 (retire-in-i-2019l must not be absorbed by the when_off cleanup) — post after user approval
    status: in_progress
  - id: "7"
    content: "PR 2 (later, merge-gated): delete FEDEX_LEGACY enum, factory entry, ProviderRICEId.FEDEX_LEGACY, temporary API tests — merge only after flag true in prod + 30-day zero-traffic window"
    status: pending
  - id: "8"
    content: "PR 3 (endgame, after PR 2 merges): delete flag + gate + RetiredRiceIdError + handler + retired-id tests + dead ProviderRICEId enum; factory unknown-id error becomes the tombstone"
    status: pending
isProject: false
---

# OTCM-139198 — Retire IN-I-2019L / FEDEX_LEGACY

All work in the monocle_integrations repo. Approved decisions: new domain exception mapped to the existing 400 handler (Q2); flag enabled in all envs in PR 1 (Q4 superseded by the 2026-10-12 deviation); gate at the domain integration level, before the factory lookup (Q5); PR 2 held unmerged until the flag is true in prod plus the 30-day post-flip zero-traffic window (Q3).

## PR breakdown

| # | Title | Repo | Contents | Est. lines | Depends on |
|---|---|---|---|---|---|
| 1 | [OTCM-139198] Add retire-in-i-2019l flag with controlled 400 rejection | monocle_integrations | New exception + handler mapping, flag service method, gate in WpCycleCountCallback, flag false in 4 env yml files, unit + API tests | ~250 (40% code / 60% tests) | none — inert until flag flips |
| 2 | [OTCM-139198] Delete FEDEX_LEGACY enum, factory entry, and temporary tests | monocle_integrations | Delete enum member, factory entry, ProviderRICEId.FEDEX_LEGACY, temporary API tests + factory unit test; export cleanup | ~120 (mostly deletions) | PR 1 merged; flag true in prod; 30 days zero IN-I-2019L after the flip |
| 3 | [OTCM-139198] Remove retire-in-i-2019l machinery and the dead ProviderRICEId enum | monocle_integrations | Delete flag (4 ymls + service method), gate + literal constant, RetiredRiceIdError + handler registration, retired-id tests, ProviderRICEId + 2 re-exports | ~150 (mostly deletions) | PR 2 merged; stale-flag CI keeps ticketing until done |

## PR 1 — flag + controlled rejection

1. New domain exception `RetiredRiceIdError` (subclass pattern follows `CycleCountCallbackError`) in [_domain/_exceptions/_cycle_count_callback_exceptions.py](monocle_integrations/_domain/_exceptions/_cycle_count_callback_exceptions.py); re-export from [_domain/_exceptions/__init__.py](monocle_integrations/_domain/_exceptions/__init__.py) and [_domain/__init__.py](monocle_integrations/_domain/__init__.py). Message states the RICE id is retired and the callback is rejected.

2. Map `(_domain.RetiredRiceIdError, _bad_request_exception_handler)` in [_api/_handlers/_exception_handlers/__init__.py](monocle_integrations/_api/_handlers/_exception_handlers/__init__.py) — same 400 pattern as `MandatorySequenceImportJobNotFound`; response body `{"error_detail": ...}`. Update [_api/_handlers/_exception_handlers/_init_unit_test.py](monocle_integrations/_api/_handlers/_exception_handlers/_init_unit_test.py).

3. Add `is_retire_in_i_2019l_enabled()` to [_domain/_services/_feature_flag_service.py](monocle_integrations/_domain/_services/_feature_flag_service.py) (flag name `retire-in-i-2019l`).

4. Gate in [_domain/_integrations/_wp_cycle_count_integration_callback/_cycle_count_callback.py](monocle_integrations/_domain/_integrations/_wp_cycle_count_integration_callback/_cycle_count_callback.py):
   - `__init__` gains `feature_flag_service` param.
   - In `__call__`, after `load_job_details = _steps.extract_load_job_details(load_job)` and before `self._cycle_count_processor_factory.get_processor(...)`: if `load_job_details.rice_id` equals the module-level constant `_RETIRED_RICE_ID_IN_I_2019L = "IN-I-2019L"` and `await self._feature_flag_service.is_retire_in_i_2019l_enabled()` is true, raise `RetiredRiceIdError`. Flag off keeps today's factory mapping untouched.

5. Wiring: add `feature_flag_service=feature_flag_service` to the `WpCycleCountCallback(...)` construction in [_domain/_monocle_integrations.py](monocle_integrations/_domain/_monocle_integrations.py) (line ~428; the service is already in scope there). No `_entry_points.py` / `get_adapters` change needed.

6. Flag config: append `retire-in-i-2019l` with `value: true` to all four of [monocle_integrations/_feature_flag_config/dev.yml](monocle_integrations/_feature_flag_config/dev.yml), [stage.yml](monocle_integrations/_feature_flag_config/stage.yml), [prod.yml](monocle_integrations/_feature_flag_config/prod.yml), [ott.yml](monocle_integrations/_feature_flag_config/ott.yml). Deployed [config/us-east-1/](config/) carries no flags — verified, no change there.

7. Tests:
   - [_cycle_count_callback_unit_test.py](monocle_integrations/_domain/_integrations/_wp_cycle_count_integration_callback/_cycle_count_callback_unit_test.py): flag on + IN-I-2019L raises `RetiredRiceIdError`; flag off + IN-I-2019L still resolves the legacy processor; flag on + IN-I-2019 unaffected.
   - [_api/_test/_cycle_count_callback_routes_api_test.py](monocle_integrations/_api/_test/_cycle_count_callback_routes_api_test.py): POST callback with `rice_id=IN-I-2019L` and flag on returns 400 with `error_detail`, not 500.
   - Existing `TestCycleCountImportVerificationForLegacyFedex` class keeps passing with flag off (its fixtures default the flag off).

8. Fast checks per pr-workflow: `make test-unit` on touched modules, `make check-format`; full coverage gate (`make check-coverage`) and API suite only right before the push. Dev-container provenance check before any make/docker command.

## PR 2 — physical deletion (prepared, merge-gated)

- Remove `CycleCountProvider.FEDEX_LEGACY` from [_domain/_integrations/_shared/_providers.py](monocle_integrations/_domain/_integrations/_shared/_providers.py) and the temporary factory entry (lines ~92–96) from [_cycle_count_processor_factory.py](monocle_integrations/_domain/_integrations/_wp_cycle_count_integration_callback/_steps/_cycle_count_processor/_cycle_count_processor_factory.py), plus its unit-test case.
- Remove `ProviderRICEId.FEDEX_LEGACY` from [_domain/_models/_cycle_count.py](monocle_integrations/_domain/_models/_cycle_count.py) (exported but unused — trivial).
- Delete `TestCycleCountImportVerificationForLegacyFedex` from the API test file.
- Keep the PR 1 rejection logic keyed on the literal constant so a stray legacy callback still gets the controlled 400 while the flag is true.

## PR 3 — endgame deletion (after PR 2 merges)

- Remove `retire-in-i-2019l` from the four env flag ymls and `FeatureFlagService.is_retire_in_i_2019l_enabled()` with its tests.
- Remove the gate and the `_RETIRED_RICE_ID_IN_I_2019L` literal from `_cycle_count_callback.py`, `RetiredRiceIdError` and its `__init__` re-exports, the 400-handler registration and its handler test, and the retired-id unit/API tests.
- Remove the dead `ProviderRICEId` enum and its two re-exports (`_domain/_models/__init__.py`, `_domain/__init__.py`) — verified unused during the PR 2 review.
- After PR 3, a stray IN-I-2019L callback hits the factory's generic unknown-id `CycleCountCallbackError` (500 + error ticket): the permanent tombstone.

## Sequencing and guards

- Approved deviation (2026-10-12): PR 1 ships the flag `true` in all four env ymls instead of deploying inert; the zero-traffic evidence (comment 957876) supports rejecting on deploy. Deploying #2700 IS the flip, so "post-flip" means post-#2700-prod-deploy. QA after deploy: IN-I-2019 create + callback work; IN-I-2019L gets the controlled 400; ABB/LMS unchanged; `FEDEX_LEGACY_UPC_REMAP` untouched.
- PR 2 merges only after #2700 deploys to prod plus 30 days of zero IN-I-2019L observed post-deploy. Until then it sits open as a draft PR stacked on PR 1 (user decision, Q3; draft per the pre-opening review).
- Endgame (decided 2026-10-12): PR 3 removes the whole retirement mechanism — flag (4 ymls + `is_retire_in_i_2019l_enabled`), gate + `_RETIRED_RICE_ID_IN_I_2019L` literal, `RetiredRiceIdError` + its 400-handler registration, the retired-id tests — and the dead `ProviderRICEId` enum + its two re-exports. It merges only after PR 2 merges; the stale-feature-flag CI check keeps ticketing the flag until then, and the OTCM-139197 exclusion comment protects the flag from `when_off` cleanup in the meantime.
- OTCM-139197 guard: post an exclusion comment on OTCM-139197 so its when_off cleanup does not absorb `retire-in-i-2019l` between the flag flip and PR 2's merge. Draft before posting; requires user approval.
- No OIC-side or cross-repo changes: OIC already sends IN-I-2019 in callbacks (verified via CloudWatch evidence).
- Scope item 1 (30-day evidence) is complete; comment 957876 posted on the ticket.