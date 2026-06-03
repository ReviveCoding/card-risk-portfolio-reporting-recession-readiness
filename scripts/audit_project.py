from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    'README.md', 'Makefile', 'requirements.txt', '.github/workflows/ci.yml',
    'reports/executive_risk_summary.md', 'reports/release_decision.md',
    'reports/reconciliation_governance_report.md', 'reports/responsible_use_and_fair_lending_boundary.md',
    'outputs/sql_python_reconciliation.csv', 'outputs/review_capacity_sensitivity.csv',
    'outputs/scenario_sensitivity_grid.csv', 'outputs/source_inventory.csv',
    'figures/review_capacity_sensitivity.png', 'figures/scenario_sensitivity_grid.png',
]
FORBIDDEN_DIR_PARTS = {'__pycache__', '.pytest_cache'}
MAX_FILE_MB = 25


def main() -> int:
    missing = [p for p in REQUIRED_FILES if not (ROOT / p).exists()]
    if missing:
        print('Missing required artifacts:')
        for p in missing:
            print(' -', p)
        return 1
    bad_dirs = [p for p in ROOT.rglob('*') if p.is_dir() and p.name in FORBIDDEN_DIR_PARTS]
    if bad_dirs:
        print('Cache directories detected locally and ignored for audit:')
        for p in bad_dirs:
            print(' -', p.relative_to(ROOT))
    large = [p for p in ROOT.rglob('*') if p.is_file() and p.stat().st_size > MAX_FILE_MB * 1024 * 1024]
    if large:
        print(f'Files larger than {MAX_FILE_MB} MB:')
        for p in large:
            print(' -', p.relative_to(ROOT), p.stat().st_size)
        return 1
    print('Project audit PASS: required artifacts present; generated cache directories are ignored; no oversized files.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
