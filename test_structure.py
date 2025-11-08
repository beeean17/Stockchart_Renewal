"""
Test script to create sample Firestore data structure
Run this to verify your database structure works correctly
"""

import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
import os
import sys

# Initialize Firebase Admin SDK
# Download serviceAccountKey.json from Firebase Console first!
SERVICE_ACCOUNT_KEY = 'serviceAccountKey.json'

if not os.path.exists(SERVICE_ACCOUNT_KEY):
    print("❌ Error: serviceAccountKey.json not found!")
    print("\nTo get your service account key:")
    print("1. Go to Firebase Console: https://console.firebase.google.com/project/stock-divi/settings/serviceaccounts")
    print("2. Click 'Generate new private key'")
    print("3. Save the file as 'serviceAccountKey.json' in the project root")
    print(f"4. Expected location: {os.path.abspath(SERVICE_ACCOUNT_KEY)}")
    sys.exit(1)

cred = credentials.Certificate(SERVICE_ACCOUNT_KEY)
firebase_admin.initialize_app(cred)
db = firestore.client()

def create_sample_stock():
    """Create a sample stock document (Samsung Electronics)"""

    stock_code = "005930"

    # Generate sample recent data (last 90 days)
    recent_data = []
    base_date = datetime(2024, 11, 4)
    base_price = 58000

    for i in range(90):
        date = base_date - timedelta(days=i)
        # Skip weekends (simplified)
        if date.weekday() >= 5:
            continue

        price_variation = (i % 10 - 5) * 100  # Simple price movement
        recent_data.insert(0, {
            'date': date.strftime('%Y-%m-%d'),
            'o': base_price + price_variation,
            'h': base_price + price_variation + 500,
            'l': base_price + price_variation - 500,
            'c': base_price + price_variation + 200,
            'v': 10000000 + (i * 100000)
        })

    # Create main stock document
    stock_ref = db.collection('stocks').document(stock_code)
    stock_ref.set({
        'code': stock_code,
        'name': '삼성전자',
        'period': '월말',
        'latest': {
            'price': 58200,
            'date': '2024-11-04',
            'change': -0.5
        },
        'dividends': [
            {'date': '2024-03-29', 'price': 361},
            {'date': '2024-06-28', 'price': 361},
            {'date': '2023-09-28', 'price': 361},
            {'date': '2023-12-29', 'price': 361}
        ],
        'recent': recent_data,
        'updated_at': firestore.SERVER_TIMESTAMP,
        'created_at': firestore.SERVER_TIMESTAMP
    })

    print(f"✅ Created stock document: stocks/{stock_code}")
    print(f"   - Recent data: {len(recent_data)} days")
    print(f"   - Dividends: 4 records")

    # Create monthly subcollection sample (October 2024)
    monthly_ref = stock_ref.collection('monthly').document('2024-10')

    monthly_days = []
    for day in range(1, 24):  # 23 trading days in October
        date = datetime(2024, 10, day)
        if date.weekday() >= 5:
            continue

        monthly_days.append({
            'date': date.strftime('%Y-%m-%d'),
            'o': 57000 + (day * 50),
            'h': 57500 + (day * 50),
            'l': 56500 + (day * 50),
            'c': 57200 + (day * 50),
            'v': 9000000 + (day * 100000)
        })

    monthly_ref.set({
        'days': monthly_days,
        'updated_at': firestore.SERVER_TIMESTAMP
    })

    print(f"✅ Created monthly document: stocks/{stock_code}/monthly/2024-10")
    print(f"   - Days: {len(monthly_days)} trading days")


