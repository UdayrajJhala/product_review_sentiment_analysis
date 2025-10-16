import os
from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
from dotenv import load_dotenv
from collections import Counter
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)

# MongoDB Atlas setup
MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError("MONGODB_URI environment variable not set!")

mongo_client = MongoClient(MONGODB_URI)
db = mongo_client["product_reviews"]
collection = db["sentiment_predictions"]

logger.info("Connected to MongoDB Atlas")


@app.route("/")
def index():
    """Render the main dashboard"""
    return render_template("index.html")


@app.route("/api/products")
def get_products():
    """Get list of all unique products"""
    try:
        products = collection.distinct("product_name")
        products = [p for p in products if p]  # Filter out empty strings
        return jsonify({"products": sorted(products)})
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/reviews")
def get_reviews():
    """Get all reviews or reviews for a specific product"""
    try:
        product_name = request.args.get("product")

        # Build query
        query = {}
        if product_name:
            query["product_name"] = product_name

        # Fetch reviews
        reviews = list(collection.find(query).sort("timestamp", -1).limit(100))

        # Convert ObjectId to string for JSON serialization
        for review in reviews:
            review["_id"] = str(review["_id"])
            review["timestamp"] = (
                review["timestamp"].isoformat() if "timestamp" in review else None
            )

        # Calculate statistics
        sentiments = [
            r["predicted_sentiment"] for r in reviews if "predicted_sentiment" in r
        ]
        sentiment_counts = Counter(sentiments)

        total = len(sentiments)
        positive_count = sentiment_counts.get("positive", 0)
        negative_count = sentiment_counts.get("negative", 0)
        neutral_count = sentiment_counts.get("neutral", 0)

        # Determine product success/failure
        # Success if positive reviews > negative reviews
        status = (
            "success"
            if positive_count > negative_count
            else "failure" if negative_count > positive_count else "neutral"
        )

        stats = {
            "total_reviews": total,
            "positive": positive_count,
            "negative": negative_count,
            "neutral": neutral_count,
            "status": status,
            "positive_percentage": (positive_count / total * 100) if total > 0 else 0,
            "negative_percentage": (negative_count / total * 100) if total > 0 else 0,
            "neutral_percentage": (neutral_count / total * 100) if total > 0 else 0,
        }

        return jsonify({"reviews": reviews, "statistics": stats})

    except Exception as e:
        logger.error(f"Error fetching reviews: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/stats")
def get_overall_stats():
    """Get overall statistics across all products"""
    try:
        # Get all reviews
        all_reviews = list(collection.find())

        # Overall sentiment distribution
        sentiments = [
            r["predicted_sentiment"] for r in all_reviews if "predicted_sentiment" in r
        ]
        sentiment_counts = Counter(sentiments)

        # Per-product stats
        products = collection.distinct("product_name")
        product_stats = []

        for product in products:
            if not product:
                continue

            product_reviews = [
                r for r in all_reviews if r.get("product_name") == product
            ]
            product_sentiments = [
                r["predicted_sentiment"]
                for r in product_reviews
                if "predicted_sentiment" in r
            ]
            product_sentiment_counts = Counter(product_sentiments)

            positive = product_sentiment_counts.get("positive", 0)
            negative = product_sentiment_counts.get("negative", 0)

            status = (
                "success"
                if positive > negative
                else "failure" if negative > positive else "neutral"
            )

            product_stats.append(
                {
                    "product_name": product,
                    "total_reviews": len(product_sentiments),
                    "positive": positive,
                    "negative": negative,
                    "neutral": product_sentiment_counts.get("neutral", 0),
                    "status": status,
                }
            )

        return jsonify(
            {
                "total_reviews": len(sentiments),
                "overall_sentiments": dict(sentiment_counts),
                "product_stats": sorted(
                    product_stats, key=lambda x: x["total_reviews"], reverse=True
                ),
            }
        )

    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
