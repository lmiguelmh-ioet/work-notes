
## Dev Lead talks / Team 
- Do not write a lot of comments
	- when code reviewing people read comments, and that can be missleading
- SOLID
	- single responsability
- "por cada cosa que puedas separar es bueno tener un PR, mientras mas puedas atomizar se hace mas facil, el review, el trabajar en paralelo, el estar continuamente enviando cambios"


### TESTs
- prefer `mocker.patch.object` over `patch.object`
```
from pytest_mocker import MockerFixture (DO NOT USE MockFIxture deprecated name)
    @pytest.mark.asyncio
    async def test__delegates_to_processor__when_import_succeeds(
        self,
        mocker: MockerFixture,
    ) -> None:
        document_name = "statement_20260211.zip"
        mock_get_document_name = mocker.patch.object(
            WpBankStatementImportCallback,
            "_get_document_name",
            return_value=document_name,
        )
```

- you should use the dependencies_factory to inject the mock dependencies in the instance to test
```
NO!
processor = BankStatementImportCallbackProcessor(file_move_strategy=file_move_strategy)
YES: use dependencies
```

- unit tests
	- ?
- Event tests (oma file dispatcher)
	- https://github.com/WarbyParker/monocle_integrations/pull/1641/changes
- API tests (material transactions)
	- https://github.com/WarbyParker/monocle_integrations/pull/1600/changes
- Integration tests (sns)
	- https://github.com/WarbyParker/monocle_integrations/pull/1670/changes
- E2E test (material transactions)
	- https://github.com/WarbyParker/monocle_integrations/pull/1600/changes
### PRs reviewed by me (-1) others reviewing mine (+1)
- MARCOS: 
	- 2026/03/11: +1 PR
	- 2026/02/12: +1 PR
	- 2026/02/11: +2 PRs
- ARIEL:
	- 2026/02/?: +2 PRs
- GABRIEL:
	- 2026/02/?: +2 PRs

## Note system: why
[team.note-system](team.note-system.md)

## Github
[team.github](team.github.md)

## Poetry

- do NOT edit `pyproject.toml`
	- Automatic dependency resolution - Poetry finds compatible versions
	- Updates `poetry.lock` automatically
	- Validates your changes won't break dependencies
	- Handles version constraints correctly
```
# ✅ CORRECT: Use poetry add
poetry add amazon-sns-extended-client@^1.0.1
poetry add requests@^2.28  # Exact constraint
poetry add fastapi         # Latest compatible version
poetry add pytest --group dev
poetry add "django>=4.0,<5.0"  # Version range

# ✅ Editing is only for metadata (name, description)
# Edit these directly in pyproject.toml:
[tool.poetry]
name = "my-project"
version = "0.1.0"
description = "My description"  # ✅ OK to edit directly

```



## CloudWatch
- https://us-east-1.console.aws.amazon.com/lambda/home?region=us-east-1#/functions/oic-monocle-integrations-lambda-stage-us-east-1?tab=monitoring
- https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:logs-insights
```
/aws/lambda/oic-monocle-integrations-lambda-stage-us-east-1
---
fields @timestamp, @message, @logStream, @log
| filter @message like /MFG-I-3021/
| sort @timestamp desc
| limit 1000
```

## JIRA
- https://warbyparker.atlassian.net/issues/?jql=textfields%20~%20%22MFG-I-3021%22
	- ![](assets/Pasted%20image%2020260120145024.png)

- Astrid open tickets:
	- https://warbyparker.atlassian.net/issues?jql=project%20%3D%20%22Monocle%20%28Oracle%29%20Production%20Issues%22%20and%20created%20%3E%3D%20%222026-02-01%22%20and%20created%20%3C%3D%20%222026-03-01%22%20and%20type%20%3D%20Bug%20and%20summary%20~%20%22Error%7CPROD%7CNon-Payables%22%20AND%20status%20NOT%20IN%20%28Rejected%2C%20Resolved%29%20ORDER%20BY%20created%20DESC%2C%20status%20DESC
## OIC
- enable debug logs to see payload
	- ![](assets/Pasted%20image%2020260223144551.png)
	- ![](assets/Pasted%20image%2020260223144606.png)
	- ![](assets/Pasted%20image%2020260223144618.png)

- check executions
	- ![](assets/Pasted%20image%2020260223144356.png)

- OIC move to dev1 or stage
	- it took me a while, but the whole picture is this:  
		- OIC integrations point to our lambda that is in `stage`  
		- but the lambda can point to Oracle `dev1` or `stage`
			- `monocle_integrations/_config/stage.yml:3`
	- see branch: `[OTCM-104451] Point to dev1`
	- ![](assets/Pasted%20image%2020260227090031.png)
	- ![](assets/Pasted%20image%2020260227090258.png)
	- 

## TIckets for oncall
- From Monday to Sunday
	- ALL should be closed
- Next monday close the ones from weekend
- You might need more time, so ask Emilio

## Scrum meet
- scrum moderator is announced on Monday:
	- ![](assets/Pasted%20image%2020260120110646.png)
		- On Call Slack/Meetings - is the one that leads if moderator is not
