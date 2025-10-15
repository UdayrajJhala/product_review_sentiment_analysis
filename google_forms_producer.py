import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from kafka import KafkaProducer
import json
import time
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


# -------------------
# Kafka setup
# -------------------
producer = KafkaProducer(
    bootstrap_servers=["localhost:9092"],
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)
topic_name = "reviews_raw"

# -------------------
# Google Sheets setup
# -------------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)

# Replace with your spreadsheet ID and sheet name

SHEET_NAME = "Form Responses 1"
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

# -------------------
# Track which rows were already sent
# -------------------
sent_rows = set()

while True:
    # Fetch all rows
    all_rows = sheet.get_all_records()
    for idx, row in enumerate(all_rows):
        if idx in sent_rows:
            continue  # already sent

        # Convert row to JSON
        message = {
            "product_name": row.get("Product Name", ""),
            "price": row.get("Product Price", ""),
            "review": row.get("Review", ""),
            "summary": row.get("Summary", ""),
            "rating": row.get("Overall Rating", 0),
        }

        # Send to Kafka
        producer.send(topic_name, message)
        print(f"Sent row {idx} to Kafka: {message}")
        sent_rows.add(idx)

    # Wait before polling again
    time.sleep(10)