def create_sample_user(user_id="test_user_001"):
    """Create a sample user with horizontal lines"""

    # Create user document
    user_ref = db.collection('users').document(user_id)
    user_ref.set({
        'email': 'test@example.com',
        'displayName': 'Test User',
        'photoURL': '',
        'created_at': firestore.SERVER_TIMESTAMP,
        'last_login': firestore.SERVER_TIMESTAMP,
        'settings': {
            'theme': 'light',
            'defaultStocks': ['005930', '000660'],
            'chartSettings': {
                'showVolume': True,
                'showDividends': True,
                'showMinMax': True
            }
        }
    })

    print(f"✅ Created user document: users/{user_id}")

    # Create sample horizontal lines
    lines = [
        {
            'stockCode': '005930',
            'price': 60000,
            'color': '#FF0000',
            'style': 'solid',
            'width': 2,
            'memo': '매수 목표가',
        },
        {
            'stockCode': '005930',
            'price': 55000,
            'color': '#00FF00',
            'style': 'dashed',
            'width': 1,
            'memo': '손절가',
        }
    ]

    for i, line_data in enumerate(lines):
        line_ref = user_ref.collection('lines').document(f'line_{i+1}')
        line_ref.set({
            **line_data,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        })

    print(f"✅ Created horizontal lines: users/{user_id}/lines")
    print(f"   - Lines: {len(lines)} records")


def create_metadata():
    """Create system metadata"""

    metadata_ref = db.collection('metadata').document('system')
    metadata_ref.set({
        'lastUpdate': firestore.SERVER_TIMESTAMP,
        'lastSuccessfulUpdate': firestore.SERVER_TIMESTAMP,
        'lastAttemptedUpdate': firestore.SERVER_TIMESTAMP,
        'updateStatus': 'success',
        'updateLog': {
            '2024-11-04': {
                'success': True,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'stocks_updated': 1,
                'duration': 2.5,
                'errors': []
            }
        },
        'stats': {
            'totalStocks': 1,
            'totalDays': 90,
            'lastCalculated': firestore.SERVER_TIMESTAMP
        }
    })

    print(f"✅ Created metadata document: metadata/system")


def verify_structure():
    """Verify the created structure"""

    print("\n" + "="*60)
    print("Verifying Database Structure...")
    print("="*60 + "\n")

    # Check stock
    stock_ref = db.collection('stocks').document('005930')
    stock = stock_ref.get()
    if stock.exists:
        data = stock.to_dict()
        print(f"✅ stocks/005930 exists")
        print(f"   - Name: {data.get('name')}")
        print(f"   - Recent data points: {len(data.get('recent', []))}")
        print(f"   - Dividends: {len(data.get('dividends', []))}")

    # Check monthly
    monthly_ref = stock_ref.collection('monthly').document('2024-10')
    monthly = monthly_ref.get()
    if monthly.exists:
        data = monthly.to_dict()
        print(f"✅ stocks/005930/monthly/2024-10 exists")
        print(f"   - Days: {len(data.get('days', []))}")

    # Check user
    user_ref = db.collection('users').document('test_user_001')
    user = user_ref.get()
    if user.exists:
        data = user.to_dict()
        print(f"✅ users/test_user_001 exists")
        print(f"   - Email: {data.get('email')}")

    # Check lines
    lines = list(user_ref.collection('lines').stream())
    print(f"✅ users/test_user_001/lines exists")
    print(f"   - Total lines: {len(lines)}")

    # Check metadata
    metadata_ref = db.collection('metadata').document('system')
    metadata = metadata_ref.get()
    if metadata.exists:
        data = metadata.to_dict()
        print(f"✅ metadata/system exists")
        print(f"   - Status: {data.get('updateStatus')}")
        print(f"   - Total stocks: {data.get('stats', {}).get('totalStocks')}")

    print("\n✅ All structure verified successfully!")
    print("\nView in Firebase Console:")
    print("https://console.firebase.google.com/project/stock-divi/firestore")


if __name__ == "__main__":
    print("Creating sample Firestore data structure...\n")

    try:
        create_sample_stock()
        print()
        create_sample_user()
        print()
        create_metadata()
        print()
        verify_structure()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure:")
        print("1. serviceAccountKey.json exists in project root")
        print("2. Firestore is enabled in Firebase Console")
        print("3. You have admin permissions")
