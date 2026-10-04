"""Synthetic data generation for backtesting."""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List


def generate_synthetic_ohlcv(
    symbol: str,
    start_date: str,
    end_date: str,
    initial_price: float = 100.0,
    trend: float = 0.001,
    volatility: float = 0.02,
    seed: int = None,
) -> pd.DataFrame:
    """
    Generate synthetic OHLCV data using geometric Brownian motion.

    Args:
        symbol: Stock symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        initial_price: Starting price
        trend: Daily trend (drift)
        volatility: Daily volatility
        seed: Random seed for reproducibility

    Returns:
        DataFrame with OHLCV data
    """
    if seed is not None:
        np.random.seed(seed)

    # Create date range (business days only)
    dates = pd.bdate_range(start=start_date, end=end_date)
    n_days = len(dates)

    # Generate price path using GBM
    dt = 1.0
    close_prices = np.zeros(n_days)
    close_prices[0] = initial_price

    for i in range(1, n_days):
        dW = np.random.normal(0, np.sqrt(dt))
        close_prices[i] = close_prices[i-1] * np.exp((trend - 0.5 * volatility**2) * dt + volatility * dW)

    # Generate OHLC from close prices
    data = []
    for i, date in enumerate(dates):
        close = close_prices[i]

        # Intraday movements
        open_price = close * np.exp(np.random.normal(0, volatility * 0.5))
        high = max(open_price, close) * np.exp(abs(np.random.normal(0, volatility * 0.3)))
        low = min(open_price, close) * np.exp(-abs(np.random.normal(0, volatility * 0.3)))

        # Volume (log-normal distributed)
        volume = int(np.random.lognormal(10, 1))

        data.append({
            'Date': date,
            'Open': open_price,
            'High': high,
            'Low': low,
            'Close': close,
            'Volume': volume,
        })

    df = pd.DataFrame(data)
    df.set_index('Date', inplace=True)
    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

    return df


def generate_dataset(
    symbols: List[str],
    start_date: str,
    end_date: str,
    **kwargs,
) -> Dict[str, pd.DataFrame]:
    """
    Generate synthetic dataset for multiple symbols.

    Args:
        symbols: List of ticker symbols
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        **kwargs: Additional arguments for generate_synthetic_ohlcv

    Returns:
        Dict of {symbol: DataFrame}
    """
    data = {}
    for i, symbol in enumerate(symbols):
        # Vary trend and volatility for diversity
        trend = 0.0005 + i * 0.0002
        volatility = 0.015 + (i % 3) * 0.005
        initial_price = 50 + i * 20

        data[symbol] = generate_synthetic_ohlcv(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_price=initial_price,
            trend=trend,
            volatility=volatility,
            seed=42 + i,
            **{k: v for k, v in kwargs.items() if k not in ['initial_price', 'trend', 'volatility']},
        )
        print(f"Generated {len(data[symbol])} days for {symbol} (price: {data[symbol]['Close'].iloc[0]:.2f} → {data[symbol]['Close'].iloc[-1]:.2f})")

    return data
