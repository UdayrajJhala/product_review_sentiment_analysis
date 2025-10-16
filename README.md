# Product Review Sentiment Analysis

A real-time end-to-end sentiment analysis system that streams product reviews from Google Forms through Kafka, predicts sentiment using a trained Logistic Regression model, stores results in MongoDB Atlas, and visualizes insights through a web dashboard.

## 🎯 Features

- **Real-time Data Pipeline**: Stream reviews from Google Forms → Kafka → ML Prediction → MongoDB
- **Sentiment Analysis**: Logistic Regression model trained with PySpark ML
- **Interactive Dashboard**: Web-based visualization with Flask + real-time statistics
- **Product Success Metrics**: Automatic product status based on sentiment distribution
- **RESTful API**: Query reviews and statistics programmatically
- **Auto-refresh**: Dashboard updates every 30 seconds
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## 🏗️ Architecture

```
Google Forms → Google Sheets API
                     ↓
          google_forms_producer.py
                     ↓
        Kafka Topic (reviews_raw)
                     ↓
              consumer.py
            (ML Prediction)
                     ↓
          MongoDB Atlas
     (sentiment_predictions)
                     ↓
              app.py (Flask)
                     ↓
          Web Dashboard (index.html)
```

## 📋 Prerequisites

- **Python 3.8+**
- **Docker Desktop** (for Kafka & Zookeeper)
- **MongoDB Atlas** account (free tier available)
- **Google Cloud Project** with Sheets API enabled
- **Service Account JSON** for Google Sheets access

## 🚀 Quick Start

### 1. Start Kafka Infrastructure

```powershell
docker-compose up -d
```

Verify containers are running:

```powershell
docker ps
```

You should see `kafka` and `zookeeper` containers.

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3. Configure Environment

Create a `.env` file in the project root:

```env
SPREADSHEET_ID="your_google_sheet_id"
MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority"
```

**MongoDB Atlas Setup:**

1. Go to [MongoDB Atlas](https://cloud.mongodb.com/)
2. Create a free cluster
3. Click "Connect" → "Connect your application"
4. Copy connection string and replace `<password>` with your password
5. Add your IP to Network Access whitelist

**Google Sheets Setup:**

1. Create a Google Cloud Project
2. Enable Google Sheets API
3. Create a Service Account and download JSON key
4. Save as `service_account.json` in project root
5. Share your Google Sheet with the service account email

### 4. Run the Pipeline

**Terminal 1 - Start Producer:**

```powershell
python google_forms_producer.py
```

**Terminal 2 - Start Consumer:**

```powershell
python consumer.py
```

**Terminal 3 - Start Dashboard:**

```powershell
python app.py
```

### 5. Access the Dashboard

Open your browser and navigate to:

```
http://localhost:5000
```

## 📊 How It Works

### Data Flow

1. **Data Collection**: User submits review via Google Form → stored in Google Sheets
2. **Producer**: `google_forms_producer.py` polls Google Sheets every 10 seconds and streams new reviews to Kafka topic `reviews_raw`
3. **Consumer**: `consumer.py` consumes from Kafka, preprocesses text, and predicts sentiment using the trained model
4. **Storage**: Predictions are stored in MongoDB with confidence scores and timestamps
5. **Dashboard**: Flask app queries MongoDB and serves data via REST API to the web interface

### Sentiment Prediction Pipeline

The consumer performs these steps:

1. **Text Preprocessing**:

   - Lowercase conversion
   - Tokenization
   - Stopword removal

2. **Feature Extraction**:

   - HashingVectorizer (2^16 dimensions)
   - TF-IDF transformation

3. **Prediction**:
   - Logistic Regression model
   - Classes: positive, negative, neutral
   - Confidence score calculation

### Product Success Logic

The dashboard determines product status:

- ✅ **Success**: `positive_reviews > negative_reviews`
- ❌ **Failure**: `negative_reviews > positive_reviews`
- ➖ **Neutral**: `positive_reviews == negative_reviews`

## 🗄️ Data Schema

### MongoDB Document Structure

Collection: `product_reviews.sentiment_predictions`

```json
{
  "product_name": "iPhone 16",
  "price": 90000,
  "review": "bad",
  "summary": "i hate this phone",
  "rating": 1,
  "predicted_sentiment": "negative",
  "confidence": 0.8923,
  "timestamp": "2025-10-15T10:30:00Z"
}
```

## 🔌 API Endpoints

### GET `/api/products`

Returns list of all unique product names.

**Response:**

```json
{
  "products": ["iPhone 16", "Samsung Galaxy", ...]
}
```

### GET `/api/reviews?product=<product_name>`

Returns reviews and statistics for a specific product (or all if no product specified).

**Parameters:**

- `product` (optional): Product name to filter by

**Response:**

```json
{
  "reviews": [...],
  "statistics": {
    "total_reviews": 100,
    "positive": 60,
    "negative": 30,
    "neutral": 10,
    "status": "success",
    "positive_percentage": 60.0,
    "negative_percentage": 30.0,
    "neutral_percentage": 10.0
  }
}
```

### GET `/api/stats`

Returns overall statistics across all products.

**Response:**

```json
{
  "total_reviews": 500,
  "overall_sentiments": {
    "positive": 300,
    "negative": 150,
    "neutral": 50
  },
  "product_stats": [...]
}
```

## 🎨 Dashboard Features

### Statistics Cards

- Total reviews count
- Sentiment distribution (positive, negative, neutral)
- Percentage breakdowns
- Product success/failure indicator

### Review Cards

Each card displays:

- Product name and price
- Sentiment badge (color-coded: 🟢 positive, 🔴 negative, 🟡 neutral)
- Star rating (⭐)
- Review summary and full text
- Confidence score with visual bar
- Timestamp

### Filtering

- Dropdown to filter by product
- View all products or specific product reviews
- Auto-refresh maintains filter selection

## 🧪 Testing

### Test the Model Locally

```powershell
python test_model.py
```

### Monitor Kafka Messages

```powershell
docker exec -it kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic reviews_raw --from-beginning
```

### View Consumer Logs

The consumer logs predictions in real-time:

```
INFO - Received: {'product_name': 'iPhone 16', 'summary': 'i hate this phone', ...}
INFO - ✅ Predicted: negative (confidence: 89.23%)
INFO - 📝 Stored in MongoDB with ID: 507f1f77bcf86cd799439011
```

### Verify MongoDB Data

1. Go to MongoDB Atlas → Browse Collections
2. Navigate to `product_reviews` → `sentiment_predictions`
3. Verify documents are being inserted

## 📊 Model Information

- **Algorithm**: Logistic Regression (PySpark ML)
- **Classes**: positive, negative, neutral
- **Features**: HashingTF + TF-IDF (2^16 dimensions)
- **Training**: See `sentiment_model_pyspark.ipynb`
- **Model File**: `saved_model/sentiment_model.pkl`

## 📝 Project Structure

```
├── app.py                          # Flask web server & API
├── templates/
│   └── index.html                  # Dashboard frontend
├── google_forms_producer.py        # Google Sheets → Kafka producer
├── consumer.py                     # Kafka → ML Prediction → MongoDB
├── producer.py                     # Alternative Kafka producer
├── sentiment_model_pyspark.ipynb   # Model training notebook
├── Dataset-SA.csv                  # Training dataset
├── docker-compose.yml              # Kafka + Zookeeper setup
├── requirements.txt                # Python dependencies
├── .env                            # Environment configuration
├── service_account.json            # Google Sheets credentials
└── saved_model/
    ├── sentiment_model.pkl         # Trained model
    └── labels.txt                  # Class labels
```
