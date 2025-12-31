# GitHub Actions Setup Instructions

Since the current Git token doesn't have `workflow` scope, you'll need to manually create the workflow files on GitHub or update your token permissions.

## Option 1: Create Workflows on GitHub (Recommended)

1. Go to https://github.com/zsb3/sra-accession-search
2. Click "Add file" → "Create new file"
3. Name it `.github/workflows/test.yml`
4. Copy the contents from `.github/workflows/test.yml` in this repository
5. Commit directly to main branch
6. Repeat for `.github/workflows/release.yml`

## Option 2: Update Git Token

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Edit your token or create a new one
3. Enable the `workflow` scope checkbox
4. Update your local Git credentials
5. Run: `git push origin main`

## Option 3: Manual Push Command

If you have SSH access configured:

```bash
# Add SSH remote (if not already done)
git remote add ssh git@github.com:zsb3/sra-accession-search.git

# Push using SSH
git push ssh main
```

## Verifying Workflows

Once workflows are pushed:

1. Go to https://github.com/zsb3/sra-accession-search/actions
2. You should see the "Tests" workflow running
3. Check that all Python versions (3.10, 3.11, 3.12) pass
4. Coverage report should show ~90% coverage

## Optional: Configure Secrets for Integration Tests

If you want to enable integration tests (optional):

1. Go to repository Settings → Secrets and variables → Actions
2. Add secrets:
   - `NCBI_EMAIL`: Your NCBI email
   - `NCBI_API_KEY`: Your NCBI API key
3. Integration tests will automatically run when these are configured

## Workflow Files Location

The workflow files are ready in your local repository:
- `.github/workflows/test.yml` - Main CI workflow
- `.github/workflows/release.yml` - Release automation

Current status: **Committed locally, pending push to GitHub**
