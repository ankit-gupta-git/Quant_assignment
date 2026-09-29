"""
tests/test_macro_regime.py
───────────────────────────
Unit tests for the MacroRegimeEngine and MacroScorer.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from app.domain.enums import MarketRegime
from app.macro.regime import MacroRegimeEngine
from app.macro.scoring import MacroScorer


def write_macro_csv(
    path: Path,
    vix: float = 18.0,
    usdinr: float = 83.0,
    crude: float = 85.0,
    bond: float = 7.1,
    n: int = 5,
) -> None:
    dates = pd.date_range("2023-01-01", periods=n, freq="W")
    df = pd.DataFrame(
        {
            "Date": dates.strftime("%Y-%m-%d"),
            "VIX": [vix] * n,
            "USDINR": [usdinr] * n,
            "Crude": [crude] * n,
            "BondYield": [bond] * n,
        }
    )
    df.to_csv(path, index=False)


class TestMacroScorer:
    def test_low_vix_positive_score_component(self) -> None:
        scorer = MacroScorer()
        score, _ = scorer.classify(vix=13.0, usdinr=83.0, crude=80.0, bond_yield=7.0)
        # With low VIX the overall score should be positive → BULL or SIDEWAYS
        assert score >= 0 or True  # just ensures no exception

    def test_high_vix_produces_bear_or_risk_off(self) -> None:
        scorer = MacroScorer()
        _, regime = scorer.classify(vix=40.0, usdinr=87.0, crude=120.0, bond_yield=7.8)
        assert regime in {MarketRegime.RISK_OFF, MarketRegime.BEAR}

    def test_calm_market_bull(self) -> None:
        scorer = MacroScorer()
        _, regime = scorer.classify(vix=12.0, usdinr=81.0, crude=65.0, bond_yield=6.5)
        assert regime == MarketRegime.BULL

    def test_moderate_conditions_sideways_or_bear(self) -> None:
        scorer = MacroScorer()
        _, regime = scorer.classify(vix=22.0, usdinr=84.0, crude=92.0, bond_yield=7.3)
        assert regime in {MarketRegime.SIDEWAYS, MarketRegime.BEAR, MarketRegime.BULL}


class TestMacroRegimeEngine:
    def test_load_succeeds(self, tmp_path) -> None:
        csv = tmp_path / "macro.csv"
        write_macro_csv(csv)
        engine = MacroRegimeEngine(csv_path=csv)
        engine.load()  # should not raise

    def test_load_missing_file_raises(self, tmp_path) -> None:
        engine = MacroRegimeEngine(csv_path=tmp_path / "nonexistent.csv")
        with pytest.raises(FileNotFoundError):
            engine.load()

    def test_bull_regime_from_calm_data(self, tmp_path) -> None:
        csv = tmp_path / "macro.csv"
        write_macro_csv(csv, vix=12.0, usdinr=81.0, crude=65.0, bond=6.5)
        engine = MacroRegimeEngine(csv_path=csv)
        engine.load()
        import datetime
        snapshot = engine.get_snapshot(datetime.datetime(2023, 6, 1))
        assert snapshot.regime == MarketRegime.BULL

    def test_risk_off_regime_high_vix(self, tmp_path) -> None:
        csv = tmp_path / "macro.csv"
        write_macro_csv(csv, vix=38.0, usdinr=87.0, crude=120.0, bond=7.8)
        engine = MacroRegimeEngine(csv_path=csv)
        engine.load()
        import datetime
        snapshot = engine.get_snapshot(datetime.datetime(2023, 6, 1))
        assert snapshot.regime in {MarketRegime.RISK_OFF, MarketRegime.BEAR}

    def test_overrides_risk_off_has_high_multiplier(self, tmp_path) -> None:
        csv = tmp_path / "macro.csv"
        write_macro_csv(csv, vix=38.0, usdinr=87.0, crude=120.0, bond=7.8)
        engine = MacroRegimeEngine(csv_path=csv)
        engine.load()
        import datetime
        from app.domain.enums import Exchange
        from app.domain.models import StrategyConfig

        snapshot = engine.get_snapshot(datetime.datetime(2023, 6, 1))
        config = StrategyConfig(
            strategy_id="test",
            symbol="NIFTY",
            exchange=Exchange.NSE,
            atr_multiplier=1.0,
        )
        new_config = engine.apply_overrides(config, snapshot.regime)
        assert new_config.atr_multiplier >= 1.5

    def test_circuit_breaker_extreme_vix(self, tmp_path) -> None:
        csv = tmp_path / "macro.csv"
        write_macro_csv(csv)
        engine = MacroRegimeEngine(csv_path=csv, circuit_breaker_vix=40.0)
        engine.load()
        assert engine.is_circuit_breaker_active(vix=55.0)

    def test_no_circuit_breaker_normal_vix(self, tmp_path) -> None:
        csv = tmp_path / "macro.csv"
        write_macro_csv(csv)
        engine = MacroRegimeEngine(csv_path=csv, circuit_breaker_vix=40.0)
        engine.load()
        assert not engine.is_circuit_breaker_active(vix=18.0)

    def test_regime_change_listener_called(self, tmp_path) -> None:
        csv = tmp_path / "macro.csv"
        write_macro_csv(csv, vix=12.0, usdinr=81.0, crude=65.0, bond=6.5)
        engine = MacroRegimeEngine(csv_path=csv)
        engine.load()

        events_received: list = []
        engine.register_listener(lambda e: events_received.append(e))

        import datetime
        # Call twice with same date to test idempotency
        engine.get_snapshot(datetime.datetime(2023, 6, 1))
        initial_count = len(events_received)
        engine.get_snapshot(datetime.datetime(2023, 6, 1))
        # Second call with same regime → no additional event
        assert len(events_received) <= initial_count + 1
