"""
app/macro/scoring.py
─────────────────────
Macro variable scoring and regime classification.

Each variable contributes a score in [-1, +1]:
  +1 → bullish / risk-on
  -1 → bearish / risk-off
   0 → neutral

The composite score is a weighted sum.  The regime is determined by
thresholding the composite score.

Scoring rules:
  VIX:        low VIX (+1) → BULL; mid (+0) → SIDEWAYS; high (-1) → RISK_OFF
  USDINR:     INR strengthening (falling USDINR) is bullish; weakening bearish
  Crude:      moderate crude (+0.5) = bullish for India (cheap imports);
              very high crude = inflationary headwind (-1)
  BondYield:  low / falling yield = BULL; high / rising = BEAR

Weights (sum = 1.0):
  VIX        0.40
  USDINR     0.25
  Crude      0.20
  BondYield  0.15
"""
from __future__ import annotations

from app.domain.enums import MarketRegime


class MacroScorer:
    """
    Scores macro variables and returns a composite regime label.

    Args:
        vix_high:    VIX level considered elevated (→ BEAR).
        vix_extreme: VIX level considered extreme (→ RISK_OFF).
    """

    # Reference / baseline levels for z-score style normalisation
    _USDINR_NEUTRAL = 83.0
    _CRUDE_LOW = 60.0
    _CRUDE_HIGH = 100.0
    _YIELD_LOW = 6.0
    _YIELD_HIGH = 8.5

    def __init__(self, vix_high: float = 25.0, vix_extreme: float = 35.0) -> None:
        self.vix_high = vix_high
        self.vix_extreme = vix_extreme

    def classify(
        self,
        vix: float,
        usdinr: float,
        crude: float,
        bond_yield: float,
    ) -> tuple[float, MarketRegime]:
        """
        Score all macro variables and return (composite_score, regime).

        Args:
            vix:        India VIX level.
            usdinr:     USD/INR spot rate.
            crude:      Crude oil price (USD/bbl).
            bond_yield: 10-year Indian government bond yield (%).

        Returns:
            Tuple of (composite_score, MarketRegime).
            Score is in range approximately [-1, +1].
        """
        score_vix = self._score_vix(vix)
        score_fx = self._score_usdinr(usdinr)
        score_crude = self._score_crude(crude)
        score_yield = self._score_bond_yield(bond_yield)

        composite = (
            0.40 * score_vix
            + 0.25 * score_fx
            + 0.20 * score_crude
            + 0.15 * score_yield
        )

        regime = self._regime_from_score(composite, vix)
        return composite, regime

    # ── Individual scorers ────────────────────────────────────────────────────

    def _score_vix(self, vix: float) -> float:
        """
        Score VIX:
          < 15           → +1.0 (calm, BULL)
          15–vix_high    → linear decline to 0
          vix_high–vix_extreme → linear decline to -1
          > vix_extreme  → -1.0 (panic)
        """
        if vix < 15.0:
            return 1.0
        elif vix <= self.vix_high:
            # linear 0 → -1 over [15, vix_high]
            return 1.0 - (vix - 15.0) / (self.vix_high - 15.0)
        elif vix <= self.vix_extreme:
            return -(vix - self.vix_high) / (self.vix_extreme - self.vix_high)
        else:
            return -1.0

    def _score_usdinr(self, usdinr: float) -> float:
        """
        Score USDINR:
          Strong INR (USDINR < neutral) is bullish → positive score.
          Weak INR (USDINR > neutral) is bearish → negative score.
          Clipped to [-1, 1] using ±5 INR as full range.
        """
        delta = usdinr - self._USDINR_NEUTRAL
        return float(max(-1.0, min(1.0, -delta / 5.0)))

    def _score_crude(self, crude: float) -> float:
        """
        Score crude oil:
          < $60  → +0.5 (very cheap, but possibly deflationary signal)
          $60-$80 → +1.0 (sweet spot for India)
          $80-$100 → linear decline to -0.5
          > $100  → -1.0 (inflationary headwind)
        """
        if crude < self._CRUDE_LOW:
            return 0.5
        elif crude <= 80.0:
            return 1.0
        elif crude <= self._CRUDE_HIGH:
            return 1.0 - 1.5 * (crude - 80.0) / 20.0
        else:
            return -1.0

    def _score_bond_yield(self, bond_yield: float) -> float:
        """
        Score 10yr yield:
          < 6%  → +1.0 (accommodative)
          6–7%  → linear to 0
          7–8.5% → linear to -1
          > 8.5% → -1.0 (tight)
        """
        if bond_yield < self._YIELD_LOW:
            return 1.0
        elif bond_yield <= 7.0:
            return 1.0 - (bond_yield - self._YIELD_LOW) / (7.0 - self._YIELD_LOW)
        elif bond_yield <= self._YIELD_HIGH:
            return -(bond_yield - 7.0) / (self._YIELD_HIGH - 7.0)
        else:
            return -1.0

    # ── Regime classification ─────────────────────────────────────────────────

    @staticmethod
    def _regime_from_score(score: float, vix: float) -> MarketRegime:
        """
        Map composite score to regime.

        Thresholds (tuned for Indian market):
          score >= +0.30  → BULL
          score in [-0.20, +0.30) → SIDEWAYS
          score in [-0.60, -0.20) → BEAR
          score < -0.60   → RISK_OFF (also triggered by extreme VIX)
        """
        if vix >= 35.0:
            return MarketRegime.RISK_OFF
        if score >= 0.30:
            return MarketRegime.BULL
        elif score >= -0.20:
            return MarketRegime.SIDEWAYS
        elif score >= -0.60:
            return MarketRegime.BEAR
        else:
            return MarketRegime.RISK_OFF
