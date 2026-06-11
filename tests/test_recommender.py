"""
test_recommender.py
====================
Unit tests for the mutual fund recommender system.
"""

import pytest
import pandas as pd
from scripts.recommender import (
    RISK_MAP,
    _demo_recommend,
)


class TestRiskMap:
    def test_all_risk_levels_covered(self):
        """All three risk levels (Low, Moderate, High) should be mapped."""
        assert "Low" in RISK_MAP
        assert "Moderate" in RISK_MAP
        assert "High" in RISK_MAP

    def test_risk_map_values_are_lists(self):
        """Each risk level should map to a list of risk grades."""
        for key, value in RISK_MAP.items():
            assert isinstance(value, list)
            assert len(value) > 0

    def test_low_risk_grades(self):
        """Low risk should map to conservative grades."""
        grades = RISK_MAP["Low"]
        assert "Low" in grades
        assert "Very High" not in grades

    def test_high_risk_grades(self):
        """High risk should include aggressive grades."""
        grades = RISK_MAP["High"]
        assert "Very High" in grades or "High" in grades


class TestDemoRecommend:
    def test_returns_dataframe(self):
        """Demo recommender should return a DataFrame."""
        result = _demo_recommend("Low", 3)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3

    def test_moderate_recommendations(self):
        """Moderate risk should return valid recommendations."""
        result = _demo_recommend("Moderate", 3)
        assert len(result) == 3
        assert "scheme_name" in result.columns
        assert "sharpe_ratio" in result.columns

    def test_high_recommendations(self):
        """High risk should return valid recommendations."""
        result = _demo_recommend("High", 3)
        assert len(result) == 3

    def test_top_n_respected(self):
        """Should return at most top_n recommendations (demo has 3 items max)."""
        # Demo data always has exactly 3 entries per risk level
        result_3 = _demo_recommend("Low", 3)
        assert len(result_3) == 3
        result_5 = _demo_recommend("Low", 5)
        assert len(result_5) == 3  # Only 3 demo entries available

    def test_index_starts_at_one(self):
        """Result index should be 1-based for ranking display."""
        result = _demo_recommend("Moderate", 3)
        assert result.index[0] == 1
        assert result.index[-1] == 3

    def test_sharpe_ratio_positive(self):
        """All demo Sharpe ratios should be positive."""
        for risk in ["Low", "Moderate", "High"]:
            result = _demo_recommend(risk, 3)
            assert (result["sharpe_ratio"] > 0).all()

    def test_has_required_columns(self):
        """Demo recommendations should have key columns."""
        result = _demo_recommend("Moderate", 3)
        required_cols = ["amfi_code", "scheme_name", "risk_grade", "sharpe_ratio"]
        for col in required_cols:
            assert col in result.columns, f"Missing column: {col}"

    def test_unknown_risk_uses_moderate(self):
        """Unknown risk level should fall back to Moderate."""
        result = _demo_recommend("Unknown", 3)
        assert len(result) == 3  # Uses Moderate as default
