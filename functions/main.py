"""
Firebase Cloud Functions for Stock Chart App
Handles daily stock data collection from the Korea Investment & Securities (KIS) API.
"""

import functions_framework
import requests
import json
import os
import logging
import time
from datetime import datetime
from typing import List
from firebase_admin import initialize_app, firestore

# Initialize Firebase Admin SDK
# This is done automatically when deployed to Cloud Functions.
# For local testing, you need to have the GOOGLE_APPLICATION_CREDENTIALS env var set.
try:
    initialize_app()
except ValueError:
    # If it's already initialized, do nothing.
    pass

db = firestore.client()
logger = logging.getLogger(__name__)


def get_target_stock_codes() -> List[str]:
    """Resolve target stock codes from env or Firestore."""
    env_value = os.environ.get("TARGET_STOCK_CODES") or os.environ.get("STOCK_CODES")
    if env_value:
        codes = [code.strip() for code in env_value.split(",") if code.strip()]
        if codes:
            logger.info("Loaded %d stock codes from environment.", len(codes))
            return codes

    try:
        config_doc = db.collection('metadata').document('config').get()
        if config_doc.exists:
            data = config_doc.to_dict() or {}
            raw_codes = data.get('stockCodes') or data.get('targetStockCodes') or data.get('stocks')
            if isinstance(raw_codes, list):
                codes = [str(code).strip() for code in raw_codes if str(code).strip()]
            elif isinstance(raw_codes, str):
                codes = [code.strip() for code in raw_codes.split(',') if code.strip()]
            else:
                codes = []

            if codes:
                logger.info("Loaded %d stock codes from Firestore metadata/config.", len(codes))
                return codes
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Failed to load stock codes from Firestore: %s", exc)

    logger.error("No stock codes configured. Set TARGET_STOCK_CODES env var or metadata/config.stockCodes.")
    return []

# --- KIS API Client ---

