from datetime import datetime, timedelta
import time
import requests
from backand.database.database import Session
from backand.database.models import Crypto

# --- FETCH KLINES ---
def fetch_klines(symbol="TONUSDT", interval="60", start=None, limit=200):
    url = "https://api.bybit.com/v5/market/kline"
    params = {"category": "spot", "symbol": symbol, "interval": interval, "limit": limit}
    if start:
        params["start"] = start
    print(f"🔍 Запит: {params}")
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()
    if data.get("retCode") != 0:
        raise Exception(f"❌ API error: {data}")
    return data["result"]["list"]

# --- FETCH LAST MONTH (змінили на останні 3 дні) ---
def fetch_last_month_klines(symbol="TONUSDT", interval="60"):
    all_candles = []

    # беремо 3 дні назад від зараз
    start_dt = datetime.utcnow() - timedelta(days=3)
    start = int(start_dt.timestamp())  # у секундах
    last_ts = None

    while True:
        candles = fetch_klines(symbol, interval, start=start, limit=200)
        if not candles:
            break

        all_candles.extend(candles)

        new_ts = int(candles[-1][0]) // 1000
        if last_ts == new_ts:
            break
        last_ts = new_ts

        start = new_ts + 1
        time.sleep(0.2)

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
