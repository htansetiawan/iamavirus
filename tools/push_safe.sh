#!/bin/bash
# Push main without ever rejecting or overwriting a commit the human made from
# the phone (chatroom/msg_NNNN.md). Fetches first; pushes if origin/main is
# already contained in HEAD; otherwise rebases our commits onto origin/main,
# stashing and restoring any uncommitted work of the other agent around it.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
git fetch -q origin
if git merge-base --is-ancestor origin/main HEAD; then
  git push -q origin main
else
  git rebase -q --autostash origin/main
  git push -q origin main
fi
# mirror: henryatharvard/iamavirus (private) gets the same main; its token is
# passed to this one push so the active gh account is never switched
if git remote get-url harvard >/dev/null 2>&1; then
  GH_TOKEN=$(gh auth token --user henryatharvard 2>/dev/null) git push -q harvard main 2>/dev/null \
    || echo "push_safe: mirror push to harvard failed" >&2
fi
git log --oneline -1 | cat
