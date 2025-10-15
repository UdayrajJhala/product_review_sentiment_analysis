# Sentiment Analysis Consumer Setup

This document explains how to set up and run the Kafka consumer that predicts sentiment and stores results in MongoDB Atlas.

## Prerequisites

1. **Kafka** running (via docker-compose)
2. **MongoDB Atlas** account and cluster
3. **Python 3.8+** with required packages

## Setup Instructions

### 1. Install Required Python Packages

```powershell
pip install -r requirements.txt
```

### 2. Configure MongoDB Atlas

1. Go to [MongoDB Atlas](https://cloud.mongodb.com/)
2. Create a free cluster if you haven't already
3. Click "Connect" on your cluster
4. Choose "Connect your application"
5. Copy the connection string (looks like `mongodb+srv://...`)
6. Replace `<password>` with your database user password

### 3. Update Environment Variables

Edit your `.env` file and add the MongoDB connection string:

```env
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
```

**Important**: Replace:

- `username` with your MongoDB Atlas username
- `password` with your MongoDB Atlas password
- `cluster` with your cluster name

### 4. Verify Kafka is Running

```powershell
docker ps
```

You should see `kafka` and `zookeeper` containers running.

### 5. Run the Consumer

```powershell
python consumer.py
```

## How It Works

The consumer:

1. **Connects to Kafka** topic `reviews_raw`
2. **Receives streaming data** from Google Forms (via `google_forms_producer.py`)
3. **Loads the trained Logistic Regression model** from `saved_model/sentiment_model.pkl`
4. **Preprocesses** the summary text:
   - Lowercases text
   - Tokenizes (splits into words)
   - Removes stopwords
   - Applies HashingVectorizer + TF-IDF (same as training)
5. **Predicts sentiment** using the saved model coefficients
6. **Stores result in MongoDB** with the following structure:

```json
{
  "product_name": "iphone 16",
  "price": 90000,
  "review": "bad",
  "summary": "i hate this phone",
  "rating": 1,
  "predicted_sentiment": "negative",
  "confidence": 0.89,
  "timestamp": "2025-10-15T10:30:00Z"
}
```

## Testing

1. Start the producer (in another terminal):

```powershell
python google_forms_producer.py
```

2. Submit a review via Google Forms

3. Check consumer logs for predictions:

```
2025-10-15 10:30:00 - INFO - Received: {'product_name': 'iphone 16', ...}
2025-10-15 10:30:00 - INFO - ✅ Predicted: negative (confidence: 89.23%)
2025-10-15 10:30:00 - INFO - 📝 Stored in MongoDB with ID: 507f1f77bcf86cd799439011
```

4. Verify in MongoDB Atlas:
   - Go to your cluster → Browse Collections
   - Database: `product_reviews`
   - Collection: `sentiment_predictions`

## Monitoring Kafka Messages

To see raw messages in Kafka:

```powershell
docker exec -it kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic reviews_raw --from-beginning
```

## Troubleshooting

### "MONGODB_URI environment variable not set"

- Make sure `.env` file exists in the project root
- Check that MONGODB_URI is set correctly

### "Import ... could not be resolved"

- Run: `pip install -r requirements.txt`

### Connection errors to MongoDB

- Check your MongoDB Atlas network access (allow your IP)
- Verify username/password in connection string
- Ensure your cluster is running

### Model predictions seem incorrect

- The model uses hash-based TF-IDF which may differ slightly from PySpark's HashingTF
- For better accuracy, consider saving the actual vectorizer during training

## Architecture

```
Google Forms → google_forms_producer.py → Kafka (reviews_raw topic)
                                              ↓
                                          consumer.py
                                              ↓
                                    ┌─────────┴─────────┐
                            Load Model (LR)    Predict Sentiment
                                              ↓
                                        MongoDB Atlas
                                    (sentiment_predictions)
```

## Model Information

- **Algorithm**: Logistic Regression (trained with PySpark)
- **Classes**: positive, negative, neutral
- **Features**: TF-IDF vectors (2^16 dimensions)
- **Model file**: `saved_model/sentiment_model.pkl`

The model was trained in `sentiment_model_pyspark.ipynb` using PySpark ML.