- Structure
	- Team Updates
		- https://warbyparker.atlassian.net/jira/software/c/projects/OTCM/boards/771
		- (1) Rocio and (2) Fabiola and (3) Kio no están en el board de Jira
			- ![](assets/Pasted%20image%2020260220104144.png)
			- Select Group None (to confirm)
		- (4) Astrid and (5) Emilio
		- "Hello, ??? do you have any updates regarding your ticket?"
		- "Hello, ??? do you have any updates?"
		- "Hello, ??? any updates you want to share?"
		- "That's everyone."
	- Announcement section
		- "Let's move to the announcements sections?"
		- "Does anyone have any announcement?"
		- "Does anyone has any announcement to make?"
		- "Any other announcement?"
	- Dev huddle
		- "I think we can move onto the dev huddle"
		- "Does anyone have any topic?"
	- Ok, I think that's it for today?
## Oracle ERP
- See the transaction_date for Completed transactions (3021 perform material issue)
	- https://fa-evdi-dev1-saasfaprod1.fa.ocs.oraclecloud.com/fscmUI/faces/deeplink?objType=INV_COMPL_TXN&action=NONE
	- ![](assets/Pasted%20image%2020260227124618.png)

- See item all attributes (e.g. by item number -> UPC)
	- Product Information Management 
	- Tasks button
	- Manage Items menu item
	- Item: 19007, Search button
	- See the one under MST organization (warehouse?)
	- Specifications tab
	- All item attributes: UPC, SKU

## Slack
- solve credentials issue:
	- @joel.malchuk @tony.huang @alexis we are getting Status Code: 401\nResponse: \nError: 401, message='Unauthorized'  when we try to use the API with the WP_SCM_INTEGRATION_USER user in evdi-test, I've already reviewed the credentials and are correct I'm able to login into evdi-test
	- https://warbyparker.slack.com/archives/C06746714GZ/p1768945897493579

## Team

- proyecto
	- Dan Morel (WP - principal engineer)
	- Gabriel Viera

Astrid: 3 projects
Emilio: PM
Gabriel: tech lead
Ariel: 3 years
Jerson: developer 
Johnny: developer 3 months
Marcos: 
Michael: 4 years
Miguel: 2 years
Josué: Yos Yoshua 4 years
Fabiola: QA -
Kaio: QA Brazil 3 years
Rocio: Arg
Justo: 2 weeks

- top-performer
	- 1 Ariel - bueno técnicamente
		- gano quien saca la mayor cantidad de ticket que parece un bot
	- Josue - responsable + metódico
	- Miguel - bueno entender contexto de negocio - comunicación - proactivo
	- Gabriel - lead + capex (threshold de story points)

