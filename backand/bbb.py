from datetime import datetime, timedelta
import time
import requests
from backand.database.database import Session
from backand.database.models import Crypto

# --- FETCH KLINES ---
def fetch_klines(symbol="TONUSDT", interval="60", start=None, end=None, limit=200):
    url = "https://api.bybit.com/v5/market/kline"
    params = {"category": "spot", "symbol": symbol, "interval": interval, "limit": limit}
    if start:
        params["start"] = start
    if end:
        params["end"] = end

    print(f"🔍 Запит: {params}")
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("retCode") != 0:
            raise Exception(f"❌ API error: {data}")

        return data["result"]["list"]

    except requests.exceptions.RequestException as e:
        raise Exception(f"❌ Network error: {e}")


# --- FETCH LAST MONTH (тепер це останні 3 місяці) ---
def fetch_last_month_klines(symbol="TONUSDT", interval="60"):
    all_candles = []

    # беремо 90 днів назад від зараз
    end_date = datetime.utcnow()
    start_date_limit = end_date - timedelta(days=90)

    end_timestamp = int(end_date.timestamp() * 1000)

    while True:
        candles = fetch_klines(symbol, interval, end=end_timestamp, limit=400)

        if not candles:
            break

        oldest_candle_ts = int(candles[-1][0])
        new_candles = [c for c in candles if int(c[0]) < end_timestamp]
        all_candles.extend(new_candles)

        end_timestamp = oldest_candle_ts

        if oldest_candle_ts < int(start_date_limit.timestamp() * 1000):
            break

    all_candles.sort(key=lambda x: int(x[0]))

    return all_candles




# --- SAVE TO DB (no duplicates) ---
def save_klines(candles, symbol="TONUSDT", interval="1h"):
    with Session() as session:
        for c in candles:
            ts, o, h, l, cl, v, *_ = c
            timestamp_sec = int(ts) // 1000
            exists = session.query(Crypto).filter_by(
                symbol=symbol, interval=interval, timestamp=timestamp_sec
            ).first()
            if exists:
                continue
            crypto = Crypto(
                symbol=symbol,
                interval=interval,
                timestamp=timestamp_sec,
                open=float(o),
                high=float(h),
                low=float(l),
                close=float(cl),
                volume=float(v)
            )
            session.add(crypto)
        session.commit()
        print(f"✅ Saved {len(candles)} candles into DB (duplicates пропущено)")


# --- Виклик ---
# if __name__ == "__main__":
#     candles = fetch_last_month_klines("TONUSDT", interval="60")
#     save_klines(candles, "TONUSDT", "1h")
