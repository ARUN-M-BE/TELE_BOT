import gspread
from oauth2client.service_account import ServiceAccountCredentials
import config
import datetime

def save_to_sheets(date, url, query, message_id):
    """
    Appends a row to the designated Google Sheet.
    """
    if config.SHEET_ID == "YOUR_GOOGLE_SHEET_ID" or not config.SERVICE_ACCOUNT_FILE:
        print("Skipping Google Sheets as no ID or credentials were provided.")
        return False
    
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(config.SERVICE_ACCOUNT_FILE, scope)
    client = gspread.authorize(creds)
    
    sheet = client.open_by_key(config.SHEET_ID).sheet1
    
    row = [date, url, query, str(message_id)]
    sheet.append_row(row)
    return True
