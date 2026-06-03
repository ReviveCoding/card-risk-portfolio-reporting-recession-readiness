.PHONY: run run-small test audit clean

run:
	python -m src.run_pipeline

run-small:
	python -m src.run_pipeline --accounts 500 --months 12

test:
	pytest -q

audit:
	python scripts/audit_project.py

clean:
	python -c "from pathlib import Path; root=Path('.'); [f.unlink() for folder in ['outputs','figures','reports','data/processed','data/synthetic'] for f in (root/folder).glob('*') if f.is_file() and f.name!='README.md']; [p.unlink() for p in [root/'card_risk.db', root/'card_risk.duckdb'] if p.exists()]"
