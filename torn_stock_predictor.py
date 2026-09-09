import time
import requests
from datetime import datetime

# CONFIGURATION
API_KEY = "public_api-key"
SELL_FEE_PCT = 0.001           # 0.1% Torn stock exchange fee
TARGET_NET_PROFIT = 1.00       # Target: +1.00% NET profit AFTER 0.1% fee
STOP_LOSS_NET = -0.75          # Stop loss: -0.75% NET loss AFTER 0.1% fee
MIN_HOLD_TICKS = 60            # Minimum hold: 60 minutes (1 hour)
MAX_HOLD_TICKS = 180           # Maximum hold: 180 minutes (3 hours max window)
POLL_INTERVAL = 60             # 60 seconds per check

# Filters 
MIN_MOMENTUM_PCT = 0.08        # 5-minute trend growth must be >= +0.08%


TORN_STOCKS_URL = f"https://api.torn.com/torn/?selections=stocks&key={API_KEY}"

stock_metadata = {}    # {stock_id: {"name": str, "acronym": str}}
price_history = {}     # {stock_id: [prices]}
active_trades = {}     # {stock_id: {"buy_price": float, "entry_tick": int}}
current_tick = 0

def fetch_torn_stocks():
    try:
        response = requests.get(TORN_STOCKS_URL, timeout=10)
        data = response.json()
        if "error" in data:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] API Error: {data['error']}")
            return None
        return data.get("stocks", {})
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Network error: {e}")
        return None

def calculate_net_pnl(buy_price, current_price):
    """Calculates net PnL factoring in the 0.1% exchange fee."""
    net_sell_price = current_price * (1.0 - SELL_FEE_PCT)
    return ((net_sell_price - buy_price) / buy_price) * 100.0

def evaluate_market(stocks_data):
    global current_tick
    current_tick += 1
    timestamp = datetime.now().strftime("%H:%M:%S")

    # 1. Update Price Cache
    for s_id, info in stocks_data.items():
        if s_id not in stock_metadata:
            stock_metadata[s_id] = {
                "name": info.get("name", "Unknown"),
                "acronym": info.get("acronym", "???")
            }

        price = float(info.get("current_price", 0))
        if s_id not in price_history:
            price_history[s_id] = []
        price_history[s_id].append(price)
        if len(price_history[s_id]) > 30:
            price_history[s_id].pop(0)

    # 2. Manage Active Positions (Enforcing 1-Hour Minimum Lock)
    active_ids = list(active_trades.keys())
    for s_id in active_ids:
        pos = active_trades[s_id]
        meta = stock_metadata[s_id]
        cur_price = price_history[s_id][-1]
        ticks_held = current_tick - pos["entry_tick"]
        net_pnl = calculate_net_pnl(pos["buy_price"], cur_price)

        # Locked Phase: Under 1 hour (60 ticks)
        if ticks_held < MIN_HOLD_TICKS:
            remaining = MIN_HOLD_TICKS - ticks_held
            print(f" [LOCKED HOLD] {meta['acronym']} | Min {ticks_held}/{MIN_HOLD_TICKS} ({remaining}m to unlock) | Net: {net_pnl:+.2f}%")
            continue

        # Unlocked Phase: Check Exit Targets
        if net_pnl >= TARGET_NET_PROFIT:
            print(f"\n [SELL NOW - TARGET REACHED]")
            print(f"   Stock: {meta['name']} ({meta['acronym']})")
            print(f"   Held for: {ticks_held} min | Buy: ${pos['buy_price']:,.2f} -> Sell: ${cur_price:,.2f}")
            print(f"   Net Gain (after fee): +{net_pnl:.2f}%\n")
            del active_trades[s_id]
            continue

        if net_pnl <= STOP_LOSS_NET:
            print(f"\n [SELL NOW - STOP LOSS]")
            print(f"   Stock: {meta['name']} ({meta['acronym']})")
            print(f"   Held for: {ticks_held} min | Buy: ${pos['buy_price']:,.2f} -> Sell: ${cur_price:,.2f}")
            print(f"   Net Loss (after fee): {net_pnl:.2f}%\n")
            del active_trades[s_id]
            continue

        if ticks_held >= MAX_HOLD_TICKS:
            print(f"\n [SELL NOW - MAX TIMEOUT REACHED]")
            print(f"   Stock: {meta['name']} ({meta['acronym']})")
            print(f"   Final Net Return: {net_pnl:+.2f}%\n")
            del active_trades[s_id]
            continue

        print(f" [UNLOCKED HOLD] {meta['acronym']} | Min {ticks_held}/{MAX_HOLD_TICKS} | Net: {net_pnl:+.2f}%")

    # 3. Market Pulse & Entry Screening (5-minute Trend Momentum)
    top_mover_ticker = None
    top_mover_gain = -999.0
    candidates = []

    for s_id, history in price_history.items():
        if len(history) < 6:
            continue

        p_5m_ago = history[-6]
        p_cur = history[-1]
        delta_5m = ((p_cur - p_5m_ago) / p_5m_ago) * 100.0 if p_5m_ago > 0 else 0

        if delta_5m > top_mover_gain:
            top_mover_gain = delta_5m
            top_mover_ticker = stock_metadata[s_id]["acronym"]

        # Buy criteria: Sustained 5-minute upward trend >= +0.08%
        if delta_5m >= MIN_MOMENTUM_PCT and s_id not in active_trades:
            candidates.append((s_id, delta_5m, p_cur))

    pulse = f"Top 5m Mover: {top_mover_ticker} ({top_mover_gain:+.2f}%)" if top_mover_ticker else "Market Flat"
    print(f"--- [TICK #{current_tick} @ {timestamp}] {pulse} | Tracking {len(price_history)} stocks ---")

    # 4. Trigger Alerts
    for s_id, gain_5m, p_cur in candidates:
        meta = stock_metadata[s_id]
        print(f"\n [HOURLY TREND BUY ALERT]")
        print(f"   Stock Name : {meta['name']}")
        print(f"   Ticker     : {meta['acronym']} (ID: {s_id})")
        print(f"   Buy Price  : ${p_cur:,.2f}")
        print(f"   5m Trend   : +{gain_5m:.2f}%")
        print(f"   Rules      : Min hold 60 min | Target Net: >= +{TARGET_NET_PROFIT}% | Stop: <= {STOP_LOSS_NET}%\n")

        active_trades[s_id] = {
            "buy_price": p_cur,
            "entry_tick": current_tick
        }

def main():
    print("Initializing Torn 1-Hour Trend Trader (0.1% Fee)...")
    while True:
        data = fetch_torn_stocks()
        if data:
            evaluate_market(data)
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()