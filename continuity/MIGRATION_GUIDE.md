# SQL to Firebase Migration Guide

## 📊 Overview

This guide explains how to migrate your SQL data from `DB/stockdata_1106.sql` to Firebase Firestore using the Map-based structure defined in `DATA_STRUCTURE.md`.

---

## 🗂️ SQL Data Structure Analysis

### Current Tables

Your `stockdata_1106.sql` contains:

| Table | Records | Purpose |
|-------|---------|---------|
| **stock_info** | 7 stocks | 종목 기본 정보 (Code, Name, Period) |
| **dividend** | ~90 records | 배당 정보 (Code, Date, Price) |
| **stock** | ~2,500 records | 일별 주식 데이터 (Code, Date, OHLCV) |
| **horizontal** | 1 record | 가로선 사용자 데이터 |
| **data_time** | 7 records | 마지막 데이터 갱신 시간 |

### Stock Codes
- 475080: KODEX 테슬라커버드콜채권혼합액티브
- 475720: RISE 200위클리커버드콜
- 480020: ACE 미국빅테크7+데일리타겟커버드콜(합성)
- 480030: ACE 미국500데일리타겟커버드콜(합성)
- 480040: ACE 미국반도체데일리타겟커버드콜(합성)
- 490590: RISE 미국AI밸류체인데일리고정커버드콜
- 491620: RISE 미국테크100데일리고정커버드콜

---

## 🎯 Migration Target Structure

### Firestore Collections

```
firestore/
├── stocks/
│   └── {code}/                      # 예: "475080"
│       ├── name: "KODEX 테슬라..."
│       ├── period: "End"
│       ├── dividends: {             # Map 구조
│       │   "2025": {
│       │     "01-24": 124,
│       │     "02-27": 112,
│       │     ...
│       │   }
│       │ }
│       ├── updated_at: Timestamp
│       │
│       └── monthly/
│           ├── 2025-01/
│           │   └── days: {          # Map 구조
│           │       "02": {close: 9860, volume: 402903, ...},
│           │       "03": {close: 9720, volume: 515668, ...}
│           │     }
│           ├── 2025-02/
│           ├── 2025-03/
│           ...
│
├── users/
│   └── {defaultUserId}/
│       └── lines/
│           └── {lineId}/
│               ├── stockCode: "475080"
│               ├── price: 8000.00
│               ├── color: "#ff0000"
│               ...
│
└── metadata/
    └── system/
        ├── lastUpdate: Timestamp
        ├── stocks: {"475080": Timestamp, ...}
        ...
```

---

## 📋 Step-by-Step Migration Process

### Method 1: Python Script (Recommended)

This is the most straightforward method. You'll need:
1. MySQL/MariaDB running locally with the SQL file imported
2. Python with Firebase Admin SDK
3. Firebase project credentials

#### Step 1: Prepare Environment

```bash
# Install required packages
pip install firebase-admin pymysql python-dotenv

# Project structure
stockchart_migration/
├── .env                          # Environment variables
├── firebase-credentials.json     # Firebase service account key
├── migrate.py                    # Main migration script
└── DB/
    └── stockdata_1106.sql       # Your SQL dump
```

#### Step 2: Import SQL Data

```bash
# If you have MariaDB/MySQL installed:
mysql -u root -p -e "CREATE DATABASE stockdata;"
mysql -u root -p stockdata < DB/stockdata_1106.sql

# Verify import
mysql -u root -p -e "USE stockdata; SHOW TABLES;"
```

#### Step 3: Configuration

Create `.env` file:
```env
# MariaDB Configuration
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=stockdata

# Firebase Configuration
FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
```

#### Step 4: Run Migration Script

The script will:
1. Connect to MariaDB
2. Connect to Firestore
3. Transform data to Map structure
4. Upload to Firestore

**Total time**: ~2-5 minutes for 7 stocks

---

