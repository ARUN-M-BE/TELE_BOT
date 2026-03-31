import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import config
import datetime

def save_to_sheets(date, url, query, username, message_id):
    """
    Appends a row to the designated Google Sheet.
    """
    if config.SHEET_ID == "YOUR_GOOGLE_SHEET_ID" or (not config.SERVICE_ACCOUNT_FILE and not config.SERVICE_ACCOUNT_JSON):
        print("Skipping Google Sheets as no ID or credentials were provided.")
        return False
    
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    
    try:
        if config.SERVICE_ACCOUNT_JSON:
            # Prioritize JSON string from environment variable (Deployment)
            creds_info = json.loads(config.SERVICE_ACCOUNT_JSON)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        elif os.path.exists(config.SERVICE_ACCOUNT_FILE):
             # Fall back to local file path (Development)
            creds = ServiceAccountCredentials.from_json_keyfile_name(config.SERVICE_ACCOUNT_FILE, scope)
        else:
            print(f"Error: Neither 'SERVICE_ACCOUNT_JSON' nor file '{config.SERVICE_ACCOUNT_FILE}' found.")
            return False
        client = gspread.authorize(creds)
        sheet = client.open_by_key(config.SHEET_ID).sheet1
        
        row = [date, url, query, username, str(message_id)]
        sheet.append_row(row)
        return True
    except Exception as e:
        print(f"Google Sheets Error: {e}")
        if "403" in str(e) or "permission" in str(e).lower():
            print("Action Required: Share your Google Sheet with the Service Account email found in your JSON file.")
        return False
