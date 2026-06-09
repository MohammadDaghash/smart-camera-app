# Git Workflow

## Branch Strategy

- `main`: stable production-ready versions
- `dev`: active development integration branch
- `feature/*`: feature branches created from `dev`

## One-Time Setup

If `dev` does not exist yet:

```bash
git checkout main
git pull origin main
git checkout -b dev
git push -u origin dev
```

## Creating Feature Branches

Always branch from the latest `dev`:

```bash
git checkout dev
git pull origin dev
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
3. Set base branch to `dev`.
4. Request review from at least one teammate.
5. Merge only after the app still runs locally.

## Releasing To Main

When `dev` is stable:

```bash
git checkout main
git pull origin main
git merge dev
git push origin main
```

For GitHub pull-request flow, open a pull request from `dev` into `main`.

## Pulling Latest Updates

```bash
git checkout dev
git pull origin dev
```

If you are on a feature branch and want the newest development changes:

```bash
git checkout feature/your-branch
git fetch origin
git merge origin/dev
```

## Team Assignments

- Omar: `feature/backend-refactor`, `feature/camera-pipeline`
- Mohammad: `feature/multi-photo-recognition`, `feature/recognition-smoothing`
- Majd: `feature/frontend-dashboard`, `feature/status-overlays`

## Pull Request Checklist

- App starts locally
- `/health` works
- `/camera-test` works
- `/video` works
- No personal face images committed
- No virtual environment files committed
- README/docs updated if workflow changes
