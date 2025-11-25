# Repository Rename Guide: code-graph-mcp → codenav

This guide provides step-by-step instructions for completing the migration of `ajacobm/code-graph-mcp` to `ajacobm/codenav`.

## Current Status

✅ **Code Migration Complete**
- Package renamed: `src/code_graph_mcp/` → `src/codenav/`
- All imports updated to use `from codenav import ...`
- Entry points updated: `code-graph-mcp` → `codenav`
- Environment variables updated: `CODEGRAPHMCP_*` → `CODENAV_*`
- Docker configurations updated
- Documentation updated

## What Remains (Manual Steps Required)

The following operations **must be performed by the repository owner** through the GitHub web interface. These cannot be automated by Copilot.

---

## Step 1: Merge the PR Chain to Main

There's a chain of PRs that need to be merged in order:

### 1.1 Merge PR #3: "Migrate code-graph-mcp to CodeNavigator"
- **URL**: https://github.com/ajacobm/code-graph-mcp/pull/3
- **Branch**: `copilot/migrate-to-codenav` → `copilot/migrate-code-graph-mcp-to-codenav`
- **Status**: Open
- **Action**: Review and merge this PR first

### 1.2 Merge PR #4: "Change repository name to codenav"  
- **URL**: https://github.com/ajacobm/code-graph-mcp/pull/4
- **Branch**: `copilot/rename-repository-to-codenav` → `copilot/migrate-to-codenav`
- **Status**: Open (Draft)
- **Action**: After PR #3 is merged, merge this PR

### 1.3 Update main Branch
After merging PRs #3 and #4, you need to get these changes into `main`. You have two options:

**Option A: Create a PR from the merged branch to main**
1. Create a new PR: `copilot/migrate-to-codenav` → `main`
2. Review and merge

**Option B: Fast-forward main locally (if you prefer)**
```bash
git fetch origin
git checkout main
git merge origin/copilot/migrate-to-codenav
git push origin main
```

---

## Step 2: Rename the Repository on GitHub

1. Go to: https://github.com/ajacobm/code-graph-mcp/settings
2. Scroll to **"Repository name"** section
3. Change the name from `code-graph-mcp` to `codenav`
4. Click **"Rename"**

### What Happens When You Rename:
- ✅ All git history is preserved
- ✅ All existing PRs are preserved (they update automatically)
- ✅ All issues are preserved
- ✅ All commits are preserved
- ✅ GitHub automatically redirects `ajacobm/code-graph-mcp` → `ajacobm/codenav`
- ✅ Clone URLs update automatically
- ⚠️ You may need to update local git remotes on your machines:
  ```bash
  git remote set-url origin https://github.com/ajacobm/codenav.git
  ```

---

## Step 3: Remove the Fork Relationship

Since the project has diverged from upstream and you want it to be a standalone repository:

1. Go to: https://github.com/ajacobm/codenav/settings (after renaming)
2. Scroll down to the **"Danger Zone"** section
3. Look for **"Detach fork"** or **"This is a fork"** section
4. Click the option to detach/remove fork relationship

### Alternative: Contact GitHub Support
If the detach option is not available:
1. Go to https://support.github.com/contact
2. Request to "detach fork" for the repository
3. They typically process these requests quickly

### What Happens When You Detach:
- ✅ Your repository becomes standalone
- ✅ All your commits, branches, PRs, and issues are preserved
- ✅ You lose the link to the upstream repository (which you don't need)
- ❌ You lose the ability to create PRs to upstream (not needed since diverged)

---

## Step 4: Local Git Cleanup (Optional)

After the rename, update your local repositories:

```bash
# Update remote URL
git remote set-url origin https://github.com/ajacobm/codenav.git

# Remove upstream remote if it exists
git remote remove upstream

# Verify remotes
git remote -v
```

---

## Step 5: Post-Rename Verification

After completing all steps, verify:

1. **Repository accessible**: Visit https://github.com/ajacobm/codenav
2. **Old URL redirects**: Visit https://github.com/ajacobm/code-graph-mcp (should redirect)
3. **PRs preserved**: Check that all PRs are still accessible
4. **No fork badge**: The repository should not show "forked from" badge
5. **Clone works**: `git clone https://github.com/ajacobm/codenav.git`

---

## Step 6: Clean Up Old Branches (Optional)

After everything is merged and verified, you can delete the migration branches:

```bash
# Delete remote branches
git push origin --delete copilot/migrate-to-codenav
git push origin --delete copilot/migrate-code-graph-mcp-to-codenav
git push origin --delete copilot/rename-repository-to-codenav

# Delete local branches
git branch -d copilot/migrate-to-codenav
git branch -d copilot/migrate-code-graph-mcp-to-codenav
git branch -d copilot/rename-repository-to-codenav
```

---

## Summary of Actions

| Step | Action | Who | Status |
|------|--------|-----|--------|
| 1 | Merge PR #3 | Repository Owner | 🔲 Pending |
| 2 | Merge PR #4 | Repository Owner | 🔲 Pending |
| 3 | Merge to main | Repository Owner | 🔲 Pending |
| 4 | Rename repository | Repository Owner (GitHub Settings) | 🔲 Pending |
| 5 | Detach fork | Repository Owner (GitHub Settings/Support) | 🔲 Pending |
| 6 | Update local remotes | Developer | 🔲 Pending |
| 7 | Verify everything works | Developer | 🔲 Pending |
| 8 | Clean up old branches | Optional | 🔲 Pending |

---

## Expected Final State

After completing all steps:

- **Repository URL**: `https://github.com/ajacobm/codenav`
- **Package name**: `codenav`
- **CLI command**: `codenav`
- **Fork status**: Not a fork (standalone repository)
- **All history**: Preserved
- **All PRs/Issues**: Preserved

Refreshing your GitHub homepage at https://github.com/ajacobm should show `codenav` as one of your repositories.
