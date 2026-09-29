"""
app/backtest/brokerage.py
──────────────────────────
Indian brokerage and exchange charge calculator.

Computes all applicable charges for NSE equity/F&O trades:
  * Brokerage (flat ₹20 per order, Zerodha-style)
  * STT (Securities Transaction Tax)
  * Transaction charges (NSE turnover charges)
  * GST on brokerage + transaction charges
  * SEBI turnover fee
  * Stamp duty (buy-side only)

References:
  * NSE circular on transaction charges (2024)
  * SEBI LODR (transaction fee schedule)
  * Finance Act 2023 (STT rates)
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.domain.enums import Exchange, ProductType, Side


@dataclass(frozen=True)
class ChargeBreakdown:
    """Itemised breakdown of all transaction charges."""
    brokerage: Decimal
    stt: Decimal
    transaction_charges: Decimal
    sebi_fee: Decimal
    gst: Decimal
    stamp_duty: Decimal

    @property
    def total(self) -> Decimal:
        return (
            self.brokerage
            + self.stt
            + self.transaction_charges
            + self.sebi_fee
            + self.gst
            + self.stamp_duty
        )


class IndianBrokerageModel:
    """
    Computes Indian market transaction costs (NSE/MCX).

    Args:
        flat_brokerage:   Flat brokerage per order in INR (default ₹20).
        brokerage_pct:    Percentage brokerage (used when > flat, e.g. delivery).
        use_flat:         If True, use flat fee; else use percentage.
    """

    # ── Rate constants (as Decimal for precision) ──────────────────────────────
    _STT_EQUITY_DELIVERY_BUY = Decimal("0.001")    # 0.10% on buy
    _STT_EQUITY_DELIVERY_SELL = Decimal("0.001")   # 0.10% on sell
    _STT_EQUITY_INTRADAY_SELL = Decimal("0.00025") # 0.025% on sell side only
    _STT_FUTURES_SELL = Decimal("0.0001")          # 0.01% on sell side
    _STT_OPTIONS_BUY = Decimal("0.001")            # 0.10% on buy (premium)

    _NSE_EQUITY_TRANSACTION = Decimal("0.0000297") # ₹2.97 per lakh (0.00297%)
    _NSE_FNO_TRANSACTION = Decimal("0.0000190")    # ₹1.90 per lakh futures
    _NSE_OPTIONS_TRANSACTION = Decimal("0.0000503")

    _SEBI_FEE = Decimal("0.000001")               # ₹10 per crore
    _GST_RATE = Decimal("0.18")                    # 18% GST
    _STAMP_DUTY_RATE = Decimal("0.00003")          # 0.003% on buy turnover

    _FLAT_BROKERAGE = Decimal("20")                # Zerodha flat ₹20

    def __init__(
        self,
        flat_brokerage: Decimal = Decimal("20"),
        brokerage_pct: float = 0.03,
        use_flat: bool = True,
    ) -> None:
        self.flat_brokerage = flat_brokerage
        self.brokerage_pct = Decimal(str(brokerage_pct / 100.0))
        self.use_flat = use_flat

    def compute(
        self,
        turnover: Decimal,
        side: Side,
        product_type: ProductType,
        exchange: Exchange = Exchange.NSE,
    ) -> ChargeBreakdown:
        """
        Compute all charges for a single trade.

        Args:
            turnover:     Trade value = quantity × fill_price.
            side:         BUY or SELL.
            product_type: CNC / MIS / NRML.
            exchange:     NSE / BSE / MCX / NFO.

        Returns:
            A ``ChargeBreakdown`` with itemised and total charges.
        """
        brokerage = self._compute_brokerage(turnover)
        stt = self._compute_stt(turnover, side, product_type)
        txn = self._compute_transaction_charges(turnover, product_type, exchange)
        sebi = turnover * self._SEBI_FEE
        gst = (brokerage + txn) * self._GST_RATE
        stamp = self._compute_stamp_duty(turnover, side)

        return ChargeBreakdown(
            brokerage=brokerage,
            stt=stt,
            transaction_charges=txn,
            sebi_fee=sebi,
            gst=gst,
            stamp_duty=stamp,
        )

    # ── Private charge calculators ─────────────────────────────────────────────

    def _compute_brokerage(self, turnover: Decimal) -> Decimal:
        if self.use_flat:
            return self.flat_brokerage
        pct_brokerage = turnover * self.brokerage_pct
        return min(self.flat_brokerage, pct_brokerage)

    def _compute_stt(
        self, turnover: Decimal, side: Side, product_type: ProductType
    ) -> Decimal:
        if product_type == ProductType.CNC:
            return turnover * self._STT_EQUITY_DELIVERY_SELL  # both sides
        elif product_type == ProductType.MIS:
            return turnover * self._STT_EQUITY_INTRADAY_SELL if side == Side.SELL else Decimal("0")
        elif product_type == ProductType.NRML:
            return turnover * self._STT_FUTURES_SELL if side == Side.SELL else Decimal("0")
        return Decimal("0")

    def _compute_transaction_charges(
        self, turnover: Decimal, product_type: ProductType, exchange: Exchange
    ) -> Decimal:
        if product_type == ProductType.NRML:
            if exchange in {Exchange.NFO, Exchange.NSE}:
                return turnover * self._NSE_FNO_TRANSACTION
        return turnover * self._NSE_EQUITY_TRANSACTION

    def _compute_stamp_duty(self, turnover: Decimal, side: Side) -> Decimal:
        if side == Side.BUY:
            return turnover * self._STAMP_DUTY_RATE
        return Decimal("0")


# ── Convenience aliases for backtest engine ────────────────────────────────────

class BrokerageResult:
    """Simple result object matching what backtest engine expects."""

    def __init__(self, breakdown: 'ChargeBreakdown') -> None:
        self.brokerage = breakdown.brokerage
        self.stt = breakdown.stt
        self.transaction_charges = breakdown.transaction_charges
        self.gst = breakdown.gst
        self.total = breakdown.total


class BrokerageModel:
    """Protocol-style base for brokerage models."""

    def calculate(self, order: 'Order', fill_price: 'Decimal') -> 'BrokerageResult':
        raise NotImplementedError


class NSEEquityBrokerage(BrokerageModel):
    """
    Zerodha-style flat-brokerage model for NSE equity/intraday trades.
    Wraps IndianBrokerageModel and exposes calculate() interface for the backtest engine.
    """

    def __init__(self, flat_brokerage: 'Decimal | None' = None) -> None:
        from decimal import Decimal as _Dec
        self._model = IndianBrokerageModel(
            flat_brokerage=flat_brokerage if flat_brokerage is not None else _Dec('20'),
            use_flat=True,
        )

    def calculate(self, order, fill_price) -> 'BrokerageResult':  # type: ignore[override]
        from decimal import Decimal as _Dec
        turnover = _Dec(str(order.quantity)) * fill_price
        breakdown = self._model.compute(
            turnover=turnover,
            side=order.side,
            product_type=order.product_type,
            exchange=order.exchange,
        )
        return BrokerageResult(breakdown)
