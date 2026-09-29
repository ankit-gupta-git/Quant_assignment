"""
tests/test_pnl.py
──────────────────
Unit tests for P&L calculations in domain models.

Tests that Decimal arithmetic is used correctly and that
floating-point rounding errors cannot creep into P&L.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from app.domain.enums import Exchange, Side
from app.domain.models import Fill, Portfolio, Position, Trade


class TestPositionPnL:
    def test_long_position_mark_to_market_profit(self) -> None:
        pos = Position(
            symbol="NIFTY",
            exchange=Exchange.NSE,
            side=Side.BUY,
            quantity=10,
            average_price=Decimal("18000"),
            strategy_id="test",
        )
        pos.mark_to_market(Decimal("18200"))
        assert pos.unrealised_pnl == Decimal("2000")  # (18200-18000)*10

    def test_short_position_mark_to_market_profit(self) -> None:
        pos = Position(
            symbol="NIFTY",
            exchange=Exchange.NSE,
            side=Side.SELL,
            quantity=5,
            average_price=Decimal("18000"),
            strategy_id="test",
        )
        pos.mark_to_market(Decimal("17800"))
        assert pos.unrealised_pnl == Decimal("1000")  # (18000-17800)*5

    def test_long_position_mark_to_market_loss(self) -> None:
        pos = Position(
            symbol="NIFTY",
            exchange=Exchange.NSE,
            side=Side.BUY,
            quantity=10,
            average_price=Decimal("18000"),
            strategy_id="test",
        )
        pos.mark_to_market(Decimal("17500"))
        assert pos.unrealised_pnl == Decimal("-5000")

    def test_total_pnl_is_sum(self) -> None:
        pos = Position(
            symbol="NIFTY",
            exchange=Exchange.NSE,
            side=Side.BUY,
            quantity=1,
            average_price=Decimal("18000"),
            strategy_id="test",
        )
        pos.realised_pnl = Decimal("500")
        pos.mark_to_market(Decimal("18100"))
        assert pos.total_pnl == Decimal("600")

    def test_notional_value(self) -> None:
        pos = Position(
            symbol="NIFTY",
            exchange=Exchange.NSE,
            side=Side.BUY,
            quantity=5,
            average_price=Decimal("18000"),
            strategy_id="test",
        )
        assert pos.notional_value == Decimal("90000")


class TestPortfolioPnL:
    def test_equity_includes_unrealised(self) -> None:
        portfolio = Portfolio(cash=Decimal("900000"), peak_equity=Decimal("1000000"))
        pos = Position(
            symbol="NIFTY",
            exchange=Exchange.NSE,
            side=Side.BUY,
            quantity=1,
            average_price=Decimal("18000"),
            strategy_id="test",
        )
        pos.unrealised_pnl = Decimal("5000")
        portfolio.positions["NIFTY"] = pos
        assert portfolio.equity == Decimal("905000")

    def test_drawdown_calculation(self) -> None:
        portfolio = Portfolio(cash=Decimal("90000"), peak_equity=Decimal("100000"))
        # Drawdown = (100k - 90k) / 100k = 10%
        assert portfolio.drawdown_pct == pytest.approx(10.0, rel=1e-6)

    def test_peak_equity_updated(self) -> None:
        portfolio = Portfolio(cash=Decimal("110000"), peak_equity=Decimal("100000"))
        portfolio.update_peak()
        assert portfolio.peak_equity == Decimal("110000")

    def test_peak_equity_not_decreased(self) -> None:
        portfolio = Portfolio(cash=Decimal("90000"), peak_equity=Decimal("100000"))
        portfolio.update_peak()
        assert portfolio.peak_equity == Decimal("100000")

    def test_total_exposure(self) -> None:
        portfolio = Portfolio(cash=Decimal("1000000"), peak_equity=Decimal("1000000"))
        for i, price in enumerate([18000, 19000]):
            portfolio.positions[f"SYM{i}"] = Position(
                symbol=f"SYM{i}",
                exchange=Exchange.NSE,
                side=Side.BUY,
                quantity=1,
                average_price=Decimal(str(price)),
                strategy_id="test",
            )
        assert portfolio.total_exposure == Decimal("37000")


class TestFillNetCost:
    def test_net_cost_includes_all_charges(self) -> None:
        fill = Fill(
            order_id="ORD-001",
            symbol="NIFTY",
            exchange=Exchange.NSE,
            side=Side.BUY,
            quantity=10,
            price=Decimal("18000"),
            brokerage=Decimal("20"),
            stt=Decimal("18"),
            transaction_charges=Decimal("5"),
            gst=Decimal("3"),
        )
        expected = Decimal("10") * Decimal("18000") + Decimal("20") + Decimal("18") + Decimal("5") + Decimal("3")
        assert fill.net_cost == expected

    def test_pnl_uses_decimal_not_float(self) -> None:
        """Verify no float leakage in P&L arithmetic (regression test)."""
        pos = Position(
            symbol="NIFTY",
            exchange=Exchange.NSE,
            side=Side.BUY,
            quantity=1,
            average_price=Decimal("0.1"),
            strategy_id="test",
        )
        pos.mark_to_market(Decimal("0.2"))
        # If using float: 0.2 - 0.1 = 0.10000000000000001 (float error)
        # With Decimal: exactly 0.1
        assert pos.unrealised_pnl == Decimal("0.1")
        assert isinstance(pos.unrealised_pnl, Decimal)
