# Model Card and Use Boundary

## Intended use
Offline card-risk reporting and recession-readiness analytics demonstration for public/synthetic data.

## Not intended for
Production credit decisioning, adverse action, customer-level underwriting, bank regulatory submission, or use with real bureau/customer records.

## Data
Public aggregate benchmarks are used for plausibility only. Synthetic account-level records simulate portfolio reporting workflows.

## Models
Vanilla baselines include logistic regression, calibrated logistic regression, random forest, static roll-rate, and segment-conditioned roll-rate. Specialty layers include Credit Health Timestep, validation-shrunk residual correction, and asymmetric risk-boundary routing.

## Monitoring
Drift is monitored with PSI; score and segment stability are summarized in `monitoring_drift_report.md` and `backtesting_validation_report.md`.

## Latest data window
Latest reporting month in this run: 2026-01.
