# URL Catalog

> **Agent contract** (used by the `open-note-url` skill):
> - One row per entry. **Aliases** are lowercase, comma-separated — match user requests against them case-insensitively (substring OK).
> - **URL** holds exactly one bare URL (no markdown link syntax). Extra links go in **Notes** as plain text.
> - To extend: append a row to the most specific section, with memorable lowercase aliases.

## Oracle ERP (Fusion) pods

| Aliases | URL | Notes |
| --- | --- | --- |
| erp dev1, fusion dev1 | https://fa-evdi-dev1-saasfaprod1.fa.ocs.oraclecloud.com/ | |
| erp dev2, fusion dev2 | https://fa-evdi-dev2-saasfaprod1.fa.ocs.oraclecloud.com/ | |
| erp stage, erp test, fusion stage | https://fa-evdi-test-saasfaprod1.fa.ocs.oraclecloud.com/ | evdi-test pod |
| erp prod, fusion prod | https://fa-evdi-saasfaprod1.fa.ocs.oraclecloud.com/ | Reports: menu → Tools → Reports and Analytics |
| erp prod rest, fusion rest api | https://fa-evdi-saasfaprod1.fa.ocs.oraclecloud.com/fscmRestApi/resources/11.13.18.05 | REST API base (prod) |

## OIC (Oracle Integration Cloud)

| Aliases | URL | Notes |
| --- | --- | --- |
| oic dev | https://oic-test-inst-axhxufzsltne-px.integration.ocp.oraclecloud.com/ | |
| oic stage, oic test | https://oictest2-axhxufzsltne-px.integration.ocp.oraclecloud.com/ | |
| oic designer, oic stage designer | https://design.integration.us-phoenix-1.ocp.oraclecloud.com/?integrationInstance=oictest2-axhxufzsltne-px | Designer view of the stage instance |
| oic prod | https://oic-prod-axhxufzsltne-ia.integration.ocp.oraclecloud.com/ic/home/ | |
| oic prod changes | https://docs.google.com/spreadsheets/d/1C4WTH_EPQ6BKwL22b8qnJT8NillpYmhv0gRhnX7c9ec/edit | Change-tracking sheet |
| oic creds stage, wms oauth stage | https://us-east-1.console.aws.amazon.com/secretsmanager/secret?name=stage%2FOracle%2Fwms_oauth&region=us-east-1 | AWS secret `stage/Oracle/wms_oauth` (prod equivalent: `prod/Oracle/wms_oauth`) |
| oic creds prod, integration user | https://us-east-1.console.aws.amazon.com/secretsmanager/secret?name=prod%2FOracle%2Fwp.integration_user&region=us-east-1 | AWS secret `prod/Oracle/wp.integration_user` |

## AWS — monocle Lambdas (us-east-1)

| Aliases | URL | Notes |
| --- | --- | --- |
| lambda stage, monocle api stage | https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/oic-monocle-integrations-lambda-stage-us-east-1?subtab=url&tab=monitoring | REST API lambda |
| lambda prod, monocle api prod | https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/oic-monocle-integrations-lambda-prod-us-east-1?subtab=url&tab=monitoring | REST API lambda |
| lambda events stage, event handler stage | https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/oic-monocle-integrations-events_handler_lambda-stage-us-east-1?tab=code | S3/SQS event handler |
| lambda events prod, event handler prod | https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/oic-monocle-integrations-events_handler_lambda-prod-us-east-1?tab=code | S3/SQS event handler |

## AWS — S3 buckets

| Aliases | URL | Notes |
| --- | --- | --- |
| s3 stage ap, s3 advanced photochromics | https://us-east-1.console.aws.amazon.com/s3/buckets/transfer-stage-data?region=us-east-1&prefix=vendors/advanced_photochromics/In/compensated_rx/&showversions=false | transfer-stage-data · vendors/advanced_photochromics/In/compensated_rx |
| s3 stage manhattan, s3 mfg-i-3021 | https://us-east-1.console.aws.amazon.com/s3/buckets/transfer-stage-data?prefix=vendors%2FManhattan%2FMFG-I-3021%2F&region=us-east-1&tab=objects | transfer-stage-data · vendors/Manhattan/MFG-I-3021 |

