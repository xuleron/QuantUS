"""Improved synthetic data with realistic market dynamics."""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def generate_realistic_ohlcv(
    symbol: str,
    start_date: str,
    end_date: str,
    initial_price: float = 100.0,
    trend: float = 0.0008,
    volatility: float = 0.03,
    momentum_periods: int = 20,  # Add momentum effect
    mean_reversion: float = 0.05,  # Add mean reversion
    seed: int = None,
) -> pd.DataFrame:
    """
    Generate realistic OHLCV data with market dynamics.

    Includes:
    - Trends (like real stocks)
    - Volatility clustering (risk on/off periods)
    - Momentum effects
    - Mean reversion
    - Volume spikes
    """
    if seed is not None:
        np.random.seed(seed)

    dates = pd.bdate_range(start=start_date, end=end_date)
    n_days = len(dates)

    # Generate price path with multiple regimes
    close_prices = np.zeros(n_days)
    close_prices[0] = initial_price

    # Volatility regime switching (50% calm, 30% volatile, 20% crash)
    regime_type = np.random.choice([1, 2, 3], n_days, p=[0.5, 0.3, 0.2])

    # Volatility multipliers
    vol_mult = np.where(regime_type == 1, 0.8,  # Calm: lower vol
                       np.where(regime_type == 2, 1.5,  # Volatile: higher vol
                               0.6))  # Crash: directional, lower vol

    # Trend multiplier (trending regime changes direction)
    trend_mult = np.where(regime_type == 3, -1, 1)

    for i in range(1, n_days):
        # Base price movement
        drift = trend * trend_mult[i] if regime_type[i] == 3 else trend
        vol = volatility * vol_mult[i]

        # Random walk
        dW = np.random.normal(0, 1)
        close_prices[i] = close_prices[i-1] * np.exp((drift - 0.5 * vol**2) + vol * dW)

        # Add momentum (prices tend to continue in direction)
        if i > momentum_periods:
            recent_return = (close_prices[i] - close_prices[i-momentum_periods]) / close_prices[i-momentum_periods]
            momentum_boost = recent_return * 0.1  # 10% of recent momentum
            close_prices[i] *= (1 + momentum_boost)

        # Add mean reversion (prices tend to mean)
        if i > 50:
            mean_price = np.mean(close_prices[max(0, i-50):i])
            if close_prices[i] > mean_price * 1.1:
                close_prices[i] *= (1 - mean_reversion * 0.01)
            elif close_prices[i] < mean_price * 0.9:
                close_prices[i] *= (1 + mean_reversion * 0.01)

    # Generate OHLC from close prices with realistic intraday action
    data = []
    for i, date in enumerate(dates):
        close = close_prices[i]

        # Intraday trading (usually: open lower, high reached, close recovered)
        if np.random.random() < 0.6:
            open_price = close * np.random.uniform(0.98, 1.00)
            high = close * np.random.uniform(1.00, 1.03)
            low = min(open_price, close) * np.random.uniform(0.97, 1.00)
        else:  # Gap up day
            open_price = close * np.random.uniform(1.00, 1.02)
            high = open_price * np.random.uniform(1.00, 1.03)
            low = min(open_price, close) * np.random.uniform(0.97, 1.00)

        high = max(high, close, open_price)
        low = min(low, close, open_price)

        # Volume (increases on volatile days)
        base_vol = 1000000
        if regime_type[i] == 2:  # High vol days
            volume = int(np.random.lognormal(np.log(base_vol * 2), 0.5))
        else:
            volume = int(np.random.lognormal(np.log(base_vol), 0.5))

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


def generate_realistic_dataset(symbols: list, start_date: str, end_date: str) -> dict:
    """Generate realistic dataset with diverse stock profiles."""
    data = {}

    for i, symbol in enumerate(symbols):
        # Different stocks have different characteristics
        # Growth stocks: higher trend
        # Value stocks: lower volatility, mean reversion
        # Volatile stocks: higher volatility

        if i < 3:  # Growth stocks (high trend, higher vol)
            trend = 0.0012 + np.random.uniform(0, 0.0005)
            volatility = 0.035 + np.random.uniform(0, 0.015)
            initial_price = 100 + i * 50
        elif i < 6:  # Value stocks (stable, lower vol)
            trend = 0.0006 + np.random.uniform(0, 0.0003)
            volatility = 0.020 + np.random.uniform(0, 0.005)
            initial_price = 100 + i * 50
        else:  # Volatile stocks
            trend = 0.0010 + np.random.uniform(-0.0003, 0.0005)
            volatility = 0.040 + np.random.uniform(0, 0.020)
            initial_price = 100 + i * 50

        df = generate_realistic_ohlcv(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_price=initial_price,
            trend=trend,
            volatility=volatility,
            seed=100 + i,
        )

        data[symbol] = df

        price_change = (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]
        print(f"Generated {symbol:12s} | Price: {df['Close'].iloc[0]:7.2f} → {df['Close'].iloc[-1]:7.2f} | Return: {price_change:7.2%}")

    return data
