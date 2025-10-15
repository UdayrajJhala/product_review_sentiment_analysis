import pandas as pd
from kafka import KafkaProducer
import json
import time

# Initialize Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=["localhost:9092"],
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

# Load dataset
df = pd.read_csv("Dataset-SA.csv")

# Select useful columns (adjust to match your dataset)
df = df[["product_name", "review", "Summary", "rating"]].dropna()

# Stream each review to Kafka
for _, row in df.iterrows():
    message = {
        "product_name": row["product_name"],
        "review": row["review"],
        "Summary": row["Summary"],
        "rating": float(row["rating"]),
    }
    producer.send("flipkart-reviews", value=message)
    print(f"Sent -> {message}")
    time.sleep(1)  # simulate real-time streaming

producer.flush()
print("All reviews sent successfully.")
