# README

Work notes.

## GIT

### Creating subtree

```
git remote add work-notes git@github.com:luis-mamani-wp/work-notes.git
git subtree push --prefix=ioet work-notes main 
# add a remote key
git config remote.work-notes.sshCommand 'ssh -i /home/ml/.ssh/ioet_wp -o IdentitiesOnly=yes'
```

### On personal device

```
# PUSH
cd ~/notes
git add -A
git commit -m "..."
git push                                              # personal backup
git subtree push --prefix=ioet work-notes main        # work repo

# PULL: bring work-device commits back into ioet/
git subtree pull --prefix=ioet work-notes main --squash
```

### On work device

```
cd ~/notes                 # or wherever you cloned work-notes
git add -A
git commit -m "..."
git pull                   # in case parent pushed
git push                   # to work-notes
```