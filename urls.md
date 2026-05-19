- Scale WMS
	- https://wpkrstg.manhscale.com/scale/trans/dashboard

- books from oreilly:
	- https://www.oreilly.com/ 

- Support
	- https://support.warbyparker.com/support/login

- Github stage:
	- https://github.com/WarbyParker/monocle_integrations/pull/1592

- Project whole documentation, including other FSD, user stories, testing scenarios:
	- https://drive.google.com/drive/folders/1XOXP7l5cug2MGherdoMZ33RjTmAB98Pr

- Lean Specs for development
	- https://drive.google.com/drive/folders/1Pf3JoT1biPQzUnHoPIJ74yE2DaUyJovc

- Process flows diagrams (entire flow)
	- https://drive.google.com/drive/folders/13erUp3Q-iicFzzpXfMKWe4b9fmgj3PO4

- monocles lambda - API
	- prod: https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/oic-monocle-integrations-lambda-stage-us-east-1?subtab=url&tab=monitoring
	- stage: https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/oic-monocle-integrations-lambda-stage-us-east-1?subtab=url&tab=monitoring

- monocles lambda - event handler (S3)
	- stage https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/oic-monocle-integrations-events_handler_lambda-stage-us-east-1?tab=code

- S3 bucket:
	- stage: https://us-east-1.console.aws.amazon.com/s3/buckets/transfer-stage-data?region=us-east-1&prefix=vendors/advanced_photochromics/In/compensated_rx/&showversions=false
	- stage: https://us-east-1.console.aws.amazon.com/s3/buckets/transfer-stage-data?prefix=vendors%2FManhattan%2FMFG-I-3021%2F&region=us-east-1&tab=objects

- monocles lambda ??
	- prod: https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/oic-monocle-integrations-events_handler_lambda-prod-us-east-1?tab=code
	- stage: https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/oic-monocle-integrations-events_handler_lambda-stage-us-east-1?tab=code

- OIC docs
	- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/fasrp/op-materialtransactions-post.html

- Oracle ERP docs tables description
	- https://docs.oracle.com/en/cloud/saas/financials/25d/books.html
	- https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/oedsc/egoitemeffb-23612.html#Details

- Oracle ERP (reports and "queries")
	- dev1: https://fa-evdi-dev1-saasfaprod1.fa.ocs.oraclecloud.com/fscmUI/faces/AtkHomePageWelcome
	- evdi-test (they call it "stage"): https://fa-evdi-test-saasfaprod1.fa.ocs.oraclecloud.com/fscmUI/faces/AtkHomePageWelcome
	- https://fa-evdi-test-saasfaprod1.fa.ocs.oraclecloud.com/fscmUI/faces/AtkHomePageWelcome?_adf.ctrl-state=1a1g9ckgym_1&_adf.no-new-window-redirect=true&_afrLoop=18960188241766294&_afrWindowMode=2&_afrWindowId=null&_afrFS=16&_afrMT=screen&_afrMFW=1365&_afrMFH=968&_afrMFDW=1920&_afrMFDH=1080&_afrMFC=8&_afrMFCI=0&_afrMFM=0&_afrMFR=96&_afrMFG=0&_afrMFS=0&_afrMFO=0

