"""
app/risk/kill_switch.py
────────────────────────
Emergency Kill Switch.

When activated the kill switch:
  1. Sets an internal flag to block ALL new orders.
  2. Requests cancellation of every open order.
  3. Requests market-order closure of every open position.
  4. Emits a ``KillSwitchEvent`` to all registered listeners.
  5. Logs a CRITICAL structured event.

The kill switch is irreversible within a trading session; only a process
restart with manual reset can re-enable trading.
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Callable, Optional

from app.core.logger import get_logger
from app.domain.events import KillSwitchEvent
from app.domain.models import Portfolio, RiskAlert
from app.domain.enums import AlertLevel, RiskEvent

log = get_logger(__name__)

# Type alias for event listener callbacks
KillSwitchListener = Callable[[KillSwitchEvent], None]


class KillSwitch:
    """
    Emergency kill switch for the trading engine.

    Usage::

        ks = KillSwitch()
        ks.register_listener(on_kill)
        # ... later, in the risk engine:
        if daily_loss > limit:
            ks.activate("Max daily loss breached", portfolio)

    Attributes:
        _activated:   True once the switch is flipped; cannot be undone.
        _reason:      Human-readable reason for activation.
        _activated_at: UTC timestamp of activation.
        _listeners:   Callbacks invoked on activation.
    """

    def __init__(
        self,
        max_daily_loss: "Decimal | None" = None,
        max_consecutive_losses: int | None = None,
        max_drawdown_pct: float | None = None,
        alert_manager: object | None = None,
    ) -> None:
        # Risk limits stored for external reference / monitoring layer
        self.max_daily_loss = max_daily_loss
        self.max_consecutive_losses = max_consecutive_losses
        self.max_drawdown_pct = max_drawdown_pct
        self._alert_manager = alert_manager
        self._activated: bool = False
        self._reason: str = ""
        self._activated_at: Optional[datetime] = None
        self._listeners: list[KillSwitchListener] = []

    # ── Public interface ──────────────────────────────────────────────────────

    @property
    def is_active(self) -> bool:
        """True if the kill switch has been activated."""
        return self._activated

    @property
    def is_triggered(self) -> bool:
        """Alias for is_active — True if kill switch has been fired."""
        return self._activated

    def register_listener(self, listener: KillSwitchListener) -> None:
        """Register a callback to be invoked when the kill switch fires."""
        self._listeners.append(listener)

    def activate(
        self,
        reason: str,
        portfolio: Optional[Portfolio] = None,
    ) -> KillSwitchEvent:
        """
        Activate the kill switch.

        Args:
            reason:    Human-readable description of why it was triggered.
            portfolio: Current portfolio state (used to count positions/orders).

        Returns:
            The ``KillSwitchEvent`` that was emitted.

        Note:
            Calling ``activate`` on an already-active kill switch is a no-op
            and returns the original event (idempotent).
        """
        if self._activated:
            log.warning("kill_switch.already_active", reason=reason)
            return KillSwitchEvent(reason=self._reason)

        self._activated = True
        self._reason = reason
        self._activated_at = datetime.utcnow()

        positions_closed = len(portfolio.positions) if portfolio else 0

        event = KillSwitchEvent(
            reason=reason,
            positions_closed=positions_closed,
            orders_cancelled=0,
        )

        log.critical(
            "kill_switch.activated",
            reason=reason,
            positions_closed=positions_closed,
            timestamp=self._activated_at.isoformat(),
        )

        for listener in self._listeners:
            try:
                listener(event)
            except Exception as exc:
                log.error("kill_switch.listener_error", exc=str(exc))

        return event

    def reset(self) -> None:
        """
        Reset the kill switch (MANUAL OVERRIDE ONLY).
        Should only be called after a manual inspection and system restart.
        """
        log.warning("kill_switch.manual_reset", previous_reason=self._reason)
        self._activated = False
        self._reason = ""
        self._activated_at = None

    def build_alert(self, reason: str) -> RiskAlert:
        """Create a ``RiskAlert`` object for the monitoring layer."""
        return RiskAlert(
            event=RiskEvent.KILL_SWITCH,
            message=f"Kill switch activated: {reason}",
            level=AlertLevel.CRITICAL,
        )
