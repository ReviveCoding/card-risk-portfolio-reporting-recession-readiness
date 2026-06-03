from __future__ import annotations
from pathlib import Path
import yaml
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def load_yaml(rel_path: str) -> dict:
    with open(ROOT / rel_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def ensure_dirs() -> None:
    for p in ['data/public_raw','data/synthetic','data/processed','outputs','figures','reports']:
        (ROOT / p).mkdir(parents=True, exist_ok=True)


def month_range(start_month: str, periods: int) -> pd.PeriodIndex:
    return pd.period_range(start=start_month, periods=periods, freq='M')


def month_to_quarter(month: str) -> str:
    p = pd.Period(month, freq='M')
    return f"{p.year}Q{p.quarter}"


def save_csv(df: pd.DataFrame, rel_path: str) -> None:
    path = ROOT / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def read_csv(rel_path: str) -> pd.DataFrame:
    return pd.read_csv(ROOT / rel_path)


def ece_score(y_true, y_prob, bins: int = 10) -> float:
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    edges = np.linspace(0, 1, bins + 1)
    ece = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (y_prob >= lo) & (y_prob < hi if hi < 1 else y_prob <= hi)
        if mask.sum() == 0:
            continue
        ece += mask.mean() * abs(y_true[mask].mean() - y_prob[mask].mean())
    return float(ece)


def top_capture(y_true, y_prob, rate: float = 0.10) -> tuple[float, float]:
    y_true = np.asarray(y_true)
    y_prob = np.asarray(y_prob)
    k = max(1, int(len(y_prob) * rate))
    idx = np.argsort(-y_prob)[:k]
    precision = float(y_true[idx].mean()) if k else 0.0
    capture = float(y_true[idx].sum() / max(y_true.sum(), 1))
    return precision, capture