## Scale WMS (Manhattan)

| Aliases | URL | Notes |
| --- | --- | --- |
| scale, wms, scale stage | https://wpkrstg.manhscale.com/scale/trans/dashboard | STG environment |
| scale receipt example | https://wpkrstg.manhscale.com/scale/details/receipt/133961 | Example receipt deep-link (TO/PO shipments) |

## Jira

| Aliases | URL | Notes |
| --- | --- | --- |
| jira, jira otcm, otcm board | https://warbyparker.atlassian.net/jira/software/c/projects/OTCM/boards/771 | |
| jira oeh, error tickets | https://warbyparker.atlassian.net/jira/software/c/projects/OEH/boards/725 | Auto-created error tickets |
| jira search, jira jql | https://warbyparker.atlassian.net/issues/?jql=textfields%20~%20%22MFG-I-3021%22 | Template — replace MFG-I-3021 with any ticket/RICE ID |

## GitHub & CI

| Aliases | URL | Notes |
| --- | --- | --- |
| github, monocle repo | https://github.com/WarbyParker/monocle_integrations | |
| github stage, stage pr | https://github.com/WarbyParker/monocle_integrations/pull/1592 | Specific PR |
| circleci, ci | https://app.circleci.com/organization/github/WarbyParker | |
| circleci env vars | https://app.circleci.com/settings/project/github/WarbyParker/monocle_integrations/environment-variables | Variable names only, no values |

## Project docs (Google Drive)

| Aliases | URL | Notes |
| --- | --- | --- |
| project docs, fsd docs | https://drive.google.com/drive/folders/1XOXP7l5cug2MGherdoMZ33RjTmAB98Pr | FSDs, user stories, testing scenarios |
| lean specs | https://drive.google.com/drive/folders/1Pf3JoT1biPQzUnHoPIJ74yE2DaUyJovc | |
| process flows, flow diagrams | https://drive.google.com/drive/folders/13erUp3Q-iicFzzpXfMKWe4b9fmgj3PO4 | End-to-end flow diagrams |
| atp creds, atp urls | https://docs.google.com/spreadsheets/d/10INW7gW6qiGM-gqHDwU2H-7Qy_g0bMpm98DHpvhQAEk/edit | ATP credentials/URLs sheet; see also `WP_INT_GENERIC_REPORT_PARAM` |

## Oracle product docs

| Aliases | URL | Notes |
| --- | --- | --- |
| oracle rest docs, scm rest docs | https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/fasrp/op-materialtransactions-post.html | 25d REST API (materialTransactions POST) |
| oracle financials docs, erp docs | https://docs.oracle.com/en/cloud/saas/financials/25d/books.html | 25d Financials books |
| oracle scm docs, item docs | https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/oedsc/egoitemeffb-23612.html#Details | 25d SCM tables |

## Warby Parker internal

| Aliases | URL | Notes |
| --- | --- | --- |
| okta, warby okta | https://warbyparker.okta.com/ | SSO portal |
| wp support | https://support.warbyparker.com/support/login | |
| slack warby | https://warbyparker.enterprise.slack.com/ | |
| slack warby client | https://app.slack.com/client/T03VCBF1Z | |

## ioet internal

| Aliases | URL | Notes |
| --- | --- | --- |
| slack ioet | https://ioetec.slack.com/ | |
| notion, ioet notion | https://www.notion.so/ioet/Internal-ioet-Home-Page-20253fa4fef480c89b7dd5f6ea748a96 | |
| directory, contacts | https://www.notion.so/ioet/Company-Directory-21553fa4fef4803eb6cff97e6918b716 | |
| houses | https://www.notion.so/ioet/Houses-21053fa4fef4804a93ead5f23bac9d53 | |
| karma | https://app.karmabot.chat/rewards#/ | Uses Slack account |
| securestore, share secrets | https://www.securestore.ioet.com/dashboard | Share keys/creds securely |
| desk, book desk, office booking | https://reservations.ioet.com/en | |
| snipe-it, equipment inventory | https://ioet.snipe-it.io/ | |

## Misc

| Aliases | URL | Notes |
| --- | --- | --- |
| oreilly, books | https://www.oreilly.com/ | |
