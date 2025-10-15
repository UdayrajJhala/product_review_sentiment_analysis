# Product Review Sentiment Analysis Pipeline

Real-time sentiment analysis system that streams product reviews from Google Forms through Kafka, predicts sentiment using a trained Logistic Regression model, and stores results in MongoDB Atlas.

## 🏗️ Architecture

```
Google Forms → google_forms_producer.py → Kafka (reviews_raw topic)
                                              ↓
                                          consumer.py
                                    (Load LR Model + Predict)
                                              ↓
                                        MongoDB Atlas
                                    (sentiment_predictions)
```

## 📋 Components

1. **google_forms_producer.py** - Polls Google Sheets and streams new reviews to Kafka
2. **consumer.py** - Consumes from Kafka, predicts sentiment, stores in MongoDB
3. **sentiment_model_pyspark.ipynb** - Trains Logistic Regression model using PySpark
4. **saved_model/** - Contains trained model (sentiment_model.pkl) and labels

## 🚀 Quick Start

### 1. Start Kafka Infrastructure

```powershell
docker-compose up -d
```

Verify containers are running:

```powershell
docker ps
```

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` and update:

```env
SPREADSHEET_ID="your_google_sheet_id"
MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority"
```

### 4. Run the Producer (Terminal 1)

```powershell
python google_forms_producer.py
```

This streams data from Google Forms to Kafka topic `reviews_raw`.

### 5. Run the Consumer (Terminal 2)

```powershell
python consumer.py
```

This consumes from Kafka, predicts sentiment, and stores in MongoDB.

## 🧪 Testing

### Test the Model Locally

```powershell
python test_model.py
```

This verifies the sentiment prediction model works correctly before running the full pipeline.

### Monitor Kafka Messages

```powershell
docker exec -it kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic reviews_raw --from-beginning
```

### View Consumer Output

The consumer will log predictions in real-time:

```
INFO - Received: {'product_name': 'iphone 16', 'summary': 'i hate this phone', ...}
INFO - ✅ Predicted: negative (confidence: 89.23%)
INFO - 📝 Stored in MongoDB with ID: 507f1f77bcf86cd799439011
```

## 📊 Model Information

- **Algorithm**: Logistic Regression (PySpark ML)
- **Classes**: positive, negative, neutral
- **Features**: HashingTF + TF-IDF (2^16 dimensions)
- **Training**: See `sentiment_model_pyspark.ipynb`
- **Model Metrics**:
  - Stored in saved_model/sentiment_model.pkl
  - Includes accuracy and F1 score

## 🗄️ MongoDB Schema

Documents stored in `product_reviews.sentiment_predictions`:

```json
{
  "product_name": "iphone 16",
  "price": 90000,
  "review": "bad",
  "summary": "i hate this phone",
  "rating": 1,
  "predicted_sentiment": "negative",
  "confidence": 0.8923,
  "timestamp": "2025-10-15T10:30:00Z"
}
```

## 📝 Project Structure

```
├── docker-compose.yml              # Kafka + Zookeeper setup
├── google_forms_producer.py        # Streams from Google Forms → Kafka
├── consumer.py                     # Kafka → Sentiment Prediction → MongoDB
├── producer.py                     # (Alternative producer)
├── test_model.py                   # Test sentiment model locally
├── sentiment_model_pyspark.ipynb   # Model training notebook
├── requirements.txt                # Python dependencies
├── .env                            # Environment configuration
├── service_account.json            # Google Sheets credentials
├── saved_model/
│   ├── sentiment_model.pkl         # Trained LR model
│   └── labels.txt                  # Class labels
└── CONSUMER_SETUP.md               # Detailed consumer setup guide
```

## 🔧 Troubleshooting

See [CONSUMER_SETUP.md](CONSUMER_SETUP.md) for detailed setup instructions and troubleshooting.

### Common Issues

1. **Kafka not available**: Ensure docker-compose is running
2. **MongoDB connection errors**: Check MONGODB_URI and network access in Atlas
3. **Import errors**: Run `pip install -r requirements.txt`
4. **Model predictions incorrect**: Run `python test_model.py` to verify

## 📚 Additional Documentation

- **Consumer Setup**: See [CONSUMER_SETUP.md](CONSUMER_SETUP.md)
- **Model Training**: Open `sentiment_model_pyspark.ipynb` in Jupyter/VS Code

## 🛠️ Development

### Retrain the Model

1. Update `Dataset-SA.csv` with new training data
2. Open `sentiment_model_pyspark.ipynb`
3. Run all cells to retrain and save the model
4. Restart `consumer.py` to use the new model

### Monitor Kafka Topics

List all topics:

```powershell
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --list
```

Delete a topic:

```powershell
docker exec -it kafka kafka-topics --bootstrap-server localhost:9092 --delete --topic reviews_raw
```

## 📄 License

[Add your license here]
