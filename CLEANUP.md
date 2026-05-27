# Automated cleanup and auditing steps

These commands help locate unused code, unused dependencies, and other cleanup tasks. Run them locally in the repository root.

Python (recommended dev tools):

```bash
# create a virtual env and activate it
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install vulture autoflake isort black flake8

# Find dead Python code
vulture backend -o vulture-report.txt

# Remove unused imports and format
autoflake --remove-all-unused-imports --recursive --in-place backend
isort backend
black backend

# Run tests
pytest backend
```

Node / Frontend:

```bash
cd frontend
npm ci
npm install -g depcheck

# detect unused deps (manual review required)
depcheck

# fix lint issues automatically (if desired)
npm run lint -- --fix

# build to ensure no regressions
npm run build
```

Dependency audit suggestions:
- Use `pipdeptree` to inspect Python dependency graph.
- Use `npm prune` and `npm dedupe` to reduce duplicates.
- Add `safety` or `pip-audit` to CI for Python vulnerability scanning.

Notes:
- Automated removals should be code-reviewed before committing.
- Some dev-only packages are intentionally present for testing or CI.
