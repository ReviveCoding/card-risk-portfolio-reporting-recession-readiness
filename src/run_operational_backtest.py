from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(__file__).resolve().parents[1]
DATA_PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"
REPORTS = ROOT / "reports"
FIGURES = ROOT / "figures"


def _ensure_dirs() -> None:
    for p in [OUTPUTS, REPORTS, FIGURES]:
        p.mkdir(parents=True, exist_ok=True)


def _find_col(df: pd.DataFrame, candidates: List[str]) -> str | None:
    lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None


def _load_mart() -> pd.DataFrame:
    candidates = [
        DATA_PROCESSED / "scored_card_risk_mart.csv",
        DATA_PROCESSED / "card_risk_analytics_mart.csv",
    ]
    for path in candidates:
        if path.exists():
            return pd.read_csv(path)
    raise FileNotFoundError(
        "No processed mart found. Run `python -m src.run_pipeline --accounts 10000 --months 24` first."
    )


def _normalize_month(df: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
    month_col = _find_col(
        df,
        [
            "month",
            "report_month",
            "snapshot_month",
            "as_of_month",
            "period",
            "quarter",
        ],
    )
    if month_col is None:
        raise ValueError("Could not find month/reporting-period column.")

    s = df[month_col].astype(str)
    parsed = pd.to_datetime(s, errors="coerce")
    if parsed.notna().mean() >= 0.8:
        df["_op_month"] = parsed.dt.to_period("M").astype(str)
    else:
        # Handles strings like 2024Q1 by mapping to quarter start month.
        q = pd.PeriodIndex(s, freq="Q")
        df["_op_month"] = q.to_timestamp().to_period("M").astype(str)

    return df, "_op_month"


def _dq_to_numeric(x) -> float:
    if pd.isna(x):
        return np.nan
    if isinstance(x, (int, float, np.integer, np.floating)):
        return float(x)
    t = str(x).strip().lower()
    mapping = {
        "current": 0,
        "cur": 0,
        "0": 0,
        "dq0": 0,
        "dq30": 1,
        "30": 1,
        "30dpd": 1,
        "dq60": 2,
        "60": 2,
        "60dpd": 2,
        "dq90": 3,
        "90": 3,
        "90dpd": 3,
        "chargeoff": 4,
        "charge_off": 4,
        "charged_off": 4,
        "co": 4,
    }
    return float(mapping.get(t, np.nan))


def _build_target(df: pd.DataFrame) -> pd.DataFrame:
    existing_target = _find_col(
        df,
        [
            "target",
            "default",
            "default_flag",
            "is_default",
            "next_default",
            "default_next_month",
            "dq30_next_month",
            "next_month_dq30_plus",
            "chargeoff_next_month",
        ],
    )
    if existing_target is not None:
        df["_op_target"] = pd.to_numeric(df[existing_target], errors="coerce").fillna(0).astype(int)
        return df[df["_op_target"].isin([0, 1])].copy()

    acct_col = _find_col(df, ["account_id", "customer_id", "acct_id"])
    dq_col = _find_col(
        df,
        [
            "delinquency_bucket",
            "dq_bucket",
            "dpd_bucket",
            "delinquency_status",
            "current_dq_bucket",
        ],
    )

    if acct_col is not None and dq_col is not None:
        tmp = df.copy()
        tmp["_dq_num"] = tmp[dq_col].map(_dq_to_numeric)
        tmp = tmp.sort_values([acct_col, "_op_month"])
        tmp["_next_dq_num"] = tmp.groupby(acct_col)["_dq_num"].shift(-1)
        tmp["_op_target"] = (tmp["_next_dq_num"] >= 1).astype(float)
        tmp = tmp[tmp["_next_dq_num"].notna()].copy()
        tmp["_op_target"] = tmp["_op_target"].astype(int)
        return tmp

    chargeoff_col = _find_col(df, ["chargeoff_proxy", "charge_off_proxy", "chargeoff_flag"])
    if chargeoff_col is not None:
        df["_op_target"] = (pd.to_numeric(df[chargeoff_col], errors="coerce").fillna(0) > 0).astype(int)
        return df

    dq30_col = _find_col(df, ["dq30_plus_flag", "dq30_plus", "is_dq30_plus"])
    if dq30_col is not None:
        df["_op_target"] = (pd.to_numeric(df[dq30_col], errors="coerce").fillna(0) > 0).astype(int)
        return df

    raise ValueError("Could not infer operational target. Need a default/DQ/chargeoff label column.")


def _feature_columns(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    banned_keywords = [
        "target",
        "default",
        "future",
        "next",
        "label",
        "chargeoff_next",
        "_op_target",
        "_next_dq_num",
    ]
    banned_exact = {
        "_op_month",
        "_dq_num",
        "_next_dq_num",
    }
    id_like = ["account_id", "customer_id", "acct_id"]

    cols = []
    for c in df.columns:
        lc = c.lower()
        if c in banned_exact:
            continue
        if any(k in lc for k in banned_keywords):
            continue
        if any(k == lc for k in id_like):
            continue
        if lc in ["month", "report_month", "snapshot_month", "as_of_month", "period", "quarter"]:
            continue
        cols.append(c)

    numeric_cols = []
    categorical_cols = []
    for c in cols:
        if pd.api.types.is_numeric_dtype(df[c]):
            numeric_cols.append(c)
        else:
            nunique = df[c].nunique(dropna=True)
            if nunique <= 50:
                categorical_cols.append(c)

    return numeric_cols, categorical_cols


def _build_model(numeric_cols: List[str], categorical_cols: List[str]) -> Pipeline:
    numeric_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=True)),
        ]
    )

    pre = ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, numeric_cols),
            ("cat", categorical_pipe, categorical_cols),
        ],
        remainder="drop",
    )

    clf = LogisticRegression(
        max_iter=500,
        class_weight="balanced",
        solver="lbfgs",
        n_jobs=None,
    )

    return Pipeline(steps=[("preprocess", pre), ("model", clf)])


