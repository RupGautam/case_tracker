import os
import sys
import time
import requests
import re
import logging
import threading
import schedule
from bs4 import BeautifulSoup
from requests_html import HTMLSession
import warnings
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
URL = 'https://egov.uscis.gov/casestatus/mycasestatus.do'
HEADER = {'user-agent': '"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"'}
TELEGRAM_API = 'https://api.telegram.org/bot{}/{}?chat_id={}&text={}'

def check_status(case_id):
    # Use a dictionary to store the payload
    payload = {
        "changeLocale": "",
        "appReceiptNum": case_id,
        "initCaseSearch": "CHECK STATUS"
    }

    # Send a POST request and parse the response using BeautifulSoup
    response = requests.post(url=URL, headers=HEADER, data=payload, verify=False)
    soup = BeautifulSoup(response.content, "lxml")

    # Find the status text and remove unwanted characters
    status = soup.find('div', "current-status-sec").text
    status = re.sub(r'[\t\n\r]', "", status)
    return status


def send_notification(telegram_bot_api, telegram_id, case_id):
    # Check the status of the case
    status = check_status(case_id)

    # Use the format method to insert the values into the TELEGRAM_API string
    url = TELEGRAM_API.format(telegram_bot_api, 'sendMessage', telegram_id, status)

    # Send a GET request to the Telegram API in a separate thread
    thread = threading.Thread(target=requests.get, args=(url, HEADER))
    thread.start()
    
    # Set a timer to run the function every morning at 10:00 AM
    schedule.every().day.at("10:00").do(send_notification, telegram_bot_api, telegram_id, case_id)

while True:
    schedule.run_pending()

if __name__ == '__main__':
    # Check for the required environment variables
    case_id = os.getenv('USCIS_CASE_ID')
    telegram_bot_api = os.getenv('TELEGRAM_BOT_API')
    telegram_id = os.getenv('TELEGRAM_ID')
    if not case_id:
        logging.critical("No environment variable USCIS_CASE found!")
        sys.exit(1)
    if not telegram_bot_api:
        logging.critical("No environment variable TELEGRAM_API found!")
        sys.exit(1)
    if not telegram_id:
        logging.critical("No environment variable TELEGRAM_ID found!")
        sys.exit(1)

    # Log the case ID and Telegram API information
    logging.info('Monitoring USCIS case: {}'.format(case_id))
    logging.info('BOT_API: {}, CHAT: {}'.format(telegram_bot_api, telegram_id))

    # Send a notification with the case status
    send_notification(telegram_bot_api, telegram_id, case_id)
