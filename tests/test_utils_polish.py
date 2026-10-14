"""Boundary checks for credit-risk reporting helper functions."""

import numpy as np
import pytest

from src.utils import ece_score, top_capture


def test_top_capture_empty_arrays_returns_no_observed_capture():
    assert top_capture(np.array([]), np.array([])) == (0.0, 0.0)


def test_top_capture_nonempty_order_and_capture_are_preserved():
    precision, capture = top_capture([1, 0, 1, 0], [0.9, 0.7, 0.2, 0.1], rate=0.5)
    assert precision == pytest.approx(0.5)
    assert capture == pytest.approx(0.5)


def test_calibration_error_is_zero_for_perfectly_calibrated_binary_scores():
    assert ece_score([0, 1], [0, 1], bins=2) == pytest.approx(0.0)
