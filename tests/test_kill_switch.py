"""
tests/test_kill_switch.py
──────────────────────────
Unit tests for the KillSwitch risk engine component.
"""
from __future__ import annotations

from decimal import Decimal

import pytest

from app.domain.enums import AlertLevel
from app.domain.models import Portfolio, RiskAlert
from app.risk.kill_switch import KillSwitch


class TestKillSwitchActivation:
    def test_not_active_by_default(self) -> None:
        ks = KillSwitch()
        assert not ks.is_active

    def test_activate_sets_active(self) -> None:
        ks = KillSwitch()
        ks.activate("test reason")
        assert ks.is_active

    def test_activate_returns_event(self) -> None:
        from app.domain.events import KillSwitchEvent

        ks = KillSwitch()
        event = ks.activate("daily loss breach")
        assert isinstance(event, KillSwitchEvent)
        assert event.reason == "daily loss breach"

    def test_activate_idempotent(self) -> None:
        """Calling activate twice should be a no-op on the second call."""
        ks = KillSwitch()
        ks.activate("reason 1")
        ks.activate("reason 2")  # second call is no-op
        assert ks.is_active
        assert ks._reason == "reason 1"  # first reason preserved

    def test_reset_clears_activation(self) -> None:
        ks = KillSwitch()
        ks.activate("some reason")
        assert ks.is_active
        ks.reset()
        assert not ks.is_active

    def test_listener_called_on_activate(self) -> None:
        from app.domain.events import KillSwitchEvent

        calls: list[KillSwitchEvent] = []
        ks = KillSwitch()
        ks.register_listener(lambda e: calls.append(e))
        ks.activate("breach")
        assert len(calls) == 1
        assert calls[0].reason == "breach"

    def test_listener_not_called_on_double_activate(self) -> None:
        calls: list = []
        ks = KillSwitch()
        ks.register_listener(lambda e: calls.append(e))
        ks.activate("first")
        ks.activate("second")  # idempotent – no second listener call
        assert len(calls) == 1

    def test_build_alert_returns_critical(self) -> None:
        ks = KillSwitch()
        alert = ks.build_alert("max drawdown")
        assert alert.level == AlertLevel.CRITICAL
        assert "max drawdown" in alert.message

    def test_activate_with_portfolio(self) -> None:
        portfolio = Portfolio(cash=Decimal("100000"), peak_equity=Decimal("100000"))
        ks = KillSwitch()
        event = ks.activate("exposure breach", portfolio=portfolio)
        assert event is not None

    def test_activate_without_portfolio(self) -> None:
        ks = KillSwitch()
        event = ks.activate("system error")
        assert event is not None
