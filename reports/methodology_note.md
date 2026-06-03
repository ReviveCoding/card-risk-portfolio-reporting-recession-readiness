# Methodology Note

## Intended use

Offline portfolio analytics demonstration for card-risk reporting, recession-readiness analysis, and model-validation style documentation.

## Data boundary

Public aggregate datasets are used for market context and benchmark alignment. Synthetic account-level data simulate internal-style card reporting, bureau-tradeline-style proxy integration, cross-LOB segmentation, and recession scenario analysis. No proprietary bank, real customer, or real bureau microdata are used.

## Modeling boundary

Vanilla baselines include logistic regression, calibrated logistic regression, HistGradientBoosting, static roll-rate, and segment-conditioned roll-rate. Specialty enhancements include Credit Health Timestep, residual bias correction, and asymmetric risk-boundary review routing.

## Limitations

The synthetic portfolio does not represent an actual bank portfolio. Public aggregate data cannot validate account-level behavior. The UCI benchmark is a public Taiwan default dataset and should not be interpreted as a U.S. consumer-bank production portfolio.
