"""
app/macro/regime.py
────────────────────
Macro Regime Engine.

Reads a CSV containing daily macro data and classifies the current market
into one of four regimes: BULL, BEAR, RISK_OFF, SIDEWAYS.

Each macro variable is scored independently and the scores are combined into
a composite regime score used to select a regime label.

Regime transitions trigger a ``RegimeChangeEvent`` and can modify strategy
parameters via ``regime_overrides``.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

import pandas as pd

from app.core.logger import get_logger
from app.domain.enums import MarketRegime
from app.domain.events import RegimeChangeEvent
from app.domain.models import MacroSnapshot, StrategyConfig
from app.macro.scoring import MacroScorer

log = get_logger(__name__)

# Regime-specific parameter overrides applied to StrategyConfig
REGIME_OVERRIDES: dict[MarketRegime, dict] = {
    MarketRegime.BULL: {
        "atr_multiplier": 1.0,
        "max_positions": 10,
        "position_cap_pct": 1.0,
    },
    MarketRegime.BEAR: {
        "atr_multiplier": 1.5,
        "max_positions": 6,
        "position_cap_pct": 0.6,
    },
    MarketRegime.RISK_OFF: {
        "atr_multiplier": 2.0,
        "max_positions": 4,
        "position_cap_pct": 0.5,
    },
    MarketRegime.SIDEWAYS: {
        "atr_multiplier": 1.2,
        "max_positions": 8,
        "position_cap_pct": 0.8,
    },
}


class MacroRegimeEngine:
    """
    Classifies the current macro environment and adjusts strategy parameters.

    Usage::

        engine = MacroRegimeEngine(csv_path=Path("data/macro.csv"))
        engine.load()
        snapshot = engine.get_snapshot(date=datetime(2024, 1, 15))
        engine.apply_overrides(strategy_config, snapshot.regime)

    Args:
        csv_path:         Path to macro CSV (Date, VIX, USDINR, Crude, BondYield).
        vix_high:         VIX threshold above which market enters RISK_OFF zone.
        vix_extreme:      VIX threshold for extreme RISK_OFF.
        circuit_breaker_vix: If VIX exceeds this level, circuit breaker fires.
    """

    def __init__(
        self,
        csv_path: Path,
        vix_high: float = 25.0,
        vix_extreme: float = 35.0,
        circuit_breaker_vix: float = 40.0,
    ) -> None:
        self.csv_path = csv_path
        self.vix_high = vix_high
        self.vix_extreme = vix_extreme
        self.circuit_breaker_vix = circuit_breaker_vix
        self._df: Optional[pd.DataFrame] = None
        self._current_regime: MarketRegime = MarketRegime.SIDEWAYS
        self._scorer = MacroScorer(vix_high=vix_high, vix_extreme=vix_extreme)
        self._listeners: list = []

    # ── Data loading ──────────────────────────────────────────────────────────

    def load(self) -> None:
        """Load and validate the macro CSV file."""
        if not self.csv_path.exists():
            raise FileNotFoundError(f"Macro CSV not found: {self.csv_path}")

        df = pd.read_csv(self.csv_path, parse_dates=["Date"])
        required = {"Date", "VIX", "USDINR", "Crude", "BondYield"}
        missing = required - set(df.columns)
        if missing:
            raise ValueError(f"Macro CSV missing columns: {missing}")

        df = df.sort_values("Date").reset_index(drop=True)
        df["Date"] = pd.to_datetime(df["Date"])
        self._df = df
        log.info("macro.loaded", rows=len(df), path=str(self.csv_path))

    # ── Regime computation ────────────────────────────────────────────────────

    def get_snapshot(self, date: datetime) -> MacroSnapshot:
        """
        Return the macro snapshot for the most recent available date
        up to and including ``date``.

        Args:
            date: Reference date (typically today or the backtest bar date).

        Returns:
            ``MacroSnapshot`` with regime label and composite score.

        Raises:
            RuntimeError: If ``load()`` has not been called.
        """
        if self._df is None:
            raise RuntimeError("MacroRegimeEngine.load() must be called first.")

        mask = self._df["Date"] <= pd.Timestamp(date)
        if not mask.any():
            log.warning("macro.no_data_before_date", date=str(date))
            return MacroSnapshot(
                date=date,
                vix=20.0,
                usdinr=83.0,
                crude=80.0,
                bond_yield=7.0,
                regime=MarketRegime.SIDEWAYS,
                score=0.0,
            )

        row = self._df[mask].iloc[-1]
        score, regime = self._scorer.classify(
            vix=float(row["VIX"]),
            usdinr=float(row["USDINR"]),
            crude=float(row["Crude"]),
            bond_yield=float(row["BondYield"]),
        )

        snapshot = MacroSnapshot(
            date=pd.Timestamp(row["Date"]).to_pydatetime(),
            vix=float(row["VIX"]),
            usdinr=float(row["USDINR"]),
            crude=float(row["Crude"]),
            bond_yield=float(row["BondYield"]),
            regime=regime,
            score=score,
        )

        if regime != self._current_regime:
            event = RegimeChangeEvent(
                previous_regime=self._current_regime.value,
                new_regime=regime.value,
                score=score,
            )
            self._current_regime = regime
            log.info(
                "macro.regime_change",
                previous=event.previous_regime,
                new=event.new_regime,
                score=score,
            )
            for listener in self._listeners:
                listener(event)

        return snapshot

    # ── Circuit breaker ───────────────────────────────────────────────────────

    def is_circuit_breaker_active(self, vix: float) -> bool:
        """
        Return True if VIX exceeds the circuit breaker threshold.
        When active, no new positions should be opened.
        """
        if vix >= self.circuit_breaker_vix:
            log.critical(
                "macro.circuit_breaker",
                vix=vix,
                threshold=self.circuit_breaker_vix,
            )
            return True
        return False

    # ── Parameter overrides ───────────────────────────────────────────────────

    def apply_overrides(
        self, config: StrategyConfig, regime: MarketRegime
    ) -> StrategyConfig:
        """
        Apply regime-specific parameter overrides to a strategy config.

        Returns a NEW StrategyConfig with overrides applied (immutable update).
        """
        overrides = REGIME_OVERRIDES.get(regime, {})
        new_config = StrategyConfig(
            strategy_id=config.strategy_id,
            symbol=config.symbol,
            exchange=config.exchange,
            atr_multiplier=overrides.get("atr_multiplier", config.atr_multiplier),
            max_positions=overrides.get("max_positions", config.max_positions),
            take_profit_multiplier=config.take_profit_multiplier,
            stop_loss_multiplier=config.stop_loss_multiplier,
            pyramid_enabled=config.pyramid_enabled,
            stop_and_reverse=config.stop_and_reverse,
            state=config.state,
            regime_overrides=overrides,
        )
        log.info(
            "macro.overrides_applied",
            regime=regime.value,
            atr_multiplier=new_config.atr_multiplier,
            max_positions=new_config.max_positions,
        )
        return new_config

    def register_listener(self, listener) -> None:  # type: ignore[type-arg]
        """Register a callback for regime change events."""
        self._listeners.append(listener)

    @property
    def current_regime(self) -> MarketRegime:
        return self._current_regime
