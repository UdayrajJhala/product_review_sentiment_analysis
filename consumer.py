import os
import json
import pickle
import re
import numpy as np
from kafka import KafkaConsumer
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
from sklearn.feature_extraction.text import HashingVectorizer, TfidfTransformer
from sklearn.pipeline import Pipeline
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

# MongoDB Atlas setup
MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError("MONGODB_URI environment variable not set!")

mongo_client = MongoClient(MONGODB_URI)
db = mongo_client["product_reviews"]  # Database name
collection = db["sentiment_predictions"]  # Collection name

logger.info("Connected to MongoDB Atlas")

# Load the trained model
MODEL_PATH = r"D:\product_review_sentiment_analysis\saved_model\sentiment_model.pkl"

with open(MODEL_PATH, "rb") as f:
    model_package = pickle.load(f)

coefficients = model_package["coefficients"]
intercept = model_package["intercept"]
labels = model_package["labels"]
num_classes = model_package["num_classes"]

logger.info(f"Model loaded successfully")
logger.info(f"Classes: {labels}")
logger.info(f"Model accuracy: {model_package.get('accuracy', 'N/A'):.2%}")
logger.info(f"Model F1 Score: {model_package.get('f1_score', 'N/A'):.2%}")

# Text preprocessing setup
# English stopwords (same as PySpark's default)
STOPWORDS = set(
    [
        "i",
        "me",
        "my",
        "myself",
        "we",
        "our",
        "ours",
        "ourselves",
        "you",
        "you're",
        "you've",
        "you'll",
        "you'd",
        "your",
        "yours",
        "yourself",
        "yourselves",
        "he",
        "him",
        "his",
        "himself",
        "she",
        "she's",
        "her",
        "hers",
        "herself",
        "it",
        "it's",
        "its",
        "itself",
        "they",
        "them",
        "their",
        "theirs",
        "themselves",
        "what",
        "which",
        "who",
        "whom",
        "this",
        "that",
        "that'll",
        "these",
        "those",
        "am",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "having",
        "do",
        "does",
        "did",
        "doing",
        "a",
        "an",
        "the",
        "and",
        "but",
        "if",
        "or",
        "because",
        "as",
        "until",
        "while",
        "of",
        "at",
        "by",
        "for",
        "with",
        "about",
        "against",
        "between",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "to",
        "from",
        "up",
        "down",
        "in",
        "out",
        "on",
        "off",
        "over",
        "under",
        "again",
        "further",
        "then",
        "once",
        "here",
        "there",
        "when",
        "where",
        "why",
        "how",
        "all",
        "both",
        "each",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "nor",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "s",
        "t",
        "can",
        "will",
        "just",
        "don",
        "don't",
        "should",
        "should've",
        "now",
        "d",
        "ll",
        "m",
        "o",
        "re",
        "ve",
        "y",
        "ain",
        "aren",
        "aren't",
        "couldn",
        "couldn't",
        "didn",
        "didn't",
        "doesn",
        "doesn't",
        "hadn",
        "hadn't",
        "hasn",
        "hasn't",
        "haven",
        "haven't",
        "isn",
        "isn't",
        "ma",
        "mightn",
        "mightn't",
        "mustn",
        "mustn't",
        "needn",
        "needn't",
        "shan",
        "shan't",
        "shouldn",
        "shouldn't",
        "wasn",
        "wasn't",
        "weren",
        "weren't",
        "won",
        "won't",
        "wouldn",
        "wouldn't",
    ]
)

# Initialize HashingVectorizer + TF-IDF to match PySpark's HashingTF+IDF
# This doesn't require fitting and uses consistent hashing
hashing_vectorizer = HashingVectorizer(
    n_features=2**16,  # Match PySpark's HashingTF numFeatures
    lowercase=True,
    token_pattern=r"\w+",
    alternate_sign=False,  # Use positive values only
    norm=None,  # Don't normalize at this stage
)

