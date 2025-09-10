import requests
import time
from datetime import datetime, timedelta
from backand.database.database import Session
from backand.database.models import Crypto


with Session() as session:
    candles = session.query(Crypto).filter_by(symbol="BTCUSDT").order_by(Crypto.timestamp).all()
    for c in candles:
        print(c.timestamp, c.open, c.high, c.low, c.close, c.volume)

# --- FETCH KLINES ---
def fetch_klines(symbol="ETHUSDT", interval="60", start=None, limit=200):
    url = "https://api.bybit.com/v5/market/kline"
    params = {
        "category": "spot",
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    if start:
        params["start"] = start

    print(f"🔍 Запит: {params}")  # логування

    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()

    if data.get("retCode") != 0:
        raise Exception(f"❌ API error: {data}")

    return data["result"]["list"]

# --- FETCH LAST MONTH ---
def fetch_last_month_klines(symbol="ETHUSDT", interval="60"):
    all_candles = []
    start = int((datetime.utcnow() - timedelta(days=30)).timestamp() * 1000)  # 30 днів тому
    last_ts = None

    while True:
        candles = fetch_klines(symbol, interval, start=start, limit=200)
        if not candles:
            break

        all_candles.extend(candles)

        new_ts = int(candles[-1][0])
        if new_ts == last_ts or new_ts > int(time.time() * 1000):
            break
        last_ts = new_ts

        start = new_ts + 1
        time.sleep(0.2)  # анти rate-limit

    return all_candles

# --- SAVE TO DB (no duplicates) ---
def save_klines(candles, symbol="ETHUSDT", interval="1h"):
    with Session() as session:
        for c in candles:
            ts, o, h, l, cl, v, turnover = c
            timestamp_sec = int(int(ts) // 1000)

            # Перевірка, чи свічка вже є
            exists = session.query(Crypto).filter_by(
                symbol=symbol,
                interval=interval,
                timestamp=timestamp_sec
            ).first()

            if exists:
                continue  # пропускаємо дублікат

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
            session.add(crypto)  # просто додаємо новий рядок
        session.commit()
        print(f"✅ Saved {len(candles)} candles into DB (duplicates пропущено)")


# --- RUN EXAMPLE ---
# if __name__ == "__main__":
#     candles = fetch_last_month_klines("ETHUSDT", interval="60")
#     save_klines(candles, "ETHUSDT", "1h")
