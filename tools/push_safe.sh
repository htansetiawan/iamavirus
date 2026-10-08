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
git log --oneline -1 | cat