- OIC Prod changes
	- [https://docs.google.com/spreadsheets/d/1C4WTH_EPQ6BKwL22b8qnJT8NillpYmhv0gRhnX7c9ec/edit?usp=sharing](https://docs.google.com/spreadsheets/d/1C4WTH_EPQ6BKwL22b8qnJT8NillpYmhv0gRhnX7c9ec/edit?usp=sharing)

- Oracle ATP
	- `select * from WP_INT_GENERIC_REPORT_PARAM`
	- credentials and urls:
	- https://docs.google.com/spreadsheets/d/10INW7gW6qiGM-gqHDwU2H-7Qy_g0bMpm98DHpvhQAEk/edit?pli=1&gid=0#gid=0

- OIC platform
	- ??? works: https://design.integration.us-phoenix-1.ocp.oraclecloud.com/?integrationInstance=oictest2-axhxufzsltne-px
	- prod changes: https://docs.google.com/spreadsheets/d/1C4WTH_EPQ6BKwL22b8qnJT8NillpYmhv0gRhnX7c9ec/edit?usp=sharing&pli=1&authuser=0
	- Dev  
		- OIC: https://oic-test-inst-axhxufzsltne-px.integration.ocp.oraclecloud.com/ 
		- Oracle ERP: [https://fa-evdi-dev1-saasfaprod1.fa.ocs.oraclecloud.com/fscmUI/faces/FuseWelcome?_adf.ctrl-state=165[…]M=0&_afrMFR=192&_afrMFG=0&_afrMFS=0&_afrMFO=0](https://fa-evdi-dev1-saasfaprod1.fa.ocs.oraclecloud.com/fscmUI/faces/FuseWelcome?_adf.ctrl-state=165x65j434_1&_adf.no-new-window-redirect=true&_afrLoop=72736312678623741&_afrWindowMode=2&_afrWindowId=null&_afrFS=16&_afrMT=screen&_afrMFW=1641&_afrMFH=943&_afrMFDW=1643&_afrMFDH=947&_afrMFC=10&_afrMFCI=0&_afrMFM=0&_afrMFR=192&_afrMFG=0&_afrMFS=0&_afrMFO=0)
	- Stage  
		- OIC: [https://oictest2-axhxufzsltne-px.integration.ocp.oraclecloud.com/](https://oictest2-axhxufzsltne-px.integration.ocp.oraclecloud.com/)  
		- Oracle ERP: https://fa-evdi-test-saasfaprod1.fa.ocs.oraclecloud.com/
	- Prod 
		- OIC: https://oic-prod-axhxufzsltne-ia.integration.ocp.oraclecloud.com/ic/home/
		- Oracle ERP: https://fa-evdi-saasfaprod1.fa.ocs.oraclecloud.com/
			- Reports: Hamburger > Tools > Report and analytics

	- OIC Credentials (same for all environments) 
		- [https://us-east-1.console.aws.amazon.com/secretsmanager/secret?name=prod%2FOracle%2Fwp.integration_user&region=us-east-1#](https://us-east-1.console.aws.amazon.com/secretsmanager/secret?name=prod%2FOracle%2Fwp.integration_user&region=us-east-1#)

- JIRA boards
	- https://warbyparker.atlassian.net/jira/software/c/projects/OTCM/boards/771
	- Errors tickets:
		- https://warbyparker.atlassian.net/jira/software/c/projects/OEH/boards/725
	- Filter issues by ticket:
		- https://warbyparker.atlassian.net/issues/?jql=textfields%20~%20%22MFG-I-3021%22

- warby parker
	- https://warbyparker.okta.com/

- warby parker github
	- https://github.com/WarbyParker/monocle_integrations

- circle ci
	- https://app.circleci.com/organization/github/WarbyParker
	- env vars for monocle (no values)
	- https://app.circleci.com/settings/project/github/WarbyParker/monocle_integrations/environment-variables

- directory/contacts:
	- https://www.notion.so/ioet/Company-Directory-21553fa4fef4803eb6cff97e6918b716
- notion
	- https://www.notion.so/ioet/Internal-ioet-Home-Page-20253fa4fef480c89b7dd5f6ea748a96
- slack
	- https://warbyparker.enterprise.slack.com/
	- https://ioetec.slack.com/
	- https://app.slack.com/client/T03VCBF1Z
- karma
	- created with slack account
	- https://app.karmabot.chat/rewards#/
- secure store: to share secrets like keys, creds
	- https://www.securestore.ioet.com/dashboard
- desk: to book a workspace
	- https://reservations.ioet.com/en
- snipe-it: inventory management of equipment
	- https://ioet.snipe-it.io/
- houses
	- https://www.notion.so/ioet/Houses-21053fa4fef4804a93ead5f23bac9d53
