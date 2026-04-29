- my PRs
	- https://github.com/WarbyParker/monocle_integrations/pulls/@me
	- filter: is:open is:pr author:@me 

- before PR:
```
make up
make test-unit
make check-coverage
make check-format
make format

branch: OEH-50831-modify-po-inspection-report-dm
commit: [OEH-50831] Modify PO Inspection Report DM
- Adds optional parameter to filter by PO line status (other than OPEN).
- Adds optional parameter to filter by change notice.
- Filter early by moving where conditions to the JOIN level.
- Filter accessories and suppliers as requested.
  
description:
This PR modifies the PO Inspection Report data model:


sample description:
## Related Tickets
https://warbyparker.atlassian.net/browse/OTCM-105313

## Description
Implements a new Oracle BIP report reader to retrieve inbound files (BAI2) from the `IBY_INBOUND_FILE` table via the `/Custom/WP Integrations/SCM/WP GET INBOUND FILES.xdo` report.

- **Port**: `InboundFilesReader` abstract interface with `InboundFilesRequest` / `InboundFilesResponse` domain models under `_banking_service_reader`
- **Adapter**: `OracleInboundFilesReader` that calls the Oracle report, parses the XML response, and maps `G_1` entries to `InboundFile` domain objects
- **Mock server**: Handler, Jinja2 template, and setup/cleanup endpoints for the local mock Oracle ERP
- **Tests**: Unit tests (parsing, error handling, request validation) and integration tests against the mock server
- **Shared fixtures**: `inbound_file_factory`, `inbound_file_to_domain`, and `insert_inbound_files` extracted into `_fixtures.py` for reuse across test types

### Request parameters

| Parameter | Required | Notes |
|-----------|----------|-------|
| `P_BANK_TRANSMIT_CONFIG_ID` | Yes | Always required |
| `P_FROM_DATE` / `P_TO_DATE` | Conditional | Both must be provided together; `date` objects converted to ISO 8601 in the adapter |
| `P_FILE_NAMES` | Conditional | List of strings, comma-separated when sent to the report |

At least one of `P_FILE_NAMES` or the `P_FROM_DATE`/`P_TO_DATE` pair must be provided alongside `P_BANK_TRANSMIT_CONFIG_ID`.



Hey Team, could you help me reviewing this PR:
<URL>

I promise next time I will try to split it in smaller pieces.
```
- stage
```
1. Merge a main:
2. Después vas a ese pr y le das en update branch with rebase
https://github.com/WarbyParker/monocle_integrations/pull/1592
3. Y después creas el tag en stage
   
# list existing tags
git tag --sort=-taggerdate -n

# show tag
git show vstage28 --quiet

# create annotated tag with empty description
git tag -a vstage105 -m "[OTCM-109709] Fix PayPal settlement upload filename date format"
git push origin vstage105

# remove tag
git tag -d vstage26
```

