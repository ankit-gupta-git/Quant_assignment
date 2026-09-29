"""
tests/test_pyramiding.py
─────────────────────────
Regression tests for the PyramidingController edge-cases.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.domain.enums import Exchange, Side
from app.domain.models import Position
from app.risk.pyramiding import PyramidingController


def make_ctrl(max_layers: int = 3) -> PyramidingController:
    return PyramidingController(
        max_layers=max_layers,
        min_profit_atr=1.0,
        size_factor=0.5,
        base_quantity=2,
    )


def make_pos(avg_price: float = 18000.0) -> Position:
    return Position(
        symbol="NIFTY",
        exchange=Exchange.NSE,
        side=Side.BUY,
        quantity=1,
        average_price=Decimal(str(avg_price)),
        strategy_id="test",
    )


class TestPyramidingEdgeCases:
    def test_layer_1_quantity_is_base(self) -> None:
        ctrl = make_ctrl()
        assert ctrl._layer_quantity(1) == 2

    def test_layer_2_quantity_less_than_layer_1(self) -> None:
        ctrl = make_ctrl()
        assert ctrl._layer_quantity(2) <= ctrl._layer_quantity(1)

    def test_minimum_quantity_is_one(self) -> None:
        ctrl = PyramidingController(max_layers=5, size_factor=0.1, base_quantity=1)
        # Even for high layer numbers, qty >= 1
        assert ctrl._layer_quantity(10) >= 1

    def test_cannot_pyramid_zero_atr(self) -> None:
        ctrl = make_ctrl()
        pos = make_pos()
        # ATR=0 → profit in ATR = 0 → blocked
        allowed, reason = ctrl.can_pyramid(pos, Decimal("18500"), atr=Decimal("0"))
        assert not allowed

    def test_can_pyramid_after_close_reset(self) -> None:
        ctrl = make_ctrl(max_layers=2)
        for _ in range(2):
            ctrl.add_layer("NIFTY")
        pos = make_pos()
        allowed, _ = ctrl.can_pyramid(pos, Decimal("18500"), atr=Decimal("100"))
        assert not allowed

        ctrl.close_position("NIFTY")
        allowed, _ = ctrl.can_pyramid(pos, Decimal("18500"), atr=Decimal("100"))
        assert allowed

    def test_validate_returns_alerts_when_blocked(self) -> None:
        ctrl = make_ctrl(max_layers=1)
        ctrl.add_layer("NIFTY")
        pos = make_pos()
        alerts = ctrl.validate(pos, Decimal("18500"), atr=Decimal("100"))
        assert len(alerts) >= 1

    def test_validate_returns_empty_when_allowed(self) -> None:
        ctrl = make_ctrl()
        pos = make_pos()
        alerts = ctrl.validate(pos, Decimal("18500"), atr=Decimal("100"))
        assert alerts == []

    def test_short_position_profit(self) -> None:
        ctrl = make_ctrl()
        pos = Position(
            symbol="NIFTY",
            exchange=Exchange.NSE,
            side=Side.SELL,
            quantity=1,
            average_price=Decimal("18000"),
            strategy_id="test",
        )
        # Short profit: avg - current = 18000 - 17800 = 200 / ATR(100) = 2 ATR
        allowed, _ = ctrl.can_pyramid(pos, Decimal("17800"), atr=Decimal("100"))
        assert allowed
