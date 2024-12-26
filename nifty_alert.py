import os
import requests
import yfinance as yf
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram Bot API details
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# Nifty 50 symbol and threshold
NIFTY_SYMBOL = '^NSEI'
THRESHOLD = -0.5  # -0.5% drop for hourly alert

# Initialize the Pyrogram client
app = Client("nifty_monitor_bot", api_id=API_ID, api_hash=API_HASH, bot_token=TELEGRAM_BOT_TOKEN)


# Function to send Telegram message
def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        params = {'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            print("Telegram message sent successfully.")
        else:
            print(f"Failed to send Telegram message. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error in sending Telegram message: {e}")


def get_nifty_data(period='5d'):
    try:
        nifty = yf.Ticker(NIFTY_SYMBOL)
        nifty_data = nifty.history(period=period)
        if not nifty_data.empty:
            last_date = nifty_data.index[-1].date()
            print(f"Fetched Nifty 50 data successfully. Last available data is for {last_date}.")
        else:
            print("Fetched Nifty 50 data is empty. Please check the source.")
        return nifty_data
    except Exception as e:
        print(f"Error in fetching Nifty 50 data: {e}")
        return None


# Function to calculate percentage change
def calculate_percentage_change(data):
    try:
        if len(data) < 2:
            print("Not enough data for calculating percentage change.")
            return None

        last_close = data['Close'].iloc[-1]
        previous_close = data['Close'].iloc[-2]
        percentage_change = (last_close - previous_close) / previous_close * 100
        print(f"Calculated percentage change: {percentage_change:.2f}%")
        return percentage_change
    except Exception as e:
        print(f"Error in calculating percentage change: {e}")
        return None


# Function to calculate average price
def calculate_average_price(data):
    try:
        if data.empty:
            print("No data available for calculating average price.")
            return None
        average_price = data['Close'].mean()
        print(f"Calculated average price: ₹{average_price:.2f}")
        return average_price
    except Exception as e:
        print(f"Error in calculating average price: {e}")
        return None


# Function to determine color based on percentage change
def determine_color(percentage_change):
    if percentage_change > 0:
        return "🟢"
    elif percentage_change < 0:
        return "🔴"
    else:
        return "⚫"  # For 0% change


# Function to monitor Nifty 50 hourly
def hourly_monitor(triggered_manually=False):
    print("Hourly monitor check triggered.")
    if not triggered_manually and not is_market_open():
        print("Market is closed (holiday or weekend). Skipping hourly monitor.")
        return

    print("Market is open. Running hourly monitor.")
    nifty_data = get_nifty_data()
    if nifty_data is None or nifty_data.empty:
        print("Nifty data fetch failed or is empty. Skipping alert.")
        return

    pct_change = calculate_percentage_change(nifty_data)
    if pct_change is None:
        print("Percentage change calculation failed. Skipping alert.")
        return

    if pct_change < THRESHOLD:  # Trigger alert if percentage change meets threshold
        color = determine_color(pct_change)
        message = f"""⏰ *Hourly Nifty 50 Alert:*\n
        Nifty 50 is {color} DOWN by {pct_change:.2f}% 📉\n
        Trigger: {"Manual" if triggered_manually else "Automatic"}"""
        send_telegram_message(message)
        print("Hourly alert message sent successfully.")
    else:
        if triggered_manually:
            message = f"""📢 *Hourly Update:*\n
            Current Nifty 50 percentage change is *{pct_change:.2f}%* {determine_color(pct_change)}\n
            No significant threshold breach detected."""
            send_telegram_message(message)
            print("Hourly update message sent manually.")
        else:
            print(f"No hourly alert triggered. Current percentage change: *{pct_change:.2f}%*")


# Function to send daily status
def daily_status():
    print("Daily status check triggered.")
    nifty_data = get_nifty_data(period='5d')  # Fetch up to 5 days of data
    if nifty_data is None or nifty_data.empty:
        print("Not enough data for daily status.")
        return

    try:
        last_close = nifty_data['Close'].iloc[-1]
        previous_close = nifty_data['Close'].iloc[-2]
        percentage_change = (last_close - previous_close) / previous_close * 100

        # Compare with 1mo, 3mo, and 6mo averages
        data_1mo = get_nifty_data(period='1mo')
        avg_1mo = calculate_average_price(data_1mo)

        data_3mo = get_nifty_data(period='3mo')
        avg_3mo = calculate_average_price(data_3mo)

        data_6mo = get_nifty_data(period='6mo')
        avg_6mo = calculate_average_price(data_6mo)

        trend_1mo = "*UP*" if last_close > avg_1mo else "*DOWN*"
        diff_1mo = (last_close - avg_1mo) / avg_1mo * 100 if avg_1mo else 0

        trend_3mo = "*UP*" if last_close > avg_3mo else "*DOWN*"
        diff_3mo = (last_close - avg_3mo) / avg_3mo * 100 if avg_3mo else 0

        trend_6mo = "*UP*" if last_close > avg_6mo else "*DOWN*"
        diff_6mo = (last_close - avg_6mo) / avg_6mo * 100 if avg_6mo else 0

        message = (
            f"📊 *Daily Nifty 50 Update:*\n"
            f"1. Last closing price: ₹{last_close:.2f}\n"
            f"2. Percentage change from yesterday: *{percentage_change:.2f}%* {determine_color(percentage_change)}\n"
            f"3. 1-month average (₹{avg_1mo:.2f}): {trend_1mo} *({diff_1mo:.2f}%)* {determine_color(diff_1mo)}\n"
            f"4. 3-month average (₹{avg_3mo:.2f}): {trend_3mo} *({diff_3mo:.2f}%)* {determine_color(diff_3mo)}\n"
            f"5. 6-month average (₹{avg_6mo:.2f}): {trend_6mo} *({diff_6mo:.2f}%)* {determine_color(diff_6mo)}\n"
        )
        send_telegram_message(message)
        print("Daily status message sent successfully.")
    except Exception as e:
        print(f"Error in daily status: {e}")


# Function to check if today is a market day and market is open
def is_market_open():
    today = datetime.now().date()
    current_time = datetime.now().time()
    market_start = time(9, 15)
    market_end = time(15, 30)

    if today.weekday() >= 5:  # Check if today is a weekend
        return False

    if market_start <= current_time <= market_end:  # Check market hours
        return True

    return False


# Scheduler setup
scheduler = BackgroundScheduler()

scheduler.add_job(daily_status, 'cron', hour=17, minute=0)  # Daily at 5:00 PM
scheduler.start()

# Telegram Bot Commands
@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply(
        "Welcome to the Nifty 50 Monitoring Bot! Use the buttons below to interact with the bot.",
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📢 Hourly Update", callback_data="hourly_update")],
                [InlineKeyboardButton("📊 Daily Update", callback_data="daily_update")],
            ]
        ),
    )


@app.on_callback_query(filters.regex("hourly_update"))
async def hourly_update(client, callback_query):
    await callback_query.answer("Fetching Hourly Update...")
    hourly_monitor(triggered_manually=True)


@app.on_callback_query(filters.regex("daily_update"))
async def daily_update(client, callback_query):
    await callback_query.answer("Fetching Daily Update...")
    daily_status()


# Run the bot
print("Starting Nifty 50 Monitoring Bot...")
app.run()
