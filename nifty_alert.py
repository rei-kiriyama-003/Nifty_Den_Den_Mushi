import requests
import yfinance as yf
from apscheduler.schedulers.background import BackgroundScheduler
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, time
import os
from dotenv import load_dotenv
from holiday_checker import is_holiday  # Import the holiday checker module

# Load environment variables
load_dotenv()

# Telegram Bot API details
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# Nifty 50 symbol and threshold
NIFTY_SYMBOL = '^NSEI'
THRESHOLD = -0.5  # -0.5% drop for hourly alert

# Configure logging with rotating file handler
LOG_FILE = 'nifty_monitor.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=5),
        logging.StreamHandler()
    ]
)

# Function to send Telegram message
def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        params = {'chat_id': CHAT_ID, 'text': message}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            logging.info("Telegram message sent successfully.")
        else:
            logging.error(f"Failed to send Telegram message. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error in sending Telegram message: {e}")

# Function to fetch Nifty 50 data
def get_nifty_data(period='2d'):
    try:
        nifty = yf.Ticker(NIFTY_SYMBOL)
        nifty_data = nifty.history(period=period)
        if not nifty_data.empty:
            last_date = nifty_data.index[-1].date()
            logging.info(f"Fetched Nifty 50 data successfully. Last available data is for {last_date}.")
        else:
            logging.warning("Fetched Nifty 50 data is empty. Please check the source.")
        return nifty_data
    except Exception as e:
        logging.error(f"Error in fetching Nifty 50 data: {e}")
        return None

# Function to calculate percentage change
def calculate_percentage_change(data):
    try:
        last_close = data['Close'][-1]
        previous_close = data['Close'][-2]
        percentage_change = (last_close - previous_close) / previous_close * 100
        logging.info(f"Calculated percentage change: {percentage_change:.2f}%")
        return percentage_change
    except Exception as e:
        logging.error(f"Error in calculating percentage change: {e}")
        return None

# Function to check if today is a market day and market is open
def is_market_open():
    today = datetime.now().date()
    current_time = datetime.now().time()
    market_start = time(9, 15)
    market_end = time(15, 30)

    # Check if today is a weekend or holiday
    if today.weekday() >= 5 or is_holiday(today):
        return False

    # Check if current time is within market hours
    return market_start <= current_time <= market_end

# Function to monitor Nifty 50 hourly
def hourly_monitor():
    logging.info("Hourly monitor check triggered.")
    if is_market_open():
        logging.info("Market is open. Running hourly monitor.")
        nifty_data = get_nifty_data()
        if nifty_data is None:
            return

        pct_change = calculate_percentage_change(nifty_data)
        if pct_change is None:
            return

        if pct_change < THRESHOLD:
            message = f"🚨 Hourly Alert: Nifty 50 is DOWN by {pct_change:.2f}%!"
            send_telegram_message(message)
        else:
            logging.info(f"No hourly alert triggered. Current percentage change: {pct_change:.2f}%")
    else:
        logging.info("Market is closed (holiday or weekend). Skipping hourly monitor.")

# Function to send daily status
def daily_status():
    logging.info("Daily status check triggered.")
    today = datetime.now().date()
    if today.weekday() >= 5 or is_holiday(today):
        message = f"📢 Market Alert: The market is closed today ({today})."
        send_telegram_message(message)
        logging.info("Market closed alert sent.")
    else:
        logging.info("Running daily status.")
        nifty_data = get_nifty_data(period='1d')
        if nifty_data is None:
            return

        pct_change = calculate_percentage_change(nifty_data)
        last_close = nifty_data['Close'][-1]

        if pct_change is None:
            return

        message = f"📊 Daily Nifty 50 Update:\n"
        message += f"1. Last closing price: {last_close:.2f}\n"
        message += f"2. Percentage change from yesterday: {pct_change:.2f}%\n"
        send_telegram_message(message)


# Add a status logging job to the scheduler
def status_check():
    logging.info("Status Check: Script is running. Scheduler is active.")


# Scheduler setup
scheduler = BackgroundScheduler()

# Add job to check if market is open, and schedule tasks accordingly
def market_check_and_schedule():
    logging.info("Market check and schedule triggered.")
    if is_market_open():
        scheduler.add_job(hourly_monitor, 'cron', hour='9-15', minute=0)  # Hourly during market hours
        logging.info("Market is open. Scheduled hourly monitor.")
    else:
        scheduler.add_job(daily_status, 'cron', hour=23, minute=5)  # Run daily at 11:05 PM
        logging.info("Market is closed. Scheduled daily status.")

# Schedule the market check at the start of the day
scheduler.add_job(market_check_and_schedule, 'cron', hour=9, minute=0)

# Schedule the status check job every hour
scheduler.add_job(status_check, 'interval', hours=2)

# Start scheduler
scheduler.start()

# Main script
if __name__ == "__main__":
    logging.info("Nifty 50 monitoring script started.")
    try:
        while True:
            pass  # Keep the script running
    except (KeyboardInterrupt, SystemExit):
        logging.info("Shutting down Nifty 50 monitoring script.")
        scheduler.shutdown()