### Emilio Lopez
![Photo of manager](https://images7.bamboohr.com/23336/photos/40683-0-4.jpg?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9pbWFnZXM3LmJhbWJvb2hyLmNvbS8yMzMzNi8qIiwiQ29uZGl0aW9uIjp7IkRhdGVHcmVhdGVyVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNzY3Nzk5NzE3fSwiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3NzAzOTE3Mjd9fX1dfQ__&Signature=AeziZv1IO6JSL2LwsHFzFxEGopUNB9~eGjFLjpCcQh8QwzsNmgt2lSvjQAGBoUU8oUHgaWyQL5q7vy~aYrnrlVOdreSgJ80bShfTK8P0jHGh-ThLk2VzSTdTirdtqPPSbQCoPHAf8WtXSclrkr14GrSj4gk9ZcSRapzsk5jtkkmyXa1KLWBlHq1dxYu1kSVox13KNFPM2bxg9P0JAtFWQH6Zgsz6QA0QFlRlgjwKoEkx3T9zv6uKC~oojp2GHUE7eR-cMMNVJdFW4N2d6b1IV-OVfmJs7klG~kgVlailu4olb5713iV4wYXX3a4CKBNEx58WtXAmF50k2lK3PkekYA__&Key-Pair-Id=APKAIZ7QQNDH4DJY7K4Q)

Emilio López

- Senior PM/BA
- [emilio.lopez@ioet.com](mailto:emilio.lopez@ioet.com)
- [](mailto:emilio.lopez@ioet.com)[](https://ioet.bamboohr.com/self_onboarding/packet/www.linkedin.com/in/emilio-l%C3%B3pez-48a769129)

### Kaio Amaral

![Team member photo](https://images7.bamboohr.com/23336/photos/40805-3-4.jpg?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9pbWFnZXM3LmJhbWJvb2hyLmNvbS8yMzMzNi8qIiwiQ29uZGl0aW9uIjp7IkRhdGVHcmVhdGVyVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNzY3Nzk5NzE3fSwiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3NzAzOTE3Mjd9fX1dfQ__&Signature=AeziZv1IO6JSL2LwsHFzFxEGopUNB9~eGjFLjpCcQh8QwzsNmgt2lSvjQAGBoUU8oUHgaWyQL5q7vy~aYrnrlVOdreSgJ80bShfTK8P0jHGh-ThLk2VzSTdTirdtqPPSbQCoPHAf8WtXSclrkr14GrSj4gk9ZcSRapzsk5jtkkmyXa1KLWBlHq1dxYu1kSVox13KNFPM2bxg9P0JAtFWQH6Zgsz6QA0QFlRlgjwKoEkx3T9zv6uKC~oojp2GHUE7eR-cMMNVJdFW4N2d6b1IV-OVfmJs7klG~kgVlailu4olb5713iV4wYXX3a4CKBNEx58WtXAmF50k2lK3PkekYA__&Key-Pair-Id=APKAIZ7QQNDH4DJY7K4Q)

Kaio Amaral

- QA Engineer
- [kaio.amaral@ioet.com](mailto:kaio.amaral@ioet.com)
- [](mailto:kaio.amaral@ioet.com)

### Fabiola Briones

![Team member photo](https://images7.bamboohr.com/23336/photos/40671-0-4.jpg?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9pbWFnZXM3LmJhbWJvb2hyLmNvbS8yMzMzNi8qIiwiQ29uZGl0aW9uIjp7IkRhdGVHcmVhdGVyVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNzY3Nzk5NzE3fSwiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3NzAzOTE3Mjd9fX1dfQ__&Signature=AeziZv1IO6JSL2LwsHFzFxEGopUNB9~eGjFLjpCcQh8QwzsNmgt2lSvjQAGBoUU8oUHgaWyQL5q7vy~aYrnrlVOdreSgJ80bShfTK8P0jHGh-ThLk2VzSTdTirdtqPPSbQCoPHAf8WtXSclrkr14GrSj4gk9ZcSRapzsk5jtkkmyXa1KLWBlHq1dxYu1kSVox13KNFPM2bxg9P0JAtFWQH6Zgsz6QA0QFlRlgjwKoEkx3T9zv6uKC~oojp2GHUE7eR-cMMNVJdFW4N2d6b1IV-OVfmJs7klG~kgVlailu4olb5713iV4wYXX3a4CKBNEx58WtXAmF50k2lK3PkekYA__&Key-Pair-Id=APKAIZ7QQNDH4DJY7K4Q)

Fabiola Briones

- Senior QA Engineer
- [fabiola.briones@ioet.com](mailto:fabiola.briones@ioet.com)
- [](mailto:fabiola.briones@ioet.com)

### Josué Cando

![Team member photo](https://images7.bamboohr.com/23336/photos/40681-0-4.jpg?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9pbWFnZXM3LmJhbWJvb2hyLmNvbS8yMzMzNi8qIiwiQ29uZGl0aW9uIjp7IkRhdGVHcmVhdGVyVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNzY3Nzk5NzE3fSwiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3NzAzOTE3Mjd9fX1dfQ__&Signature=AeziZv1IO6JSL2LwsHFzFxEGopUNB9~eGjFLjpCcQh8QwzsNmgt2lSvjQAGBoUU8oUHgaWyQL5q7vy~aYrnrlVOdreSgJ80bShfTK8P0jHGh-ThLk2VzSTdTirdtqPPSbQCoPHAf8WtXSclrkr14GrSj4gk9ZcSRapzsk5jtkkmyXa1KLWBlHq1dxYu1kSVox13KNFPM2bxg9P0JAtFWQH6Zgsz6QA0QFlRlgjwKoEkx3T9zv6uKC~oojp2GHUE7eR-cMMNVJdFW4N2d6b1IV-OVfmJs7klG~kgVlailu4olb5713iV4wYXX3a4CKBNEx58WtXAmF50k2lK3PkekYA__&Key-Pair-Id=APKAIZ7QQNDH4DJY7K4Q)

Josué Cando

- Senior Software Engineer
- [josue.cando@ioet.com](mailto:josue.cando@ioet.com)
- [](mailto:josue.cando@ioet.com)[](https://linkedin.com/in/josueob)

### Johnny Coral

![Team member photo](https://images7.bamboohr.com/23336/photos/40909-0-4.jpg?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9pbWFnZXM3LmJhbWJvb2hyLmNvbS8yMzMzNi8qIiwiQ29uZGl0aW9uIjp7IkRhdGVHcmVhdGVyVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNzY3Nzk5NzE3fSwiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3NzAzOTE3Mjd9fX1dfQ__&Signature=AeziZv1IO6JSL2LwsHFzFxEGopUNB9~eGjFLjpCcQh8QwzsNmgt2lSvjQAGBoUU8oUHgaWyQL5q7vy~aYrnrlVOdreSgJ80bShfTK8P0jHGh-ThLk2VzSTdTirdtqPPSbQCoPHAf8WtXSclrkr14GrSj4gk9ZcSRapzsk5jtkkmyXa1KLWBlHq1dxYu1kSVox13KNFPM2bxg9P0JAtFWQH6Zgsz6QA0QFlRlgjwKoEkx3T9zv6uKC~oojp2GHUE7eR-cMMNVJdFW4N2d6b1IV-OVfmJs7klG~kgVlailu4olb5713iV4wYXX3a4CKBNEx58WtXAmF50k2lK3PkekYA__&Key-Pair-Id=APKAIZ7QQNDH4DJY7K4Q)

Johnny Coral

- Junior Software Engineer
- [johnny.coral@ioet.com](mailto:johnny.coral@ioet.com)
- [](mailto:johnny.coral@ioet.com)[](https://www.linkedin.com/in/johnny-coral/)

### Rocio Fabrykant

![Team member photo](https://images7.bamboohr.com/23336/photos/40894-0-4.jpg?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9pbWFnZXM3LmJhbWJvb2hyLmNvbS8yMzMzNi8qIiwiQ29uZGl0aW9uIjp7IkRhdGVHcmVhdGVyVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNzY3Nzk5NzE3fSwiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3NzAzOTE3Mjd9fX1dfQ__&Signature=AeziZv1IO6JSL2LwsHFzFxEGopUNB9~eGjFLjpCcQh8QwzsNmgt2lSvjQAGBoUU8oUHgaWyQL5q7vy~aYrnrlVOdreSgJ80bShfTK8P0jHGh-ThLk2VzSTdTirdtqPPSbQCoPHAf8WtXSclrkr14GrSj4gk9ZcSRapzsk5jtkkmyXa1KLWBlHq1dxYu1kSVox13KNFPM2bxg9P0JAtFWQH6Zgsz6QA0QFlRlgjwKoEkx3T9zv6uKC~oojp2GHUE7eR-cMMNVJdFW4N2d6b1IV-OVfmJs7klG~kgVlailu4olb5713iV4wYXX3a4CKBNEx58WtXAmF50k2lK3PkekYA__&Key-Pair-Id=APKAIZ7QQNDH4DJY7K4Q)

Rocio Fabrykant

- Oracle Specialist
- [rocio.fabrykant@ioet.com](mailto:rocio.fabrykant@ioet.com)
- [](mailto:rocio.fabrykant@ioet.com)

### Michael Guanolisa

![Team member photo](https://images7.bamboohr.com/23336/photos/40709-0-4.jpg?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9pbWFnZXM3LmJhbWJvb2hyLmNvbS8yMzMzNi8qIiwiQ29uZGl0aW9uIjp7IkRhdGVHcmVhdGVyVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNzY3Nzk5NzE3fSwiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3NzAzOTE3Mjd9fX1dfQ__&Signature=AeziZv1IO6JSL2LwsHFzFxEGopUNB9~eGjFLjpCcQh8QwzsNmgt2lSvjQAGBoUU8oUHgaWyQL5q7vy~aYrnrlVOdreSgJ80bShfTK8P0jHGh-ThLk2VzSTdTirdtqPPSbQCoPHAf8WtXSclrkr14GrSj4gk9ZcSRapzsk5jtkkmyXa1KLWBlHq1dxYu1kSVox13KNFPM2bxg9P0JAtFWQH6Zgsz6QA0QFlRlgjwKoEkx3T9zv6uKC~oojp2GHUE7eR-cMMNVJdFW4N2d6b1IV-OVfmJs7klG~kgVlailu4olb5713iV4wYXX3a4CKBNEx58WtXAmF50k2lK3PkekYA__&Key-Pair-Id=APKAIZ7QQNDH4DJY7K4Q)

Michael Guanoluisa

- Software Engineer
- [michael.guanoluisa@ioet.com](mailto:michael.guanoluisa@ioet.com)
- [](mailto:michael.guanoluisa@ioet.com)[](https://www.linkedin.com/in/michael-guanoluisa-96a723204/)[](https://www.facebook.com/michael.guanoluisaquiroz)

### Marcos Hernandez

![Team member photo](https://images7.bamboohr.com/23336/photos/40859-0-4.jpg?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9pbWFnZXM3LmJhbWJvb2hyLmNvbS8yMzMzNi8qIiwiQ29uZGl0aW9uIjp7IkRhdGVHcmVhdGVyVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNzY3Nzk5NzE3fSwiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3NzAzOTE3Mjd9fX1dfQ__&Signature=AeziZv1IO6JSL2LwsHFzFxEGopUNB9~eGjFLjpCcQh8QwzsNmgt2lSvjQAGBoUU8oUHgaWyQL5q7vy~aYrnrlVOdreSgJ80bShfTK8P0jHGh-ThLk2VzSTdTirdtqPPSbQCoPHAf8WtXSclrkr14GrSj4gk9ZcSRapzsk5jtkkmyXa1KLWBlHq1dxYu1kSVox13KNFPM2bxg9P0JAtFWQH6Zgsz6QA0QFlRlgjwKoEkx3T9zv6uKC~oojp2GHUE7eR-cMMNVJdFW4N2d6b1IV-OVfmJs7klG~kgVlailu4olb5713iV4wYXX3a4CKBNEx58WtXAmF50k2lK3PkekYA__&Key-Pair-Id=APKAIZ7QQNDH4DJY7K4Q)

Marcos Hernández
"but I like throwing fuel on the fire"
- Software Engineer
- [marcos.hernandez@ioet.com](mailto:marcos.hernandez@ioet.com)
- [](mailto:marcos.hernandez@ioet.com)[](https://www.linkedin.com/in/marcos-hernandez-896b11185/)

### Jerson Morocho

![Team member photo](https://images7.bamboohr.com/23336/photos/40653-0-4.jpg?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9pbWFnZXM3LmJhbWJvb2hyLmNvbS8yMzMzNi8qIiwiQ29uZGl0aW9uIjp7IkRhdGVHcmVhdGVyVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNzY3Nzk5NzE3fSwiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3NzAzOTE3Mjd9fX1dfQ__&Signature=AeziZv1IO6JSL2LwsHFzFxEGopUNB9~eGjFLjpCcQh8QwzsNmgt2lSvjQAGBoUU8oUHgaWyQL5q7vy~aYrnrlVOdreSgJ80bShfTK8P0jHGh-ThLk2VzSTdTirdtqPPSbQCoPHAf8WtXSclrkr14GrSj4gk9ZcSRapzsk5jtkkmyXa1KLWBlHq1dxYu1kSVox13KNFPM2bxg9P0JAtFWQH6Zgsz6QA0QFlRlgjwKoEkx3T9zv6uKC~oojp2GHUE7eR-cMMNVJdFW4N2d6b1IV-OVfmJs7klG~kgVlailu4olb5713iV4wYXX3a4CKBNEx58WtXAmF50k2lK3PkekYA__&Key-Pair-Id=APKAIZ7QQNDH4DJY7K4Q)

Jerson Morocho

- Senior Software Engineer
- [jerson.morocho@ioet.com](mailto:jerson.morocho@ioet.com)
- [](mailto:jerson.morocho@ioet.com)[](https://www.linkedin.com/in/thegreatyamori/)[](http://twitter.com/https://twitter.com/thegreatyamori)

### Miguel Muñoz

![Team member photo](https://images7.bamboohr.com/23336/photos/40824-0-4.jpg?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9pbWFnZXM3LmJhbWJvb2hyLmNvbS8yMzMzNi8qIiwiQ29uZGl0aW9uIjp7IkRhdGVHcmVhdGVyVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNzY3Nzk5NzE3fSwiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3NzAzOTE3Mjd9fX1dfQ__&Signature=AeziZv1IO6JSL2LwsHFzFxEGopUNB9~eGjFLjpCcQh8QwzsNmgt2lSvjQAGBoUU8oUHgaWyQL5q7vy~aYrnrlVOdreSgJ80bShfTK8P0jHGh-ThLk2VzSTdTirdtqPPSbQCoPHAf8WtXSclrkr14GrSj4gk9ZcSRapzsk5jtkkmyXa1KLWBlHq1dxYu1kSVox13KNFPM2bxg9P0JAtFWQH6Zgsz6QA0QFlRlgjwKoEkx3T9zv6uKC~oojp2GHUE7eR-cMMNVJdFW4N2d6b1IV-OVfmJs7klG~kgVlailu4olb5713iV4wYXX3a4CKBNEx58WtXAmF50k2lK3PkekYA__&Key-Pair-Id=APKAIZ7QQNDH4DJY7K4Q)

Miguel Muñoz

- Software Engineer
- [miguel.munoz@ioet.com](mailto:miguel.munoz@ioet.com)
- [](mailto:miguel.munoz@ioet.com)[](https://www.linkedin.com/in/jos%C3%A9-mu%C3%B1oz-49b295a3/)

### Justo Rivera

![Team member photo](https://images7.bamboohr.com/23336/photos/40928-0-4.jpg?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9pbWFnZXM3LmJhbWJvb2hyLmNvbS8yMzMzNi8qIiwiQ29uZGl0aW9uIjp7IkRhdGVHcmVhdGVyVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNzY3Nzk5NzE3fSwiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3NzAzOTE3Mjd9fX1dfQ__&Signature=AeziZv1IO6JSL2LwsHFzFxEGopUNB9~eGjFLjpCcQh8QwzsNmgt2lSvjQAGBoUU8oUHgaWyQL5q7vy~aYrnrlVOdreSgJ80bShfTK8P0jHGh-ThLk2VzSTdTirdtqPPSbQCoPHAf8WtXSclrkr14GrSj4gk9ZcSRapzsk5jtkkmyXa1KLWBlHq1dxYu1kSVox13KNFPM2bxg9P0JAtFWQH6Zgsz6QA0QFlRlgjwKoEkx3T9zv6uKC~oojp2GHUE7eR-cMMNVJdFW4N2d6b1IV-OVfmJs7klG~kgVlailu4olb5713iV4wYXX3a4CKBNEx58WtXAmF50k2lK3PkekYA__&Key-Pair-Id=APKAIZ7QQNDH4DJY7K4Q)

Justo Rivera

- Senior Software Engineer
- [justo.rivera@ioet.com](mailto:justo.rivera@ioet.com)
- [](mailto:justo.rivera@ioet.com)

### Ariel Sperduti

![Team member photo](https://images7.bamboohr.com/23336/photos/40809-1-4.jpg?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9pbWFnZXM3LmJhbWJvb2hyLmNvbS8yMzMzNi8qIiwiQ29uZGl0aW9uIjp7IkRhdGVHcmVhdGVyVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNzY3Nzk5NzE3fSwiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3NzAzOTE3Mjd9fX1dfQ__&Signature=AeziZv1IO6JSL2LwsHFzFxEGopUNB9~eGjFLjpCcQh8QwzsNmgt2lSvjQAGBoUU8oUHgaWyQL5q7vy~aYrnrlVOdreSgJ80bShfTK8P0jHGh-ThLk2VzSTdTirdtqPPSbQCoPHAf8WtXSclrkr14GrSj4gk9ZcSRapzsk5jtkkmyXa1KLWBlHq1dxYu1kSVox13KNFPM2bxg9P0JAtFWQH6Zgsz6QA0QFlRlgjwKoEkx3T9zv6uKC~oojp2GHUE7eR-cMMNVJdFW4N2d6b1IV-OVfmJs7klG~kgVlailu4olb5713iV4wYXX3a4CKBNEx58WtXAmF50k2lK3PkekYA__&Key-Pair-Id=APKAIZ7QQNDH4DJY7K4Q)

Ariel Sperduti

- Senior Software Engineer
- [ariel.sperduti@ioet.com](mailto:ariel.sperduti@ioet.com)
- [](mailto:ariel.sperduti@ioet.com)[](https://www.linkedin.com/in/arielsperduti/)

### Gabriel Viera

![Team member photo](https://images7.bamboohr.com/23336/photos/40697-0-4.jpg?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiaHR0cHM6Ly9pbWFnZXM3LmJhbWJvb2hyLmNvbS8yMzMzNi8qIiwiQ29uZGl0aW9uIjp7IkRhdGVHcmVhdGVyVGhhbiI6eyJBV1M6RXBvY2hUaW1lIjoxNzY3Nzk5NzE3fSwiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE3NzAzOTE3Mjd9fX1dfQ__&Signature=AeziZv1IO6JSL2LwsHFzFxEGopUNB9~eGjFLjpCcQh8QwzsNmgt2lSvjQAGBoUU8oUHgaWyQL5q7vy~aYrnrlVOdreSgJ80bShfTK8P0jHGh-ThLk2VzSTdTirdtqPPSbQCoPHAf8WtXSclrkr14GrSj4gk9ZcSRapzsk5jtkkmyXa1KLWBlHq1dxYu1kSVox13KNFPM2bxg9P0JAtFWQH6Zgsz6QA0QFlRlgjwKoEkx3T9zv6uKC~oojp2GHUE7eR-cMMNVJdFW4N2d6b1IV-OVfmJs7klG~kgVlailu4olb5713iV4wYXX3a4CKBNEx58WtXAmF50k2lK3PkekYA__&Key-Pair-Id=APKAIZ7QQNDH4DJY7K4Q)

Gabriel Viera

- Senior Software Engineer
- [gabriel.viera@ioet.com](mailto:gabriel.viera@ioet.com)
- [](mailto:gabriel.viera@ioet.com)[](https://www.linkedin.com/in/gabriel-viera/)[](http://twitter.com/https://twitter.com/Gabriel62363152)


![[Pasted image 20260107104332.png]]

## Annual review questions

### Engineer
```
Your Role in Relation to the Reviewee
*
Select the option that best describes your working relationship
Direct Team Member (same team, similar level)
Tech Lead / Senior Engineer
Project Manager / Business Analyst
Team Lead / Engineering Manager
Cross-functional Collaborator (Designer, QA, DevOps)
Client / Stakeholder
Other
How long have you worked with this person?
*
Less than 3 months
3-6 months
6-12 months
1-2 years
More than 2 years

This person follows coding standards and best practices
1 - Rarely follows standards
2 - Sometimes follows standards
3 - Usually follows standards
4 - Always follows standards and suggests improvements
5 - Sets the standard for the team

This person helps improve our codebase and technical processes
1 - Rarely contributes improvements
2 - Occasionally suggests improvements
3 - Regularly contributes improvements
4 - Actively drives improvements
5 - Leads major improvements that benefit the whole team

This person creates maintainable and scalable solutions
1 - Rarely creates maintainable solutions
2 - Sometimes creates maintainable solutions
3 - Usually creates maintainable solutions
4 - Always creates well-structured solutions
5 - Creates exemplary solutions that others learn from

This person manages their work to meet deadlines
*
1 - Often misses deadlines
2 - Sometimes struggles with deadlines
3 - Usually meets deadlines
4 - Always meets deadlines and stays organized
5 - Always delivers on time and helps the team stay on track
This person speaks up when deadlines are unrealistic
*
1 - Rarely raises timeline concerns
2 - Sometimes questions unrealistic deadlines
3 - Usually negotiates when needed
4 - Proactively manages expectations
5 - Helps the team plan realistic timelines
This person balances speed and quality in their work
*
1 - Often sacrifices quality for speed
2 - Sometimes struggles to balance both
3 - Usually finds the right balance
4 - Consistently delivers quality work on time
5 - Sets the example for balancing speed and quality

This person helps with tasks beyond their main responsibilities
*
1 - Rarely helps beyond assigned tasks
2 - Sometimes helps when asked
3 - Regularly helps with additional tasks
4 - Actively looks for ways to contribute
5 - Goes above and beyond to support team success
This person works with managers and leads to improve processes
*
1 - Rarely engages in process discussions
2 - Sometimes shares process feedback
3 - Regularly contributes to process improvements
4 - Actively suggests and implements improvements
5 - Drives significant process improvements
This person identifies opportunities for innovation and improvement
*
1 - Rarely notices improvement opportunities
2 - Sometimes spots areas for improvement
3 - Regularly identifies improvement opportunities
4 - Actively pursues innovative solutions
5 - Consistently drives innovation and positive change

This person completes tasks without needing supervision
*
1 - Usually needs guidance and follow-up
2 - Sometimes needs reminders
3 - Usually works independently
4 - Always works independently and reliably
5 - Takes full ownership and helps others stay accountable
This person takes initiative to solve problems and remove blockers
*
1 - Rarely takes initiative
2 - Sometimes takes initiative when prompted
3 - Usually takes initiative
4 - Always proactive in solving problems
5 - Drives problem-solving for the entire team
This person handles large, complex projects effectively
*
1 - Struggles with complex projects
2 - Sometimes manages complex work
3 - Usually handles complex projects well
4 - Excels at managing complex projects
5 - Masters complex projects and guides others

This person considers different solutions before deciding
*
1 - Usually goes with the first solution
2 - Sometimes considers alternatives
3 - Regularly evaluates multiple options
4 - Thoroughly analyzes options and explains choices
5 - Finds creative solutions others haven't considered
This person proposes innovative solutions to complex problems
*
1 - Rarely suggests new approaches
2 - Sometimes proposes creative solutions
3 - Regularly offers innovative ideas
4 - Consistently brings fresh perspectives
5 - Leads breakthrough thinking and innovation
This person contributes effectively to brainstorming and design discussions
*
1 - Rarely participates in design discussions
2 - Sometimes contributes to discussions
3 - Regularly adds value to discussions
4 - Often leads productive discussions
5 - Facilitates breakthrough discussions and decisions

This person actively participates in discussions and offers helpful insights
*
1 - Rarely speaks up in discussions
2 - Sometimes participates when prompted
3 - Regularly contributes to discussions
4 - Always adds valuable insights
5 - Drives discussions and helps the team reach decisions
This person helps resolve blockers for teammates
*
1 - Rarely helps with blockers
2 - Sometimes helps when asked
3 - Regularly helps resolve blockers
4 - Proactively identifies and solves blockers
5 - Prevents blockers and improves team workflows
This person helps team members stay aligned and work together
*
1 - Rarely helps with team alignment
2 - Sometimes facilitates team discussions
3 - Regularly promotes team alignment
4 - Actively builds team collaboration
5 - Ensures team unity and shared understanding

This person helps and supports teammates
*
1 - Rarely helps others
2 - Helps when directly asked
3 - Regularly supports teammates
4 - Actively mentors and guides others
5 - Goes above and beyond to develop team members
This person contributes to team growth and learning
*
1 - Rarely contributes to team development
2 - Sometimes shares knowledge
3 - Regularly helps the team grow
4 - Actively drives team learning initiatives
5 - Creates a culture of continuous learning
This person creates a positive, collaborative team environment
*
1 - Sometimes creates friction or tension
2 - Generally maintains neutral interactions
3 - Usually promotes positive collaboration
4 - Actively builds team morale and unity
5 - Creates an exceptionally positive team culture

This person understands what clients need
*
1 - Rarely considers client perspective
2 - Sometimes thinks about client needs
3 - Usually understands client requirements
4 - Anticipates client needs proactively
5 - Deeply understands clients and exceeds expectations
This person delivers work that meets or exceeds client expectations
*
1 - Sometimes falls short of client expectations
2 - Usually meets basic client expectations
3 - Regularly meets client expectations
4 - Often exceeds client expectations
5 - Consistently delivers exceptional results
This person focuses on providing high-quality service
*
1 - Service quality is inconsistent
2 - Usually provides acceptable service
3 - Regularly provides good service
4 - Always provides excellent service
5 - Sets the standard for exceptional service

This person communicates clearly and respectfully, and contributes to a positive, collaborative team culture.
*
1 - Often unclear or creates tension in interactions
2 - Occasionally struggles with clarity or teamwork
3 - Generally professional and collaborative
4 - Consistently clear, respectful, and a positive team influence
5 - Sets a high standard for communication and inspires collaboration
This person is open to feedback, gives it constructively, and takes accountability for their actions and work.
*
1 - Avoids feedback and deflects responsibility
2 - Accepts feedback but struggles to apply it; sometimes avoids accountability
3 - Applies feedback when needed and takes responsibility for tasks
4 - Seeks/gives feedback thoughtfully and owns mistakes
5 - Builds a feedback-driven culture and promotes integrity
This person remains flexible and productive during shifting priorities or team changes.
*
1 - Struggles with change and uncertainty
2 - Occasionally adaptable with support
3 - Adjusts to change with minimal disruption
4 - Adapts quickly and helps others adjust
5 - Leads through change and keeps the team aligned
This person fosters a positive, collaborative work environment.
*
1 - Frequently creates tension or disengagement
2 - Sometimes struggles to work with others
3 - Generally collaborative and respectful
4 - Actively contributes to a healthy team culture
5 - Inspires collaboration and team spirit
This person handles stressful or challenging situations with professionalism and supports others.
*
1 - Often reactive or overwhelmed under stress
2 - Sometimes loses focus in high-pressure situations
3 - Stays calm in most stressful scenarios
4 - Maintains composure and reassures others
5 - A stabilizing force for the team in difficult situations

Key Strengths
*
What are this engineer's top 3 strengths? Please provide specific examples of when you've observed these strengths in action.
Development Opportunities
*
What 1-2 areas would you recommend for this engineer's professional development? Please be constructive and specific.
Have there been any highlights or feedback from the client about this person?
*
```


### QA
```
This person follows and promotes QA/testing best practices
*
1 - Rarely follows standards
2 - Sometimes follows standards
3 - Usually follows standards
4 - Always follows standards and suggests improvements
5 - Sets the standard for the team
This person improves test coverage and quality processes
*
1 - Rarely contributes improvements
2 - Occasionally suggests improvements
3 - Regularly contributes improvements
4 - Actively drives improvements
5 - Leads major improvements that benefit the whole team
This person builds maintainable and scalable test frameworks
*
1 - Rarely creates maintainable solutions
2 - Sometimes creates maintainable solutions
3 - Usually creates maintainable solutions
4 - Always creates well-structured solutions
5 - Creates exemplary solutions that others learn from

This person delivers test plans, cases, and reports on time
*
1 - Often misses deadlines
2 - Sometimes struggles with timelines
3 - Usually meets QA timelines
4 - Always delivers QA assets on time
5 - Keeps the QA process ahead of schedule
This person speaks up when deadlines or QA expectations are unrealistic
*
1 - Rarely raises concerns
2 - Sometimes flags timing risks
3 - Usually manages expectations
4 - Proactively negotiates timing constraints
5 - Helps teams plan realistic timelines
This person balances quality, speed, and testing scope effectively
*
1 - Often sacrifices depth or coverage
2 - Sometimes misjudges scope vs time
3 - Usually finds a good balance
4 - Consistently meets quality and time goals
5 - Sets the benchmark for QA delivery

This person takes full ownership of testing responsibilities without supervision
*
1 - Often needs reminders
2 - Occasionally needs follow-up
3 - Generally reliable on their own
4 - Always reliable and autonomous
5 - Owns tasks and helps others stay on track
This person proactively resolves test environment or blocker issues
*
1 - Avoids or ignores blockers
2 - Sometimes escalates issues
3 - Often resolves problems with help
4 - Proactively removes blockers
5 - Leads QA issue resolution for the team
This person handles complex testing efforts effectively (e.g. regression, automation)
*
1 - Struggles with complex QA work
2 - Sometimes needs support
3 - Handles advanced QA tasks well
4 - Excels in complex QA assignments
5 - Leads end-to-end QA for large projects

This person proposes thoughtful test strategies or root cause analysis
*
1 - Rarely offers insight into issues
2 - Sometimes suggests improvements
3 - Regularly offers QA solutions
4 - Consistently proposes valuable strategies
5 - Guides others in strategic QA decisions
This person finds innovative ways to improve testing or coverage
*
1 - Rarely innovates in QA
2 - Sometimes adapts new ideas
3 - Regularly contributes innovative approaches
4 - Consistently improves QA efficiency
5 - Leads innovation in QA practices
This person contributes effectively to QA planning and retrospectives
*
1 - Rarely joins or contributes
2 - Sometimes provides input
3 - Regularly contributes usefully
4 - Actively drives QA process discussions
5 - Leads structured QA improvements

This person actively participates in QA discussions and team syncs
*
1 - Rarely joins or contributes
2 - Sometimes involved
3 - Regular contributor
4 - Drives QA conversations
5 - Fosters cross-team collaboration
This person helps resolve blockers for other team members
*
1 - Rarely supports teammates
2 - Supports when asked
3 - Often unblocks peers
4 - Proactively assists teammates
5 - Consistently improves team flow
This person promotes shared understanding of quality goals
*
1 - Often works in isolation
2 - Sometimes syncs with others
3 - Keeps team aligned on QA
4 - Builds bridges across roles
5 - Aligns all stakeholders on quality

This person understands and anticipates user-impacting issues
*
1 - Rarely considers user impact
2 - Occasionally flags risks
3 - Frequently raises UX/quality issues
4 - Proactively tests with users in mind
5 - Champions user-focused quality
This person ensures the product meets or exceeds quality expectations
*
1 - Often misses quality issues
2 - Meets basic QA expectations
3 - Delivers expected results
4 - Exceeds QA expectations
5 - Ensures exceptional quality
This person maintains consistency and excellence in testing and reporting
*
1 - Results vary in depth or accuracy
2 - Usually good reports
3 - Consistent and clear QA work
4 - Delivers QA excellence regularly
5 - Sets the standard in QA reporting

This person communicates professionally, clearly, and respectfully in all work situations.
*
1 - Often unprofessional or unclear in communication
2 - Occasionally struggles with tone or clarity
3 - Communicates clearly in most situations
4 - Consistently communicates with clarity and respect
5 - Sets a high standard for professional communication
This person is open to receiving and giving constructive feedback.
*
1 - Avoids or resists feedback
2 - Accepts feedback but struggles to apply it
3 - Open to feedback and applies it when needed
4 - Seeks feedback and gives it thoughtfully
5 - Builds a feedback-driven team culture
This person takes accountability for their actions and work.
*
1 - Often deflects responsibility
2 - Sometimes avoids accountability
3 - Takes responsibility for their own tasks
4 - Owns mistakes and learns from them
5 - Promotes a culture of ownership and integrity
This person shows flexibility and stays productive during changing priorities or team shifts.
*
1 - Struggles with change and uncertainty
2 - Occasionally adaptable with support
3 - Adjusts to change with minimal impact
4 - Adapts quickly and helps others adjust
5 - Leads through change and keeps the team aligned
This person fosters a positive, collaborative work environment.
*
1 - Frequently creates tension or disengagement
2 - Sometimes struggles to work with others
3 - Generally collaborative and respectful
4 - Actively contributes to a healthy team culture
5 - Inspires collaboration and team spirit
This person handles stressful or challenging situations with professionalism and composure.
*
1 - Often reactive or overwhelmed
2 - Sometimes loses focus under stress
3 - Stays calm in most situations
4 - Maintains composure and supports others
5 - A stabilizing force for the team in high-pressure situations
```