# Nifty Den Den Mushi

This is a Telegram bot that monitors the Nifty 50 index and sends hourly and daily alerts based on percentage changes in the index.

## Features
- Hourly alerts when Nifty 50 drops more than 0.5%
- Daily status update on Nifty 50 performance over 1-month, 3-month, and 6-month periods
- Uses Pyrogram for Telegram bot interactions and yfinance for fetching market data

## Setup

### Prerequisites
- Python 3.x
- Install dependencies via `pip install -r requirements.txt`

### Environment Variables
- `API_ID`: Your Pyrogram API ID
- `API_HASH`: Your Pyrogram API hash
- `TELEGRAM_BOT_TOKEN`: Telegram bot token
- `CHAT_ID`: Telegram chat ID to send messages

### Deployment
- You can deploy this bot on platforms like Render or AWS Lambda for serverless execution.

