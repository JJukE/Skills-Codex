---
name: git-sync
description: Pull, commit, and push repository changes to a configured remote using the repository's COMMIT_CONVENTION.md. Use when the user asks Codex to pull, add/stage, commit, and push changes; sync local work to a remote repository; or create a commit according to the local commit convention before pushing. Also use when the user asks to include specific changes or deletions in that workflow.
---

# Git Sync

## Workflow

Use this skill to sync local repository changes to a remote with a convention-compliant commit.

### 1. Preflight Checks

Run these checks once at the start of the task:

1. Confirm the current directory is inside a Git repository:

   ```bash
   git rev-parse --show-toplevel
   ```

2. Confirm a remote repository is configured:

   ```bash
   git remote -v
   ```

   If there is no configured remote, inform the user that no remote repository is specified and stop before pull, commit, or push.

3. Confirm the current branch:

   ```bash
   git branch --show-current
   ```

   If the branch is detached or empty, inform the user and stop unless they explicitly provide a target branch.

4. Confirm `COMMIT_CONVENTION.md` exists at the repository root:

   ```bash
   test -f COMMIT_CONVENTION.md
   ```

   If it does not exist, inform the user that the commit convention file is missing and stop before committing.

5. Read `COMMIT_CONVENTION.md` before choosing a commit message.

Only repeat these checks if the repository state changes materially during the task, such as changing directories, switching branches, or resolving a failed pull.

### 2. Inspect Local Changes

Inspect the worktree before pulling or staging:

```bash
git status --short
```

Identify which changes are requested by the user. If the user explicitly says to include all changes or includes deletions, stage those changes. If the requested scope is ambiguous and there are unrelated-looking changes, ask before staging them.

### 3. Pull Safely

Pull from the configured remote before committing.

Use the current branch and its upstream when available. If no upstream is configured, use `origin` and the current branch only when `origin` exists. If neither is clear, inform the user that the pull target is not specified and stop.

If the worktree has local changes, temporarily stash them before pulling:

```bash
git stash push -u -m codex-temp-before-convention-sync
git pull --rebase <remote> <branch>
git stash pop
```

If pulling, rebasing, or applying the stash is blocked by conflicts, authentication, missing upstream, network failure, or another Git error, inform the user with the relevant error and stop. Do not discard local changes to resolve the blockage.

### 4. Stage Requested Changes

Stage only the requested changes:

```bash
git add <paths>
```

Use `git add -A` only when the user clearly wants all changes included, including deletions.

Verify the staged set:

```bash
git diff --cached --stat
git status --short
```

If the staged set does not match the user's requested scope, fix staging before committing.

### 5. Commit According to the Convention

Choose the commit type and message from `COMMIT_CONVENTION.md`. Follow the exact format required there.

For this repository, the convention is typically:

```text
[type] short description
```

Use a concise imperative description. Examples:

```text
[docs] add git sync skill
[feat] add experiment baseline skill
[fix] correct wiki capture workflow
```

If no files are staged, do not create an empty commit unless the user explicitly asks for one. Inform the user that there are no staged changes to commit.

Run:

```bash
git commit -m "[type] short description"
```

If the commit is blocked by hooks, missing Git identity, conflicts, or any other reason, inform the user and stop. Do not bypass hooks or use override flags unless the user explicitly instructs it after seeing the blockage.

### 6. Push Without Force

Push the current branch to the configured remote:

```bash
git push <remote> <branch>
```

Never use `--force`, `--force-with-lease`, or any force-push equivalent.

If push is blocked because the remote has new commits, authentication fails, branch protection rejects the push, hooks fail, or another error occurs, inform the user and stop. Do not try to override repository protections.

### 7. Final Report

After a successful push, report:

- Whether the pull was up to date or changed the branch
- The commit hash and commit message
- The remote and branch pushed
- Whether the final worktree is clean

If any step was blocked, report the blocking reason and the repository state without attempting destructive recovery.
