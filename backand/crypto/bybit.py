import websocket
import json
import ssl
import time

def on_message(ws, message):
    print("📩", message)

def on_error(ws, error):
    print("❌ Error:", error)

def on_close(ws, close_status_code, close_msg):
    print("🔌 Connection closed:", close_status_code, close_msg)

def on_open(ws):
    print("✅ Connected")
    ws.send(json.dumps({"op": "subscribe", "args": ["tickers.BTCUSDT"]}))
    ws.send(json.dumps({"op": "subscribe", "args": ["kline.1m.BTCUSDT"]}))

def run_ws():
    url = "wss://stream.bybit.com/v5/public/spot"
    ws = websocket.WebSocketApp(
        url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

if __name__ == "__main__":
    while True:
        try:
            run_ws()
        except Exception as e:
            print("⚠️ Reconnecting in 5s...", e)
            time.sleep(5)
