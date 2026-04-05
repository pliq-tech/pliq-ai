"""Unit tests for lease analysis models."""

from src.models.lease_analysis import (
    ClauseAnalysisResult,
    ClauseType,
    LeaseAnalyzer,
    RiskLevel,
)


class TestLeaseAnalyzer:
    """Tests for the lease clause analyzer."""

    def test_english_lease_extracts_clauses(self) -> None:
        """An English lease with standard clauses should be extracted."""
        analyzer = LeaseAnalyzer()
        text = (
            "The monthly rent is 1200 EUR. "
            "A security deposit of 2400 EUR is required. "
            "The lease duration is 12 months. "
            "The termination notice period is 3 months. "
            "The tenant must maintain the property in good condition."
        )
        result = analyzer.extract_clauses(text, language="en")
        found_types = {c.clause_type for c in result.clauses}
        assert ClauseType.RENT in found_types
        assert ClauseType.DEPOSIT in found_types
        assert ClauseType.DURATION in found_types
        assert ClauseType.TERMINATION in found_types
        assert ClauseType.MAINTENANCE in found_types

    def test_french_lease_extracts_clauses(self) -> None:
        """A French lease should also extract clauses correctly."""
        analyzer = LeaseAnalyzer()
        text = (
            "Le loyer mensuel est de 1200 EUR. "
            "Un depot de garantie de 2400 EUR est requis. "
            "La duree du bail est de 12 mois. "
            "Le preavis de resiliation est de 3 mois."
        )
        result = analyzer.extract_clauses(text, language="fr")
        found_types = {c.clause_type for c in result.clauses}
        assert ClauseType.RENT in found_types
        assert ClauseType.DEPOSIT in found_types
        assert ClauseType.DURATION in found_types
        assert ClauseType.TERMINATION in found_types

    def test_empty_text_returns_empty_result(self) -> None:
        """Empty lease text should return an empty result."""
        analyzer = LeaseAnalyzer()
        result = analyzer.extract_clauses("", language="en")
        assert result.clauses == []
        assert result.high_risk_count == 0
        assert "No lease text" in result.overall_assessment

    def test_excessive_penalty_flagged_high_risk(self) -> None:
        """A clause with an excessive penalty percentage should be flagged high."""
        analyzer = LeaseAnalyzer()
        text = (
            "The monthly rent is 1000 EUR. "
            "A penalty of 50% of the deposit will be charged for late payment. "
            "The termination notice period is 1 month."
        )
        result = analyzer.extract_clauses(text, language="en")
        penalty_clauses = [
            c for c in result.clauses if c.clause_type == ClauseType.PENALTY
        ]
        assert len(penalty_clauses) >= 1
        assert penalty_clauses[0].risk_level == RiskLevel.HIGH
        assert result.high_risk_count >= 1

    def test_missing_termination_flagged_medium(self) -> None:
        """A lease with no termination clause should flag a medium-risk warning."""
        analyzer = LeaseAnalyzer()
        text = "The monthly rent is 1000 EUR. The deposit is 2000 EUR."
        result = analyzer.extract_clauses(text, language="en")
        term_clauses = [
            c for c in result.clauses if c.clause_type == ClauseType.TERMINATION
        ]
        assert len(term_clauses) == 1
        assert term_clauses[0].risk_level == RiskLevel.MEDIUM

    def test_high_risk_keyword_waive_all_rights(self) -> None:
        """Text with 'waive all rights' should be flagged as high risk."""
        analyzer = LeaseAnalyzer()
        text = (
            "The tenant agrees to waive all rights to the deposit upon termination. "
            "The rent is 900 EUR."
        )
        result = analyzer.extract_clauses(text, language="en")
        high_risk = [c for c in result.clauses if c.risk_level == RiskLevel.HIGH]
        assert len(high_risk) >= 1

    def test_standard_lease_no_high_risk(self) -> None:
        """A standard lease with no alarming language should have zero high risk."""
        analyzer = LeaseAnalyzer()
        text = (
            "The monthly rent is 800 EUR. "
            "A security deposit of 1600 EUR is required. "
            "The lease duration is 12 months. "
            "The termination notice period is 3 months. "
            "The tenant shall maintain the property. "
            "Insurance is required."
        )
        result = analyzer.extract_clauses(text, language="en")
        assert result.high_risk_count == 0
