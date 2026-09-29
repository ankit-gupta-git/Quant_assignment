"""
app/risk/position_cap.py
────────────────────────
Position Cap Risk Rule.

Enforces a hard limit on:
  * The number of simultaneous open positions.
  * The total gross notional exposure (positions × price).

These are checked BEFORE order placement.  If the cap is breached, the
order is rejected and a ``RiskAlert`` is emitted.
"""
from __future__ import annotations

from decimal import Decimal

from app.core.logger import get_logger
from app.domain.enums import AlertLevel, RiskEvent
from app.domain.models import Portfolio, RiskAlert

log = get_logger(__name__)


class PositionCap:
    """
    Enforces position-count and exposure limits.

    Args:
        max_positions: Maximum number of concurrent open positions.
        max_exposure:  Maximum gross notional value of all open positions.
    """

    def __init__(self, max_positions: int, max_exposure: Decimal) -> None:
        if max_positions < 1:
            raise ValueError("max_positions must be >= 1")
        if max_exposure <= Decimal("0"):
            raise ValueError("max_exposure must be > 0")
        self.max_positions = max_positions
        self.max_exposure = max_exposure

    # ── Checks ────────────────────────────────────────────────────────────────

    def check(self, portfolio: Portfolio) -> list[RiskAlert]:
        """
        Validate the portfolio against all position cap rules.

        Args:
            portfolio: Current portfolio snapshot.

        Returns:
            A list of ``RiskAlert`` objects.  Empty list means no violations.
        """
        alerts: list[RiskAlert] = []
        alerts.extend(self._check_position_count(portfolio))
        alerts.extend(self._check_exposure(portfolio))
        return alerts

    def can_add_position(self, portfolio: Portfolio) -> bool:
        """
        Return True if a new position can be opened without violating limits.
        Convenience method for pre-trade checks.
        """
        count_ok = len(portfolio.positions) < self.max_positions
        exposure_ok = portfolio.total_exposure < self.max_exposure
        return count_ok and exposure_ok

    # ── Private helpers ───────────────────────────────────────────────────────

    def _check_position_count(self, portfolio: Portfolio) -> list[RiskAlert]:
        count = len(portfolio.positions)
        if count >= self.max_positions:
            msg = (
                f"Position count {count} has reached/exceeded cap {self.max_positions}"
            )
            log.warning("risk.position_cap.count", count=count, cap=self.max_positions)
            return [
                RiskAlert(
                    event=RiskEvent.POSITION_CAP,
                    message=msg,
                    level=AlertLevel.WARNING,
                    metadata={"count": count, "cap": self.max_positions},
                )
            ]
        return []

    def _check_exposure(self, portfolio: Portfolio) -> list[RiskAlert]:
        exposure = portfolio.total_exposure
        if exposure >= self.max_exposure:
            msg = (
                f"Total exposure {exposure} has reached/exceeded limit {self.max_exposure}"
            )
            log.warning(
                "risk.position_cap.exposure",
                exposure=str(exposure),
                limit=str(self.max_exposure),
            )
            return [
                RiskAlert(
                    event=RiskEvent.MAX_EXPOSURE,
                    message=msg,
                    level=AlertLevel.CRITICAL,
                    metadata={"exposure": str(exposure), "limit": str(self.max_exposure)},
                )
            ]
        return []
