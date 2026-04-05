"""Lease clause extraction and risk classification."""

import re
from dataclasses import dataclass, field
from enum import Enum


class ClauseType(Enum):
    """Types of lease clauses."""

    RENT = "rent"
    DEPOSIT = "deposit"
    DURATION = "duration"
    TERMINATION = "termination"
    MAINTENANCE = "maintenance"
    SUBLETTING = "subletting"
    PET_POLICY = "pet_policy"
    INSURANCE = "insurance"
    PENALTY = "penalty"
    OTHER = "other"


class RiskLevel(Enum):
    """Risk levels for lease clauses."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Keyword patterns per clause type, supporting English and French.
# Order matters: more specific types are checked first to avoid
# ambiguity (e.g., "penalty" sentence containing "deposit" word).
_CLAUSE_PATTERNS_ORDERED: list[tuple[ClauseType, dict[str, list[str]]]] = [
    (ClauseType.PENALTY, {
        "en": [r"\bpenalty\b", r"\bfine\b", r"\bforfeit\b", r"\blate\s+fee\b"],
        "fr": [r"\bp[eé]nalit[eé]\b", r"\bamende\b", r"\bmajoration\b"],
    }),
    (ClauseType.TERMINATION, {
        "en": [r"\btermination\b", r"\bnotice\s+period\b", r"\bbreak\s+clause\b"],
        "fr": [r"\br[eé]siliation\b", r"\bpr[eé]avis\b", r"\brupture\b"],
    }),
    (ClauseType.RENT, {
        "en": [r"\brent\b", r"\bmonthly\s+payment\b", r"\blease\s+amount\b"],
        "fr": [r"\bloyer\b", r"\bmensualit[eé]\b", r"\bpaiement\s+mensuel\b"],
    }),
    (ClauseType.DEPOSIT, {
        "en": [r"\bdeposit\b", r"\bsecurity\s+deposit\b", r"\bcaution\b"],
        "fr": [r"\bd[eé]p[oô]t\b", r"\bcaution\b", r"\bgarantie\b"],
    }),
    (ClauseType.DURATION, {
        "en": [r"\bduration\b", r"\blease\s+term\b", r"\bperiod\b"],
        "fr": [r"\bdur[eé]e\b", r"\bp[eé]riode\b", r"\bterme\b"],
    }),
    (ClauseType.MAINTENANCE, {
        "en": [r"\bmaintenance\b", r"\bmaintain\b", r"\brepair\b", r"\bupkeep\b"],
        "fr": [r"\bentretien\b", r"\br[eé]paration\b", r"\btravaux\b"],
    }),
    (ClauseType.SUBLETTING, {
        "en": [r"\bsublet\b", r"\bsubletting\b", r"\bsublease\b"],
        "fr": [r"\bsous-location\b", r"\bsous-louer\b"],
    }),
    (ClauseType.PET_POLICY, {
        "en": [r"\bpet\b", r"\banimal\b", r"\bdog\b", r"\bcat\b"],
        "fr": [r"\banimal\b", r"\banimaux\b", r"\bchien\b", r"\bchat\b"],
    }),
    (ClauseType.INSURANCE, {
        "en": [r"\binsurance\b", r"\bcoverage\b", r"\bliability\b"],
        "fr": [r"\bassurance\b", r"\bcouverture\b", r"\bresponsabilit[eé]\b"],
    }),
]

# Keywords that indicate high-risk content
_HIGH_RISK_KEYWORDS: dict[str, list[str]] = {
    "en": [
        r"\bexcessive\b", r"\bforfeit\s+all\b", r"\birrevocable\b",
        r"\bwaive\s+all\s+rights\b", r"\bno\s+refund\b",
        r"\bunlimited\s+liability\b",
    ],
    "fr": [
        r"\bexcessif\b", r"\bperte\s+totale\b", r"\birr[eé]vocable\b",
        r"\brenonce[rz]?\s+[àa]\s+tous?\s+droits?\b",
        r"\bnon\s+remboursable\b",
    ],
}


@dataclass
class Clause:
    """A single extracted clause from a lease."""

    clause_type: ClauseType
    text: str
    start_position: int
    end_position: int
    risk_level: RiskLevel
    explanation: str = ""


@dataclass
class ClauseAnalysisResult:
    """Result of lease clause analysis."""

    clauses: list[Clause] = field(default_factory=list)
    overall_assessment: str = ""
    high_risk_count: int = 0
    medium_risk_count: int = 0


class LeaseAnalyzer:
    """Extracts and classifies clauses from lease text."""

    def _detect_clause_type(
        self, sentence: str, language: str
    ) -> ClauseType | None:
        """Match a sentence to a clause type by keyword patterns."""
        lang = language if language in ("en", "fr") else "en"
        lower = sentence.lower()
        for clause_type, lang_patterns in _CLAUSE_PATTERNS_ORDERED:
            patterns = lang_patterns.get(lang, lang_patterns["en"])
            for pattern in patterns:
                if re.search(pattern, lower):
                    return clause_type
        return None

    def _assess_risk(
        self, sentence: str, clause_type: ClauseType, language: str
    ) -> tuple[RiskLevel, str]:
        """Determine risk level for a clause based on content."""
        lang = language if language in ("en", "fr") else "en"
        lower = sentence.lower()

        # Check for high-risk keywords
        for pattern in _HIGH_RISK_KEYWORDS.get(lang, _HIGH_RISK_KEYWORDS["en"]):
            if re.search(pattern, lower):
                return RiskLevel.HIGH, "Contains high-risk language"

        # Penalty-specific checks
        if clause_type == ClauseType.PENALTY:
            amount_match = re.search(r"(\d+)\s*(%|percent|pour\s*cent)", lower)
            if amount_match:
                pct = int(amount_match.group(1))
                if pct > 20:
                    return RiskLevel.HIGH, f"Excessive penalty rate: {pct}%"

        # Missing termination clause is medium risk (checked at result level)
        return RiskLevel.LOW, "Standard clause"

    def _split_sentences(self, text: str) -> list[tuple[str, int, int]]:
        """Split text into sentences with positions."""
        results: list[tuple[str, int, int]] = []
        for match in re.finditer(r"[^.!?\n]+[.!?\n]?", text):
            sentence = match.group().strip()
            if sentence:
                results.append((sentence, match.start(), match.end()))
        return results

    def extract_clauses(
        self, lease_text: str, language: str = "en"
    ) -> ClauseAnalysisResult:
        """Extract and classify clauses from lease text."""
        if not lease_text or not lease_text.strip():
            return ClauseAnalysisResult(
                overall_assessment="No lease text provided"
            )

        sentences = self._split_sentences(lease_text)
        clauses: list[Clause] = []
        found_types: set[ClauseType] = set()

        for sentence, start, end in sentences:
            clause_type = self._detect_clause_type(sentence, language)
            if clause_type is None:
                continue

            risk_level, explanation = self._assess_risk(
                sentence, clause_type, language
            )
            clauses.append(
                Clause(
                    clause_type=clause_type,
                    text=sentence,
                    start_position=start,
                    end_position=end,
                    risk_level=risk_level,
                    explanation=explanation,
                )
            )
            found_types.add(clause_type)

        # Flag missing termination clause as medium risk
        if ClauseType.TERMINATION not in found_types and clauses:
            clauses.append(
                Clause(
                    clause_type=ClauseType.TERMINATION,
                    text="",
                    start_position=0,
                    end_position=0,
                    risk_level=RiskLevel.MEDIUM,
                    explanation="No termination clause found in lease",
                )
            )

        high_count = sum(1 for c in clauses if c.risk_level == RiskLevel.HIGH)
        medium_count = sum(
            1 for c in clauses if c.risk_level == RiskLevel.MEDIUM
        )

        if high_count > 0:
            assessment = f"Lease has {high_count} high-risk clause(s)"
        elif medium_count > 0:
            assessment = f"Lease has {medium_count} medium-risk clause(s)"
        else:
            assessment = "Lease appears standard with no flagged risks"

        return ClauseAnalysisResult(
            clauses=clauses,
            overall_assessment=assessment,
            high_risk_count=high_count,
            medium_risk_count=medium_count,
        )
