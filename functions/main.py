"""
Firebase Cloud Functions for Stock Chart App
Handles daily stock data collection from Korean Investment API
"""

import functions_framework
from firebase_admin import initialize_app, firestore
from datetime import datetime
import logging

# Initialize Firebase Admin SDK
initialize_app()
db = firestore.client()

logger = logging.getLogger(__name__)


@functions_framework.http
def fetch_stock_data(request):
    """
    HTTP Cloud Function to fetch stock data from Korean Investment API
    Triggered by Cloud Scheduler daily at 15:40 KST
    """
    try:
        logger.info("Starting stock data fetch...")

        # TODO: Implement Korean Investment API integration
        # 1. Get access token
        # 2. Fetch stock list from Firestore
        # 3. For each stock, fetch latest data
        # 4. Update Firestore (recent array + monthly collection)

        return {
            "status": "success",
            "message": "Stock data fetch completed",
            "timestamp": datetime.now().isoformat()
        }, 200

    except Exception as e:
        logger.error(f"Error fetching stock data: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }, 500


@functions_framework.http
def health_check(request):
    """Simple health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}, 200
