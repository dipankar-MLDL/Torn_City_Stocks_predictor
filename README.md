# Torn City Stocks Predictor & Momentum Trader

A real-time, rule-based paper-trading bot and market scanner for Torn City. The tool tracks price trends using the public Torn API, detects 5-minute upward momentum, accounts for Torn's 0.1% transaction fee, and signals simulated buy and sell triggers.

---

## Key Features

* **Real-Time Polling:** Fetches active market data on a 60-second polling cycle.
* **5-Minute Trend Momentum:** Flags assets gaining $\ge +0.08\%$ over a rolling 5-minute window.
* **Exchange Fee Calculation:** Automatically deducts Torn's 0.1% exchange fee (`0.001`) from exit prices to calculate actual net profit/loss.
* **Structured Trade Lifecycle:**
  * **1-Hour Minimum Lock:** Simulates an enforced 60-minute holding constraint.
  * **Dynamic Exits:** Alerts at $+1.00\%$ net target profit or $-0.75\%$ stop-loss.
  * **Timeout Cap:** Automatic exit after 180 minutes (3 hours).

---

## Setup & Running

### 1. Requirements

Ensure Python 3.8+ is installed, then install the required dependency:

```bash
pip install requests
```

### 2. Configure API Key

Provide your Torn API key (public access level is sufficient). You can pass it as an environment variable or edit the config variable in `torn_stock_predictor.py`:

```bash
export TORN_API_KEY="your_api_key_here"
```

### 3. Run the Bot

```bash
python torn_stock_predictor.py
```

---

## Disclaimer

This project is intended strictly for analytical simulation and paper trading. It uses read-only public endpoints from the official Torn API and does not automate any in-game actions.
