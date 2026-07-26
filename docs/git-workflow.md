# Git Workflow

## Branch Strategy

- `main`: primary protected branch
- `feature/<feature-name>`: feature branches created from `main`

## Creating Feature Branches

Always branch from the latest `main`:

```bash
git checkout main
git pull origin main
git checkout -b feature/multi-photo-recognition
```

Other examples:

```bash
git checkout -b feature/frontend-dashboard
git checkout -b feature/backend-refactor
```

## Daily Development

```bash
git status
git add .
git commit -m "Short clear commit message"
git push -u origin feature/branch-name
```

## Opening Pull Requests

1. Push your feature branch.
2. Open a pull request on GitHub.
3. Set base branch to `main`.
4. Request review from at least one teammate.
5. Merge only after the app still runs locally.

## Main Branch Protection

The `main` branch should be protected in GitHub:

- Direct pushes to `main` are blocked.
- Pull requests are required before merging.
- At least one approving review is required.

## Pulling Latest Updates

```bash
git checkout main
git pull origin main
```

If you are on a feature branch and want the newest main changes:

```bash
git checkout feature/your-branch
git fetch origin
git merge origin/main
```

## Pull Request Checklist

- App starts locally
- `/health` works
- `/camera-test` works
- `/video` works
- GitHub Actions CI passes
- No personal face images committed
- No virtual environment files committed
- README/docs updated if workflow changes

## Continuous Integration

GitHub Actions runs on pushes and pull requests for `main` and `dev`.

The CI workflow checks:

- backend tests with `pytest`
- frontend inline JavaScript syntax with `node --check`
- tracked files stay under 1000 lines

If CI fails, fix the failing check before merging.