### Method 2: Direct JSON Conversion (Alternative)

If you don't want to import SQL to a database, you can:
1. Parse the SQL file directly
2. Extract INSERT statements
3. Convert to Firebase JSON format
4. Import via Firebase Console or script

---

## 🔄 Data Transformation Details

### 1. stock_info + dividend → stocks/{code}

**SQL Data**:
```sql
-- stock_info
('475080', 'KODEX 테슬라커버드콜채권혼합액티브', 'End')

-- dividend
('475080', '2025-01-24', 124),
('475080', '2025-02-27', 112),
('475080', '2025-03-28', 110)
```

**Firestore Document** (`stocks/475080`):
```javascript
{
  name: "KODEX 테슬라커버드콜채권혼합액티브",
  period: "End",
  dividends: {
    "2025": {
      "01-24": 124,
      "02-27": 112,
      "03-28": 110
    }
  },
  updated_at: Timestamp
}
```

**Transformation Logic**:
```python
# Group dividends by year and convert to nested Map
dividends_map = {}
for dividend in sql_dividends:
    code = dividend['Code']
    date = dividend['Date']  # '2025-01-24'
    price = dividend['Price']

    year, month, day = date.split('-')
    month_day = f"{month}-{day}"  # "01-24"

    if year not in dividends_map:
        dividends_map[year] = {}

    dividends_map[year][month_day] = price

# Result:
# {
#   "2025": {
#     "01-24": 124,
#     "02-27": 112,
#     "03-28": 110
#   }
# }
```

### 2. stock → stocks/{code}/monthly/{YYYY-MM}

**SQL Data**:
```sql
('475080', '2025-01-02', 9895, 10035, 9810, 9860, 402903),
('475080', '2025-01-03', 9790, 9790, 9665, 9720, 515668),
('475080', '2025-02-03', 9875, 9875, 9780, 9790, 341801)
```

**Firestore Document** (`stocks/475080/monthly/2025-01`):
```javascript
{
  days: {
    "02": {
      close: 9860,
      volume: 402903,
      open: 9895,
      low: 9810,
      high: 10035
    },
    "03": {
      close: 9720,
      volume: 515668,
      open: 9790,
      low: 9665,
      high: 9790
    }
  }
}
```

**Transformation Logic**:
```python
# Group daily data by month
monthly_data = {}  # {stock_code: {year_month: {day: data}}}

for stock_row in sql_stock_data:
    code = stock_row['Code']
    date = stock_row['Date']  # '2025-01-02'

    year, month, day = date.split('-')
    year_month = f"{year}-{month}"  # "2025-01"

    if code not in monthly_data:
        monthly_data[code] = {}
    if year_month not in monthly_data[code]:
        monthly_data[code][year_month] = {}

    monthly_data[code][year_month][day] = {
        'close': stock_row['Close'],
        'volume': stock_row['Volume'],
        'open': stock_row['Open'],
        'low': stock_row['Low'],
        'high': stock_row['High']
    }

# Upload to Firestore
for code, months in monthly_data.items():
    for year_month, days in months.items():
        firestore.collection('stocks').doc(code) \
          .collection('monthly').doc(year_month) \
          .set({'days': days})
```

### 3. horizontal → users/{userId}/lines/{lineId}

**SQL Data**:
```sql
(17, '#ff0000', '2025-08-19 23:00:46.061583', 0, 2, NULL, 8000.00, '475080', '2025-08-19 23:00:46.061590')
```

**Firestore Document** (`users/default_user/lines/line_17`):
```javascript
{
  stockCode: "475080",
  price: 8000.00,
  color: "#ff0000",
  style: "solid",  // 0 → "solid"
  width: 2,
  memo: null,
  created_at: Timestamp("2025-08-19T23:00:46.061583Z"),
  updated_at: Timestamp("2025-08-19T23:00:46.061590Z")
}
```

