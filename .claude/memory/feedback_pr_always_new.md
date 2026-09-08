---
name: feedback_pr_always_new
description: pr-generator must always create a new PR for new commits, never update an existing one unless explicitly told to
metadata:
  type: feedback
---

Always create a new GitHub PR for each new batch of commits. Do not update or reuse an existing PR.

**Why:** User preference — each PR should represent a distinct unit of work. Reusing PRs conflates separate changes.

**How to apply:** When running pr-generator, always call `mcp__github__create_pull_request` to open a new PR, regardless of whether a PR already exists on the branch. Only update an existing PR if the user explicitly says to (e.g., "update PR #2" or "add to the existing PR").
