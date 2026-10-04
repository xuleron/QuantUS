"""Generate realistic synthetic data based on actual market characteristics."""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def generate_qqq_like_data(
    symbol: str,
    start_date: str,
    end_date: str,
    initial_price: float = 250.0,
    seed: int = None,
) -> pd.DataFrame:
    """
    Generate QQQ-like data with realistic characteristics:
    - Annual return: ~15-25% (bull market)
    - Volatility: ~25-35% annualized
    - Drawdowns: -15% to -30% typical
    - Trends: 3-6 month up/down trends
    - Mean reversion: Bounces back from extremes
    """
    if seed is not None:
        np.random.seed(seed)

    dates = pd.bdate_range(start=start_date, end=end_date)
    n_days = len(dates)

    # QQQ characteristics
    daily_volatility = 0.015  # 1.5% daily volatility (annualized ~24%)
    annual_drift = 0.00065   # ~16% annual return (0.065% daily)

    close_prices = np.zeros(n_days)
    close_prices[0] = initial_price

    # Create market regimes
    regime_length = 60  # 3 months of same regime
    n_regimes = n_days // regime_length + 1
    regimes = np.repeat(np.random.choice([0.5, 1.0, 1.5], n_regimes), regime_length)[:n_days]

    for i in range(1, n_days):
        # Base drift
        drift = annual_drift * regimes[i]

        # Volatility varies by regime
        vol = daily_volatility * (0.8 + 0.4 * regimes[i])

        # Random walk with drift
        dW = np.random.normal(0, 1)
        ret = drift + vol * dW
        close_prices[i] = close_prices[i-1] * (1 + ret)

        # Mean reversion on extreme moves
        if i > 20:
            recent_ma = np.mean(close_prices[max(0, i-20):i])
            if close_prices[i] > recent_ma * 1.15:
                close_prices[i] = close_prices[i-1]  # Skip this extreme
            elif close_prices[i] < recent_ma * 0.85:
                close_prices[i] = close_prices[i-1] * 1.01  # Bounce

    # Generate OHLC
    data = []
    for i, date in enumerate(dates):
        close = close_prices[i]

        # Realistic intraday action
        if np.random.random() < 0.55:  # Slightly bullish bias
            open_price = close * np.random.uniform(0.994, 0.999)
            high = close * np.random.uniform(1.001, 1.008)
            low = min(open_price, close) * np.random.uniform(0.992, 0.999)
        else:
            open_price = close * np.random.uniform(1.001, 1.006)
            high = open_price * np.random.uniform(1.001, 1.005)
            low = close * np.random.uniform(0.992, 0.999)

        high = max(high, close, open_price)
        low = min(low, close, open_price)

        # Volume (spikes on big moves)
        base_volume = 40_000_000
        if abs((close - open_price) / open_price) > 0.02:
            volume = int(base_volume * np.random.uniform(1.2, 1.8))
        else:
            volume = int(base_volume * np.random.uniform(0.8, 1.2))

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

    # Calculate actual performance
    total_return = (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]

    return df, total_return


def generate_tech_stock_data(
    symbols: list,
    start_date: str,
    end_date: str,
) -> dict:
    """Generate data for tech stocks with different volatility profiles."""
    data = {}

    for i, symbol in enumerate(symbols):
        # Different characteristics for different stocks
        if 'High' in symbol:  # High growth (more volatile)
            initial = 50 + i * 10
            seed = 1000 + i
        elif 'Low' in symbol:  # More stable
            initial = 150 + i * 10
            seed = 2000 + i
        else:  # Medium
            initial = 100 + i * 15
            seed = 3000 + i

        df, ret = generate_qqq_like_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_price=initial,
            seed=seed,
        )

        data[symbol] = df

        print(f"Generated {symbol:15s} | Price: ${df['Close'].iloc[0]:7.2f} → ${df['Close'].iloc[-1]:7.2f} | Return: {ret:7.2%}")

    return data


def generate_test_dataset(
    stocks: list = None,
    start_date: str = '2023-01-01',
    end_date: str = '2024-12-31',
) -> dict:
    """Generate realistic tech stock dataset."""
    if stocks is None:
        stocks = [
            'High_Growth_1', 'High_Growth_2', 'High_Growth_3',  # NVDA, TSLA like
            'Medium_Growth_1', 'Medium_Growth_2', 'Medium_Growth_3',  # MSFT like
            'Stable_1', 'Stable_2', 'Stable_3',  # QQQ-like average
        ]

    return generate_tech_stock_data(stocks, start_date, end_date)
