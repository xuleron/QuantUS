"""Data loading and preprocessing."""
import pandas as pd
import yfinance as yf
from typing import Dict, List, Optional


def load_data(
    symbols: List[str],
    start_date: str,
    end_date: str,
    interval: str = '1d',
) -> Dict[str, pd.DataFrame]:
    """
    Load historical data from yfinance.

    Args:
        symbols: List of ticker symbols
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        interval: Data interval (1m, 5m, 1h, 1d, etc.)

    Returns:
        Dict of {symbol: DataFrame}
    """
    data = {}
    for symbol in symbols:
        print(f"Loading {symbol}...")
        try:
            df = yf.download(
                symbol,
                start=start_date,
                end=end_date,
                interval=interval,
                progress=False,
            )
            if isinstance(df.columns, pd.MultiIndex):
                df = df[symbol]
            df = df.dropna()
            if len(df) > 0:
                data[symbol] = df
        except Exception as e:
            print(f"Failed to load {symbol}: {e}")

    return data


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare technical features from OHLCV data."""
    df = df.copy()

    # MA
    df['MA5'] = df['Close'].rolling(5).mean()
    df['MA10'] = df['Close'].rolling(10).mean()
    df['MA20'] = df['Close'].rolling(20).mean()
    df['MA50'] = df['Close'].rolling(50).mean()

    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))

    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['Signal']

    # ATR
    high_low = df['High'] - df['Low']
    high_close = abs(df['High'] - df['Close'].shift())
    low_close = abs(df['Low'] - df['Close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()

    # Bollinger Bands
    sma = df['Close'].rolling(20).mean()
    std = df['Close'].rolling(20).std()
    df['BB_Upper'] = sma + (std * 2)
    df['BB_Lower'] = sma - (std * 2)
    df['BB_Mid'] = sma

    # Volume
    df['Volume_MA'] = df['Volume'].rolling(20).mean()
    df['Volume_Ratio'] = df['Volume'] / df['Volume_MA']

    return df.dropna()