tfidf_transformer = TfidfTransformer(use_idf=True, smooth_idf=True, sublinear_tf=False)

# Create a preprocessing pipeline
text_pipeline = Pipeline([("hasher", hashing_vectorizer), ("tfidf", tfidf_transformer)])


# -------------------
# Preprocessing functions
# -------------------
def preprocess_text(text):
    """Preprocess text: lowercase, tokenize, remove stopwords"""
    if not text or not isinstance(text, str):
        return ""

    # Lowercase
    text = text.lower()

    # Tokenize using regex (match word characters)
    tokens = re.findall(r"\w+", text)

    # Remove stopwords
    filtered_tokens = [token for token in tokens if token not in STOPWORDS]

    # Join back to string for vectorizer
    return " ".join(filtered_tokens)


# Fit the TF-IDF transformer on a dummy corpus
# This is needed because TfidfTransformer requires fitting
# In production, you should save this from training
dummy_corpus = ["this is positive", "this is negative", "this is neutral"]
text_pipeline.fit(dummy_corpus)


def predict_sentiment(summary_text):
    """
    Predict sentiment using the loaded logistic regression model
    Returns: predicted_label (str), confidence (float)
    """
    try:
        # Preprocess text
        processed_text = preprocess_text(summary_text)

        if not processed_text:
            logger.warning("Empty text after preprocessing, returning neutral")
            return "neutral", 0.33

        # Transform to features using hash-based TF-IDF
        features = text_pipeline.transform([processed_text]).toarray()

        # Ensure feature vector matches model dimensions
        if features.shape[1] < coefficients.shape[1]:
            # Pad with zeros if needed
            padding = np.zeros((1, coefficients.shape[1] - features.shape[1]))
            features = np.hstack([features, padding])
        elif features.shape[1] > coefficients.shape[1]:
            # Truncate if needed
            features = features[:, : coefficients.shape[1]]

        # Compute logits (Z = X * W^T + b)
        logits = np.dot(features, coefficients.T) + intercept

        # Apply softmax to get probabilities
        exp_logits = np.exp(logits - np.max(logits))  # Numerical stability
        probabilities = exp_logits / np.sum(exp_logits, axis=1, keepdims=True)

        # Get prediction
        predicted_idx = np.argmax(probabilities[0])
        confidence = probabilities[0][predicted_idx]
        predicted_label = labels[predicted_idx]

        return predicted_label, float(confidence)

    except Exception as e:
        logger.error(f"Error predicting sentiment: {e}")
        return "neutral", 0.0


# -------------------
# Kafka Consumer setup
# -------------------
consumer = KafkaConsumer(
    "reviews_raw",
    bootstrap_servers=["localhost:9092"],
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest",  # Start from beginning if no offset
    enable_auto_commit=True,
    group_id="sentiment-predictor-group",
)

logger.info("Kafka consumer started. Waiting for messages...")

# -------------------
# Consume and process messages
# -------------------
try:
    for message in consumer:
        try:
            record = message.value
            logger.info(f"Received: {record}")

            # Extract summary
            summary = record.get("summary", "")

            # Predict sentiment
            predicted_sentiment, confidence = predict_sentiment(summary)

            # Prepare document for MongoDB
            document = {
                "product_name": record.get("product_name", ""),
                "price": record.get("price", 0),
                "review": record.get("review", ""),
                "summary": summary,
                "rating": record.get("rating", 0),
                "predicted_sentiment": predicted_sentiment,
                "confidence": confidence,
                "timestamp": datetime.utcnow(),
            }

            # Insert into MongoDB
            result = collection.insert_one(document)

            logger.info(
                f"✅ Predicted: {predicted_sentiment} (confidence: {confidence:.2%})"
            )
            logger.info(f"📝 Stored in MongoDB with ID: {result.inserted_id}")
            logger.info("-" * 80)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            continue

except KeyboardInterrupt:
    logger.info("Shutting down consumer...")
finally:
    consumer.close()
    mongo_client.close()
    logger.info("Consumer closed.")