class KISClient:
    """
    A client for interacting with the Korea Investment & Securities (KIS) API.
    """
    def __init__(self, is_prod=True):
        self.app_key = os.environ.get("KIS_APP_KEY")
        self.app_secret = os.environ.get("KIS_APP_SECRET")
        if not self.app_key or not self.app_secret:
            raise ValueError("KIS_APP_KEY and KIS_APP_SECRET environment variables must be set.")

        self.base_url = "https://openapi.koreainvestment.com:9443" if is_prod else "https://openapivts.koreainvestment.com:29443"
        self.access_token = None
        self._get_access_token()

    def _request_with_retry(self, method, url, *, retries=3, backoff=2, timeout=10, **kwargs):
        """Issue an HTTP request with basic retry/backoff."""
        for attempt in range(1, retries + 1):
            try:
                response = requests.request(method, url, timeout=timeout, **kwargs)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as exc:
                if attempt == retries:
                    raise
                logger.warning(
                    "KIS %s request failed (attempt %d/%d): %s",
                    method.upper(),
                    attempt,
                    retries,
                    exc,
                )
                time.sleep(backoff ** (attempt - 1))

    def _get_access_token(self):
        """Fetches and sets the access token."""
        url = f"{self.base_url}/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        try:
            response = self._request_with_retry(
                "post",
                url,
                headers=headers,
                data=json.dumps(body),
            )
            res_data = response.json()
            self.access_token = res_data.get("access_token")
            if not self.access_token:
                raise ValueError("Access token not found in API response.")
            logger.info("Successfully fetched KIS API access token.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get access token: {e}")
            raise

    def get_daily_price(self, stock_code):
        """
        Fetches the latest daily price data for a given stock code.
        Returns the data for the most recent trading day.
        """
        if not self.access_token:
            raise ValueError("Access token is not available.")

        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-price"
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "FHKST01010400", # Transaction ID for daily price inquiry
            "custtype": "P"
        }
        params = {
            "FID_COND_MRKT_DIV_CODE": "J", # J: 주식
            "FID_INPUT_ISCD": stock_code,
            "FID_PERIOD_DIV_CODE": "D", # D: 일별
            "FID_ORG_ADJ_PRC": "1" # 1: 수정주가
        }

        try:
            response = self._request_with_retry(
                "get",
                url,
                headers=headers,
                params=params,
            )
            res_data = response.json()

            if res_data.get("rt_cd") != "0":
                error_msg = res_data.get('msg1', 'Unknown API error')
                logger.error(f"KIS API error for {stock_code}: {error_msg}")
                return None

            # output is a list of recent daily data, we need the first (most recent)
            output = res_data.get("output")
            if not output:
                logger.warning(f"No daily price data found for {stock_code}.")
                return None

            latest_data = output[0]
            return {
                "date": latest_data.get("stck_bsop_date"), # 영업 일자
                "open": int(latest_data.get("stck_oprc", 0)), # 시가
                "high": int(latest_data.get("stck_hgpr", 0)), # 고가
                "low": int(latest_data.get("stck_lwpr", 0)), # 저가
                "close": int(latest_data.get("stck_clpr", 0)), # 종가
                "volume": int(latest_data.get("acml_vol", 0)) # 거래량
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get daily price for {stock_code}: {e}")
            return None

# --- Cloud Function ---

@functions_framework.http
def fetch_stock_data(request):
    """
    HTTP Cloud Function to fetch and store daily stock data.
    Triggered by Cloud Scheduler.
    """
    logger.info("Cloud Function triggered to fetch stock data.")

    try:
        client = KISClient(is_prod=True)
    except (ValueError, requests.exceptions.RequestException) as e:
        logger.error(f"Failed to initialize KISClient: {e}")
        return {"status": "error", "message": "Failed to initialize KISClient"}, 500

    stock_codes = get_target_stock_codes()
    if not stock_codes:
        return {
            "status": "error",
            "message": "No stock codes configured for scheduler execution."
        }, 500

    success_count = 0
    error_count = 0

    for code in stock_codes:
        logger.info(f"Processing stock: {code}")
        daily_data = client.get_daily_price(code)

        if not daily_data or not daily_data.get("date"):
            logger.error(f"Could not retrieve valid data for {code}.")
            error_count += 1
            continue

        try:
            date_str = daily_data["date"] # YYYYMMDD
            year = date_str[:4]
            month = date_str[4:6]
            day = date_str[6:8]
            year_month_doc_id = f"{year}-{month}"

            # Prepare data for Firestore, removing the date field
            firestore_data = {key: val for key, val in daily_data.items() if key != "date"}

            # Get the monthly document reference
            doc_ref = db.collection('stocks').document(code).collection('monthly').document(year_month_doc_id)

            # Update the 'days' map with the new day's data using dot notation.
            # This will create or update the field for the specific day.
            doc_ref.set({
                'days': {
                    day: firestore_data
                }
            }, merge=True)

            logger.info(f"Successfully updated Firestore for {code} on {date_str}.")
            success_count += 1

        except Exception as e:
            logger.error(f"Failed to update Firestore for {code}: {e}")
            error_count += 1

    # Update metadata
    try:
        meta_ref = db.collection('metadata').document('system')
        metadata_payload = {
            'lastAttemptedUpdate': firestore.SERVER_TIMESTAMP,
            'updateStatus': 'success' if error_count == 0 else 'partial_failure',
            'lastRunStats': {
                'success_count': success_count,
                'error_count': error_count,
                'total_stocks': len(stock_codes)
            }
        }
        if error_count == 0 and success_count > 0:
            metadata_payload['lastSuccessfulUpdate'] = firestore.SERVER_TIMESTAMP

        meta_ref.set(metadata_payload, merge=True)
        logger.info("Successfully updated metadata.")
    except Exception as e:
        logger.error(f"Failed to update metadata: {e}")


    summary = f"Stock data fetch completed. Success: {success_count}, Failed: {error_count}"
    logger.info(summary)

    return {
        "status": "success",
        "message": summary
    }, 200

@functions_framework.http
def health_check(request):
    """Simple health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}, 200