# Cloud Run Environment Variables Guide

## Required Environment Variables

Add these environment variables in the Cloud Run console:

### 1. Trading API Keys (REQUIRED)
```
ALPACA_API_KEY=your_alpaca_api_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

**Where to get:** https://alpaca.markets/
- Sign up for a free paper trading account
- Get your API keys from the dashboard

### 2. Stock Configuration (REQUIRED)
```
STOCKS=AAPL,MSFT,GOOGL,AMZN,TSLA
```

**Format:** Comma-separated list of stock symbols (no spaces)
**Example:** `STOCKS=AAPL,MSFT,GOOGL,AMZN,TSLA,NVDA,META`

### 3. Trading Settings (OPTIONAL - defaults shown)
```
POSITION_SIZE=1000.0
TIMEZONE=America/New_York
LOG_LEVEL=INFO
```

**POSITION_SIZE:** Dollar amount to invest per stock (default: 1000.0)
**TIMEZONE:** Timezone for market hours (default: America/New_York)
**LOG_LEVEL:** Logging level - DEBUG, INFO, WARNING, ERROR (default: INFO)

### 4. Stock Data API (OPTIONAL)
```
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
```

**Note:** This is optional. The bot will use Yahoo Finance as a fallback if not provided.
**Where to get:** https://www.alphavantage.co/support/#api-key

---

## How to Add Environment Variables in Cloud Run

1. Go to: https://console.cloud.google.com/run
2. Click on your `trading-bot` service
3. Click **"Edit & Deploy New Revision"**
4. Go to the **"Variables & Secrets"** tab
5. Click **"Add Variable"** for each environment variable
6. Enter the **Name** and **Value**
7. Click **"Deploy"** at the bottom

---

## Minimum Required Variables

At minimum, you MUST set:
- `ALPACA_API_KEY`
- `ALPACA_SECRET_KEY`
- `ALPACA_BASE_URL` (usually `https://paper-api.alpaca.markets`)
- `STOCKS` (comma-separated list)

---

## Example Complete Configuration

```
ALPACA_API_KEY=PKGE4LEF5L4QM5V3B5KWYXTN5Z
ALPACA_SECRET_KEY=7VwmRiKKFnzrxKfnfdgt98536To5FnJBoQUkTFpkbJym
ALPACA_BASE_URL=https://paper-api.alpaca.markets
STOCKS=AAPL,MSFT,GOOGL,AMZN,TSLA,NVDA,META
POSITION_SIZE=1000.0
TIMEZONE=America/New_York
LOG_LEVEL=INFO
```

---

## Important Notes

- **PORT** is automatically set by Cloud Run - DO NOT set this manually
- Use **paper trading** API URL (`https://paper-api.alpaca.markets`) for testing
- Never commit real API keys to git or share them publicly
- The bot will start trading once these variables are set

