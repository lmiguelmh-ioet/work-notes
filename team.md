## Dev Lead talks
- Do not write a lot of comments
	- when code reviewing people read comments, and that can be missleading
- SOLID
	- single responsability

## Note system: why
- Help you actually execute (personal productivity)
- Feed alignment artifacts into async channels (Jira/Slack/email/standup)
- Accumulate evidence for leveling (staff/lead skills)
- Senior = output    
- Staff = output + decisions + shaping + de-risking
- From `Done → Standup`
- From `Done → Jira comment`
- From `Decisions → Jira ticket(s)` if architectural/product
- From `Risks → Jira issues` if externalized
```
# {{date:YYYY-MM-DD}}
## Plan
- _top 1-2 priorities (sync with JIRA)_
- _add dependencies and risks to watch_

## Done (append during day)
- _should feed JIRA and stand-up updates_

## Decisions / Notes / Context
- _design choices, trade-offs, coordination needed, questions asked/answered_

## Meetings / Async Threads
### Stand Up
- _Who + Topic_
- _Summary (1–3 bullets)_
- _Decision/**Outcome**_
- _Next steps/Owners_

## Tasks (carry forward)
- _map to JIRA issue keys if possible_

## Insights/Ideas
- _for weekly review and future proposals_


---
# Weekly Review: Week {{date:YYYY-MM}}
## Outcomes (Impact)
- _Jira refs if helpful (for traceability)_

## Decisions & Tradeoffs
- _architectural, product, prioritization, tech debt vs velocity calls_

## Risks & Gaps (leadership signal)
- _blocks, unowned surfaces, future drag, missing context_

## Next Week Focus
- _priorities, dependencies, alignment topics_

## Insights/Ideas Summary
- _summary of insights_
```

## Github
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
git show vstage22 --quiet

# create annotated tag with empty description
git tag -a vstage26 -m ""
git push origin vstage26

# remove tag
git tag -d vstage26
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
## Scrum meet
- scrum moderator is announced on Monday:
	- ![](assets/Pasted%20image%2020260120110646.png)
		- On Call Slack/Meetings - is the one that leads if moderator is not
- Structure
	- Team Updates
		- https://warbyparker.atlassian.net/jira/software/c/projects/OTCM/boards/771
		- (1) Rocio and (2) Fabiola and (3) Kio no están en el board de Jira
		- (4) Astrid and (5) Emilio
		- "Hello, ??? do you have any updates regarding your ticket?"
		- "Hello, ??? do you have any updates?"
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
