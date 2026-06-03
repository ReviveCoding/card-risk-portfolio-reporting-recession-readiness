# Project Audit Summary

This repository is designed as an offline, public/synthetic, SQL-first card-risk analytics project. It intentionally avoids claims about proprietary bank data, real bureau microdata, customer-level cardholder records, production deployment, or formal regulatory submission.

## Core evidence

- SQL reporting pack for portfolio KPIs, roll rates, vintage/cohort, segment risk, bureau-style overlays, cross-LOB analysis, benchmark alignment, and Tableau-ready extracts.
- Public benchmark alignment using sample/fallback FRED and Philadelphia Fed style aggregate references.
- Vanilla baselines and specialty-enhanced ablations for calibrated scoring, residual-bias diagnostics, Credit Health Timestep, and asymmetric risk-boundary routing.
- Data validation, reporting controls, monitoring/drift reports, model card, methodology note, and release gate.
- SQL/Python reconciliation, source inventory, responsible-use boundary note, artifact manifest, review-capacity sensitivity, and scenario-sensitivity robustness checks.

## Latest verified local run

- `make run`: passed.
- `make test`: 30 tests passed.
- `make audit`: passed.
- Release gate: PASS.
- Small-data smoke validation: 500 accounts x 12 months, PASS.

## Local/GitHub runnable status

The project is runnable without internet access because sample/fallback public data are included. Optional ingestion scripts can be extended to use current public downloads. The CI workflow runs `make run`, `make test`, and `make audit` on Python 3.11.

## Repository hygiene

- `.gitignore` excludes local Python caches, virtual environments, local databases, and temporary logs.
- Generated database files are not required for GitHub; `make run` recreates local artifacts.
- Outputs and reports are intentionally included as sample evidence for portfolio review and interview discussion.
