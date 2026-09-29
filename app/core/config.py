"""
app/core/config.py
──────────────────
Centralised application configuration using Pydantic Settings.
All settings are read from environment variables or the .env file.
"""
from __future__ import annotations

from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application-wide settings loaded from the environment / .env file.
    Every value has a sensible default so the engine can be started without
    touching .env (useful for CI and unit-tests).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────────────────────
    app_env: str = Field(default="development", description="Runtime environment")
    log_level: str = Field(default="INFO", description="Root log level")
    log_format: str = Field(default="json", description="'json' or 'console'")

    # ── Zerodha Mock API ──────────────────────────────────────────────────────
    zerodha_api_key: str = Field(default="mock_api_key")
    zerodha_api_secret: str = Field(default="mock_secret")
    zerodha_access_token: str = Field(default="mock_token")
    zerodha_base_url: str = Field(default="https://api.kite.trade")
    zerodha_ws_url: str = Field(default="wss://ws.kite.trade")

    # ── Risk Parameters ───────────────────────────────────────────────────────
    max_daily_loss: Decimal = Field(default=Decimal("50000"))
    max_exposure: Decimal = Field(default=Decimal("1000000"))
    max_consecutive_losses: int = Field(default=5)
    max_drawdown_pct: float = Field(default=10.0)
    kill_switch_enabled: bool = Field(default=True)

    # ── Grid Strategy ─────────────────────────────────────────────────────────
    grid_atr_multiplier: float = Field(default=1.5)
    grid_max_positions: int = Field(default=10)
    grid_take_profit_multiplier: float = Field(default=2.0)
    grid_stop_loss_multiplier: float = Field(default=3.0)

    # ── Macro Regime ──────────────────────────────────────────────────────────
    macro_csv_path: Path = Field(default=Path("data/macro.csv"))
    vix_threshold_high: float = Field(default=25.0)
    vix_threshold_extreme: float = Field(default=35.0)

    # ── Storage ───────────────────────────────────────────────────────────────
    duckdb_path: Path = Field(default=Path("data/quant_engine.duckdb"))
    parquet_dir: Path = Field(default=Path("data/parquet"))

    # ── Monitoring ────────────────────────────────────────────────────────────
    alert_webhook_url: str = Field(default="https://hooks.example.com/alerts")
    alert_phone_number: str = Field(default="+910000000000")
    blotter_export_path: Path = Field(default=Path("data/blotter.csv"))

    # ── Backtest ──────────────────────────────────────────────────────────────
    backtest_ohlc_path: Path = Field(default=Path("data/sample_ohlc.csv"))
    backtest_slippage_pct: float = Field(default=0.05)
    backtest_brokerage_pct: float = Field(default=0.03)

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return upper

    @field_validator("log_format")
    @classmethod
    def _validate_log_format(cls, v: str) -> str:
        if v not in {"json", "console"}:
            raise ValueError("log_format must be 'json' or 'console'")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the singleton Settings instance.
    Using lru_cache ensures we parse the environment exactly once
    and the same object is shared across the entire process.
    """
    return Settings()