**Transformation Logic**:
```python
# Map line_style values
LINE_STYLE_MAP = {
    0: "solid",
    1: "dashed",
    2: "dotted"
}

for line in sql_horizontal_data:
    line_id = f"line_{line['id']}"

    firestore.collection('users').doc('default_user') \
      .collection('lines').doc(line_id).set({
        'stockCode': line['stock_code'],
        'price': float(line['price']),
        'color': line['color'],
        'style': LINE_STYLE_MAP.get(line['line_style'], 'solid'),
        'width': line['line_width'],
        'memo': line['memo'],
        'created_at': line['created_at'],
        'updated_at': line['updated_at']
    })
```

### 4. data_time → metadata/system

**SQL Data**:
```sql
('475080', '2025-11-06 06:40:00'),
('475720', '2025-11-06 06:40:01')
```

**Firestore Document** (`metadata/system`):
```javascript
{
  lastUpdate: Timestamp("2025-11-06T06:40:02Z"),
  stocks: {
    "475080": Timestamp("2025-11-06T06:40:00Z"),
    "475720": Timestamp("2025-11-06T06:40:01Z"),
    "480020": Timestamp("2025-11-06T06:40:01Z"),
    ...
  },
  stats: {
    totalStocks: 7,
    lastCalculated: Timestamp
  }
}
```

---

## ✅ Validation Checklist

After migration, verify:

### Data Count
- [ ] 7 documents in `stocks/` collection
- [ ] Each stock has correct number of monthly subcollections
  - Example: Stock with data from Jan-Nov 2025 = 11 monthly documents
- [ ] 1 document in `users/default_user/lines/`
- [ ] 1 document in `metadata/system`

### Data Structure
- [ ] Each stock document has:
  - [ ] `name` field (string)
  - [ ] `period` field (string: "End", "Mid", or "Non")
  - [ ] `dividends` field (nested Map)
  - [ ] `updated_at` field (Timestamp)
- [ ] Each monthly document has:
  - [ ] `days` field (Map with day keys like "01", "15")
  - [ ] Each day has: close, volume, open, low, high

### Data Accuracy
- [ ] Pick random date from SQL and verify in Firestore
  - SQL: `SELECT * FROM stock WHERE Code='475080' AND Date='2025-01-02'`
  - Firestore: `stocks/475080/monthly/2025-01/days/02`
  - Values should match exactly
- [ ] Verify dividend amounts
  - SQL: `SELECT * FROM dividend WHERE Code='475080'`
  - Firestore: `stocks/475080/dividends`
- [ ] Check total data points
  - SQL: `SELECT COUNT(*) FROM stock WHERE Code='475080'`
  - Firestore: Count all days across all monthly documents

### Sample Queries

```python
# Test 1: Load stock info
stock_doc = db.collection('stocks').doc('475080').get()
print(stock_doc.to_dict()['name'])  # Should: KODEX 테슬라...
print(stock_doc.to_dict()['period'])  # Should: End

# Test 2: Load January 2025 data
jan_doc = db.collection('stocks').doc('475080') \
  .collection('monthly').doc('2025-01').get()
days = jan_doc.to_dict()['days']
print(len(days))  # Should: number of trading days in Jan 2025
print(days['02'])  # Should: {close: 9860, volume: 402903, ...}

# Test 3: Load dividends
dividends = stock_doc.to_dict()['dividends']
print(dividends['2025']['01-24'])  # Should: 124
```

---

## 📊 Migration Statistics

**Expected Results**:

| Metric | Value |
|--------|-------|
| Total stocks | 7 |
| Total stock documents | 7 |
| Total monthly documents | ~70-80 (7 stocks × ~11 months each) |
| Total daily data points | ~2,500 |
| Total dividends | ~90 |
| Total horizontal lines | 1 |
| Total Firestore writes | ~150-160 |
| Estimated time | 2-5 minutes |
| Estimated cost | $0 (under free tier) |