def _safe_metrics(y_true: np.ndarray, score: np.ndarray) -> Dict[str, float]:
    out = {}
    if len(np.unique(y_true)) < 2:
        out["roc_auc"] = np.nan
        out["pr_auc"] = np.nan
    else:
        out["roc_auc"] = roc_auc_score(y_true, score)
        out["pr_auc"] = average_precision_score(y_true, score)
    out["brier"] = brier_score_loss(y_true, np.clip(score, 0, 1))
    return out


def _review_metrics(y_true: np.ndarray, score: np.ndarray, capacity: float) -> Dict[str, float]:
    n = len(y_true)
    k = max(1, int(round(n * capacity)))
    idx = np.argsort(-score)[:k]
    selected = np.zeros(n, dtype=bool)
    selected[idx] = True

    positives = y_true == 1
    selected_pos = int((selected & positives).sum())
    total_pos = int(positives.sum())
    selected_total = int(selected.sum())

    precision = selected_pos / selected_total if selected_total else 0.0
    recall = selected_pos / total_pos if total_pos else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    false_safe = 1 - recall if total_pos else 0.0
    over_review = 1 - precision if selected_total else 0.0

    return {
        "capacity_rate": capacity,
        "review_queue_size": selected_total,
        "review_precision": precision,
        "risk_capture_recall": recall,
        "risk_review_f1": f1,
        "false_safe_rate": false_safe,
        "over_review_rate": over_review,
    }


def _psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    expected = pd.Series(expected).replace([np.inf, -np.inf], np.nan).dropna()
    actual = pd.Series(actual).replace([np.inf, -np.inf], np.nan).dropna()
    if len(expected) < 20 or len(actual) < 20:
        return 0.0

    cuts = np.unique(np.quantile(expected, np.linspace(0, 1, bins + 1)))
    if len(cuts) <= 2:
        return 0.0

    e_counts, _ = np.histogram(expected, bins=cuts)
    a_counts, _ = np.histogram(actual, bins=cuts)
    e_pct = np.maximum(e_counts / max(e_counts.sum(), 1), 1e-6)
    a_pct = np.maximum(a_counts / max(a_counts.sum(), 1), 1e-6)
    return float(np.sum((a_pct - e_pct) * np.log(a_pct / e_pct)))


def _max_feature_psi(train_ref: pd.DataFrame, current: pd.DataFrame, numeric_cols: List[str]) -> float:
    values = []
    for c in numeric_cols[:25]:
        if c in train_ref.columns and c in current.columns:
            values.append(_psi(train_ref[c].to_numpy(), current[c].to_numpy()))
    return float(max(values)) if values else 0.0


