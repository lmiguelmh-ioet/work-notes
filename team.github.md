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
git show vstage28 --quiet

# create annotated tag with empty description
git tag -a vstage31 -m ""
git push origin vstage31

# remove tag
git tag -d vstage26
```

