import datetime
import pandas as pd
import requests

def is_holiday(date: datetime.date) -> bool:
    # Check if the date is a weekend (Saturday or Sunday)
    if date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
        print(f"{date} is a weekend, market is closed.")
        return True
    
    headers = {'user-agent': 'PostmanRuntime/7.26.5'}
    endpoint = "https://www.nseindia.com/api/holiday-master?type=trading"
    
    try:
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()  # Raise an error for a bad HTTP status
    except requests.exceptions.RequestException as e:
        print(f"Error fetching holiday data: {e}")
        return False
    
    try:
        holidays_json = response.json().get('FO', [])
        holidays_df = pd.DataFrame(holidays_json)
        
        if holidays_df.empty:
            print("No holiday data available.")
            return False
        
        holidays_df['tradingDate'] = pd.to_datetime(holidays_df['tradingDate'])
        
        # Check if the date is in the holidays dataframe
        return pd.Timestamp(date) in holidays_df['tradingDate'].values
    except (ValueError, KeyError) as e:
        print(f"Error processing holiday data: {e}")
        return False