---

## 🔧 Migration Script Outline

```python
# migrate.py

import pymysql
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# 1. Initialize Firebase
cred = credentials.Certificate(os.getenv('FIREBASE_CREDENTIALS_PATH'))
firebase_admin.initialize_app(cred)
db = firestore.client()

# 2. Connect to MariaDB
connection = pymysql.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME'),
    cursorclass=pymysql.cursors.DictCursor
)

# 3. Migrate stock_info + dividends
def migrate_stocks():
    """Migrate stock_info and dividends to stocks/{code}"""
    # Implementation details in actual script
    pass

# 4. Migrate stock data to monthly structure
def migrate_monthly_data():
    """Migrate stock table to stocks/{code}/monthly/{YYYY-MM}"""
    # Implementation details in actual script
    pass

# 5. Migrate horizontal lines
def migrate_horizontal_lines():
    """Migrate horizontal to users/{userId}/lines/{lineId}"""
    # Implementation details in actual script
    pass

# 6. Migrate metadata
def migrate_metadata():
    """Migrate data_time to metadata/system"""
    # Implementation details in actual script
    pass

# 7. Verify migration
def verify_migration():
    """Run validation checks"""
    # Implementation details in actual script
    pass

# Main execution
if __name__ == '__main__':
    print("🚀 Starting migration...")
    migrate_stocks()
    migrate_monthly_data()
    migrate_horizontal_lines()
    migrate_metadata()
    print("✅ Migration complete!")

    print("🔍 Verifying data...")
    verify_migration()
    print("✅ Verification complete!")
```

---

## 🚨 Important Notes

### Date Formatting
- SQL dates: `2025-01-02` (YYYY-MM-DD)
- Firestore Map keys:
  - Year: `"2025"` (string, 4 digits)
  - Month-Day: `"01-24"` (string, MM-DD with zero padding)
  - Day only: `"02"` (string, DD with zero padding)

### Data Types
- **Numbers**: All stock prices and volumes should be stored as numbers (not strings)
- **Timestamps**: Convert SQL DATETIME to Firestore Timestamp
- **Strings**: Stock codes, names should be strings

### Zero Padding
```python
# Correct
"01", "02", "03", ..., "31"

# Incorrect
"1", "2", "3", ..., "31"
```

### Batch Operations
For efficiency, use Firestore batch writes:
```python
batch = db.batch()

# Add up to 500 operations
for i in range(min(500, len(operations))):
    # batch.set(...)
    pass

batch.commit()
```

---

## 🎯 Next Steps

1. **Week 1**: Set up Firebase project (see MIGRATION_PLAN.md Week 1)
2. **Week 2 Day 1**: Create migration script based on this guide
3. **Week 2 Day 2**: Run migration and verify
4. **Week 3+**: Continue with Cloud Functions and React app

---

## 📚 Related Documents

- [DATA_STRUCTURE.md](./DATA_STRUCTURE.md) - Target Firestore structure
- [MIGRATION_PLAN.md](./MIGRATION_PLAN.md) - Overall migration timeline
- [IMPLEMENTATION_GUIDE.md](./IMPLEMENTATION_GUIDE.md) - Detailed implementation

---

## ❓ FAQ

**Q: Can I migrate without importing to MariaDB?**
A: Yes, you can parse the SQL file directly and extract INSERT statements, but it's more complex. Using a database is recommended.

**Q: How long does migration take?**
A: For 7 stocks with ~2,500 daily records, expect 2-5 minutes.

**Q: What if migration fails halfway?**
A: Firestore writes are atomic. You can safely delete all data and restart. Or use Firestore transactions for critical sections.

**Q: Can I test with sample data first?**
A: Yes! Migrate just 1 stock first to verify the structure is correct.

**Q: Do I need to migrate horizontal lines?**
A: Only if you want to preserve existing user data. You can skip this if starting fresh.