def _stress_weight(df: pd.DataFrame) -> np.ndarray:
    util_col = _find_col(df, ["utilization", "utilization_rate", "credit_utilization"])
    bureau_col = _find_col(df, ["bureau_stress_proxy", "bureau_stress", "external_utilization"])
    pay_col = _find_col(df, ["payment_to_balance_ratio", "payment_rate", "payment_ratio"])

    stress = np.ones(len(df))
    if util_col:
        u = pd.to_numeric(df[util_col], errors="coerce").fillna(0)
        stress += 0.40 * (u.rank(pct=True).to_numpy())
    if bureau_col:
        b = pd.to_numeric(df[bureau_col], errors="coerce").fillna(0)
        stress += 0.25 * (b.rank(pct=True).to_numpy())
    if pay_col:
        p = pd.to_numeric(df[pay_col], errors="coerce").fillna(0)
        stress += 0.25 * (1 - p.rank(pct=True).to_numpy())
    return stress


def _fit_score_policy(
    policy: str,
    df: pd.DataFrame,
    months: List[str],
    test_months: List[str],
    numeric_cols: List[str],
    categorical_cols: List[str],
    psi_threshold: float,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    monthly_rows = []
    pred_rows = []

    model = None
    train_ref = None
    last_retrain_i = -999
    retrain_count = 0
    drift_trigger_count = 0

    for i, m in enumerate(test_months):
        current = df[df["_op_month"] == m].copy()
        train = df[df["_op_month"] < m].copy()

        retrain = False
        reason = "reuse"

        if model is None:
            retrain = True
            reason = "initial_train"
        elif policy == "quarterly_retrain" and (i - last_retrain_i) >= 3:
            retrain = True
            reason = "quarterly_schedule"
        elif policy == "drift_triggered":
            current_psi = _max_feature_psi(train_ref, current, numeric_cols) if train_ref is not None else 0.0
            if current_psi >= psi_threshold:
                retrain = True
                reason = f"psi_{current_psi:.3f}"
                drift_trigger_count += 1

        current_psi_for_log = _max_feature_psi(train_ref, current, numeric_cols) if train_ref is not None else 0.0

        if retrain:
            if train["_op_target"].nunique() < 2:
                continue
            model = _build_model(numeric_cols, categorical_cols)
            model.fit(train[numeric_cols + categorical_cols], train["_op_target"])
            train_ref = train.copy()
            last_retrain_i = i
            retrain_count += 1

        score = model.predict_proba(current[numeric_cols + categorical_cols])[:, 1]
        y = current["_op_target"].to_numpy()

        metrics = _safe_metrics(y, score)
        monthly_rows.append(
            {
                "policy": policy,
                "month": m,
                "n_accounts": len(current),
                "event_rate": float(np.mean(y)),
                "retrained": retrain,
                "retrain_reason": reason,
                "max_feature_psi": current_psi_for_log,
                "retrain_count_to_date": retrain_count,
                "drift_trigger_count_to_date": drift_trigger_count,
                **metrics,
            }
        )

        tmp = current[["_op_month", "_op_target"]].copy()
        tmp["policy"] = policy
        tmp["score"] = score
        tmp["stress_weighted_score"] = score * _stress_weight(current)
        pred_rows.append(tmp)

    return pd.DataFrame(monthly_rows), pd.concat(pred_rows, ignore_index=True)


def run_operational_backtest(train_months: int, test_months: int, psi_threshold: float) -> None:
    _ensure_dirs()

    df = _load_mart()
    df, month_col = _normalize_month(df)
    df = _build_target(df)
    df = df.sort_values(month_col).reset_index(drop=True)

    months = sorted(df[month_col].unique())
    if len(months) < train_months + test_months:
        raise ValueError(
            f"Need at least {train_months + test_months} months, found {len(months)}."
        )

    selected_months = months[-(train_months + test_months):]
    test_ms = selected_months[-test_months:]
    df = df[df[month_col].isin(selected_months)].copy()

    numeric_cols, categorical_cols = _feature_columns(df)
    if not numeric_cols and not categorical_cols:
        raise ValueError("No usable feature columns found.")

    policies = ["static_model", "quarterly_retrain", "drift_triggered"]
    all_monthly = []
    all_preds = []

    for policy in policies:
        monthly, preds = _fit_score_policy(
            policy=policy,
            df=df,
            months=selected_months,
            test_months=test_ms,
            numeric_cols=numeric_cols,
            categorical_cols=categorical_cols,
            psi_threshold=psi_threshold,
        )
        all_monthly.append(monthly)
        all_preds.append(preds)

    monthly_df = pd.concat(all_monthly, ignore_index=True)
    preds_df = pd.concat(all_preds, ignore_index=True)

    review_rows = []
    for policy in policies:
        part = preds_df[preds_df["policy"] == policy].copy()
        y = part["_op_target"].to_numpy()
        for score_col in ["score", "stress_weighted_score"]:
            for cap in [0.02, 0.05, 0.10, 0.15, 0.20, 0.30]:
                m = _review_metrics(y, part[score_col].to_numpy(), cap)
                review_rows.append(
                    {
                        "policy": policy,
                        "score_policy": score_col,
                        **m,
                    }
                )

    review_df = pd.DataFrame(review_rows)

    summary = (
        monthly_df.groupby("policy")
        .agg(
            months_tested=("month", "nunique"),
            avg_event_rate=("event_rate", "mean"),
            avg_roc_auc=("roc_auc", "mean"),
            avg_pr_auc=("pr_auc", "mean"),
            avg_brier=("brier", "mean"),
            retrain_events=("retrained", "sum"),
            max_feature_psi=("max_feature_psi", "max"),
        )
        .reset_index()
    )

    monthly_df.to_csv(OUTPUTS / "operational_backtest_monthly.csv", index=False)
    summary.to_csv(OUTPUTS / "operational_retraining_summary.csv", index=False)
    review_df.to_csv(OUTPUTS / "operational_review_policy_summary.csv", index=False)
    preds_df.to_csv(OUTPUTS / "operational_backtest_predictions.csv", index=False)

    # Figures
    plt.figure(figsize=(9, 5))
    for policy in policies:
        p = monthly_df[monthly_df["policy"] == policy]
        plt.plot(p["month"], p["pr_auc"], marker="o", label=policy)
    plt.xticks(rotation=45)
    plt.ylabel("Monthly PR-AUC")
    plt.title("Out-of-Time Backtest: Monthly PR-AUC")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURES / "operational_backtest_pr_auc.png", dpi=160)
    plt.close()

    plt.figure(figsize=(9, 5))
    plot_df = review_df[(review_df["score_policy"] == "score") & (review_df["capacity_rate"].isin([0.05, 0.10, 0.15, 0.20]))]
    for policy in policies:
        p = plot_df[plot_df["policy"] == policy]
        plt.plot(p["capacity_rate"], p["risk_review_f1"], marker="o", label=policy)
    plt.xlabel("Review capacity rate")
    plt.ylabel("Risk-review F1")
    plt.title("Review-Capacity Policy Simulation")
    plt.legend()
    plt.tight_layout()
    plt.savefig(FIGURES / "operational_review_policy_f1.png", dpi=160)
    plt.close()

    report = []
    report.append("# Operational Backtest Report\n")
    report.append(
        f"Backtest design: train window = {train_months} months, test window = {test_months} months. "
        "The experiment compares static, quarterly retraining, and drift-triggered retraining policies under time-ordered operational validation.\n"
    )
    report.append("## Retraining Policy Summary\n")
    report.append(summary.round(4).to_markdown(index=False))
    report.append("\n\n## Review Capacity Policy Summary\n")
    show_review = review_df[
        (review_df["score_policy"] == "score")
        & (review_df["capacity_rate"].isin([0.05, 0.10, 0.15, 0.20]))
    ]
    report.append(show_review.round(4).to_markdown(index=False))
    report.append(
        "\n\n## Claim Boundary\n"
        "This is an offline operational simulation using synthetic account-level data and public benchmark-aligned reporting artifacts. "
        "It is not a production bank deployment, not real bureau microdata, and not proprietary cardholder data.\n"
    )
    (REPORTS / "operational_backtest_report.md").write_text("\n".join(report), encoding="utf-8")

    print("Operational backtest complete.")
    print(f"Saved {OUTPUTS / 'operational_backtest_monthly.csv'}")
    print(f"Saved {OUTPUTS / 'operational_retraining_summary.csv'}")
    print(f"Saved {OUTPUTS / 'operational_review_policy_summary.csv'}")
    print(f"Saved {REPORTS / 'operational_backtest_report.md'}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-months", type=int, default=18)
    parser.add_argument("--test-months", type=int, default=6)
    parser.add_argument("--psi-threshold", type=float, default=0.20)
    args = parser.parse_args()
    run_operational_backtest(
        train_months=args.train_months,
        test_months=args.test_months,
        psi_threshold=args.psi_threshold,
    )


if __name__ == "__main__":
    main()
