"""
app/monitoring/alerts.py
─────────────────────────
Alerting module.

Supports:
* Console alerts (always on)
* HTTP webhook alerts (async, fire-and-forget)
* Structured logging via structlog

The ``AlertManager`` is the single injection point for all risk-engine
and system alerts.  Downstream consumers (SMS gateways, Slack, PagerDuty)
plug in via the webhook URL configured in Settings.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

import httpx

from app.core.logger import get_logger
from app.domain.enums import AlertLevel
from app.domain.models import RiskAlert

log = get_logger(__name__)


class AlertManager:
    """
    Central alert dispatcher.

    Args:
        webhook_url:   HTTP endpoint that receives POST payloads.
        phone_number:  Destination number for SMS simulation (console only).
        timeout_s:     HTTP request timeout in seconds.
    """

    def __init__(
        self,
        webhook_url: str = "",
        phone_number: str = "",
        timeout_s: float = 5.0,
    ) -> None:
        self._webhook_url = webhook_url
        self._phone_number = phone_number
        self._timeout = timeout_s
        self._history: list[RiskAlert] = []

    # ── Public API ────────────────────────────────────────────────────────────

    def send(self, alert: RiskAlert) -> None:
        """
        Synchronously dispatch an alert to all configured channels.
        Schedules the async webhook in a background task if an event loop
        is running, otherwise blocks.
        """
        self._history.append(alert)
        self._console_alert(alert)
        self._log_alert(alert)

        if self._webhook_url:
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._send_webhook(alert))
            except RuntimeError:
                # No running event loop — fire synchronously
                asyncio.run(self._send_webhook(alert))

    def send_raw(
        self,
        message: str,
        level: AlertLevel = AlertLevel.INFO,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Convenience wrapper for ad-hoc string alerts."""
        from app.domain.enums import RiskEvent

        alert = RiskAlert(
            event=RiskEvent.KILL_SWITCH,
            message=message,
            level=level,
            metadata=metadata or {},
        )
        self.send(alert)

    @property
    def history(self) -> list[RiskAlert]:
        """All alerts dispatched in this session (most recent last)."""
        return list(self._history)

    # ── Channels ──────────────────────────────────────────────────────────────

    def _console_alert(self, alert: RiskAlert) -> None:
        """Print a colour-coded alert to stdout."""
        colour = {
            AlertLevel.INFO: "\033[96m",      # cyan
            AlertLevel.WARNING: "\033[93m",   # yellow
            AlertLevel.CRITICAL: "\033[91m",  # red
        }.get(alert.level, "\033[0m")
        reset = "\033[0m"
        prefix = f"[{alert.level.value}]"
        ts = datetime.utcnow().isoformat(timespec="seconds")
        if alert.level == AlertLevel.CRITICAL and self._phone_number:
            sms_line = f"  📱 SMS → {self._phone_number}"
        else:
            sms_line = ""
        print(
            f"{colour}{prefix}{reset} {ts} | {alert.event.value} | {alert.message}{sms_line}"
        )

    def _log_alert(self, alert: RiskAlert) -> None:
        """Emit a structured log event."""
        bound = log.bind(
            alert_level=alert.level.value,
            event=alert.event.value,
            message=alert.message,
            metadata=alert.metadata,
        )
        if alert.level == AlertLevel.CRITICAL:
            bound.critical("alert.dispatched")
        elif alert.level == AlertLevel.WARNING:
            bound.warning("alert.dispatched")
        else:
            bound.info("alert.dispatched")

    async def _send_webhook(self, alert: RiskAlert) -> None:
        """POST the alert payload to the configured webhook URL."""
        payload = {
            "level": alert.level.value,
            "event": alert.event.value,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat(),
            "metadata": alert.metadata,
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(self._webhook_url, json=payload)
                resp.raise_for_status()
                log.info("alert.webhook.ok", status=resp.status_code, url=self._webhook_url)
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "alert.webhook.failed",
                url=self._webhook_url,
                error=str(exc),
            )
