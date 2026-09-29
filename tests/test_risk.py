"""
tests/test_risk.py
───────────────────
Unit tests for PositionCap and PyramidingController risk modules.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.domain.enums import Exchange, Side
from app.domain.models import Portfolio, Position
from app.risk.position_cap import PositionCap
from app.risk.pyramiding import PyramidingController


# ── PositionCap ───────────────────────────────────────────────────────────────


@pytest.fixture
def portfolio_with_positions() -> Portfolio:
    p = Portfolio(cash=Decimal("500000"), peak_equity=Decimal("500000"))
    for i in range(3):
        sym = f"SYM{i}"
        p.positions[sym] = Position(
            symbol=sym,
            exchange=Exchange.NSE,
            side=Side.BUY,
            quantity=1,
            average_price=Decimal("100"),
            strategy_id="test",
        )
    return p


class TestPositionCap:
    def test_allows_under_cap(self, portfolio_with_positions: Portfolio) -> None:
        cap = PositionCap(max_positions=5, max_exposure=Decimal("1000000"))
        # can_add_position returns True when under cap
        assert cap.can_add_position(portfolio_with_positions)

    def test_blocks_at_cap(self, portfolio_with_positions: Portfolio) -> None:
        # 3 positions, cap = 3 → blocked
        cap = PositionCap(max_positions=3, max_exposure=Decimal("1000000"))
        assert not cap.can_add_position(portfolio_with_positions)

    def test_blocks_on_max_exposure(self, portfolio_with_positions: Portfolio) -> None:
        # 3 positions × 100 = 300 notional; set limit to 299
        cap = PositionCap(max_positions=10, max_exposure=Decimal("299"))
        assert not cap.can_add_position(portfolio_with_positions)

    def test_empty_portfolio_can_always_open(self) -> None:
        cap = PositionCap(max_positions=5, max_exposure=Decimal("1000000"))
        empty = Portfolio(cash=Decimal("100000"), peak_equity=Decimal("100000"))
        assert cap.can_add_position(empty)

    def test_check_returns_alerts_when_breached(self, portfolio_with_positions: Portfolio) -> None:
        cap = PositionCap(max_positions=3, max_exposure=Decimal("1000000"))
        alerts = cap.check(portfolio_with_positions)
        assert len(alerts) >= 1

    def test_check_returns_empty_when_ok(self, portfolio_with_positions: Portfolio) -> None:
        cap = PositionCap(max_positions=10, max_exposure=Decimal("1000000"))
        alerts = cap.check(portfolio_with_positions)
        assert alerts == []


# ── PyramidingController ──────────────────────────────────────────────────────


@pytest.fixture
def pyramid_ctrl() -> PyramidingController:
    return PyramidingController(max_layers=3, min_profit_atr=1.0, size_factor=0.5, base_quantity=1)


@pytest.fixture
def long_position() -> Position:
    return Position(
        symbol="NIFTY",
        exchange=Exchange.NSE,
        side=Side.BUY,
        quantity=1,
        average_price=Decimal("18000"),
        strategy_id="test",
    )


class TestPyramidingController:
    def test_initial_layer_count_zero(self, pyramid_ctrl: PyramidingController) -> None:
        assert pyramid_ctrl.layer_count("NIFTY") == 0

    def test_can_pyramid_profitable(
        self, pyramid_ctrl: PyramidingController, long_position: Position
    ) -> None:
        # Price is 2 ATR above entry → should allow pyramiding
        allowed, _ = pyramid_ctrl.can_pyramid(
            long_position,
            current_price=Decimal("18200"),
            atr=Decimal("100"),
        )
        assert allowed

    def test_cannot_pyramid_unprofitable(
        self, pyramid_ctrl: PyramidingController, long_position: Position
    ) -> None:
        # Price at entry → 0 ATR profit → blocked
        allowed, _ = pyramid_ctrl.can_pyramid(
            long_position,
            current_price=Decimal("18000"),
            atr=Decimal("100"),
        )
        assert not allowed

    def test_add_layer_increments_count(
        self, pyramid_ctrl: PyramidingController
    ) -> None:
        pyramid_ctrl.add_layer("NIFTY")
        assert pyramid_ctrl.layer_count("NIFTY") == 1

    def test_blocks_at_max_layers(
        self, pyramid_ctrl: PyramidingController, long_position: Position
    ) -> None:
        # Fill all 3 layers
        for _ in range(3):
            pyramid_ctrl.add_layer("NIFTY")
        allowed, _ = pyramid_ctrl.can_pyramid(
            long_position,
            current_price=Decimal("18300"),
            atr=Decimal("100"),
        )
        assert not allowed

    def test_close_position_resets_layers(
        self, pyramid_ctrl: PyramidingController
    ) -> None:
        pyramid_ctrl.add_layer("NIFTY")
        pyramid_ctrl.add_layer("NIFTY")
        pyramid_ctrl.close_position("NIFTY")
        assert pyramid_ctrl.layer_count("NIFTY") == 0

    def test_layer_quantity_decreases(self, pyramid_ctrl: PyramidingController) -> None:
        qty1 = pyramid_ctrl._layer_quantity(1)
        qty2 = pyramid_ctrl._layer_quantity(2)
        qty3 = pyramid_ctrl._layer_quantity(3)
        assert qty1 >= qty2 >= qty3 >= 1
