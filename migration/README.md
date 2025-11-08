# SQL to Firestore Migration

This directory contains the migration script to transfer your stock data from MariaDB to Firebase Firestore with the Map-based structure.

## 📁 Files

```
migration/
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .env                  # Your actual config (create this, not in git)
├── migrate.py            # Main migration script (copy from continuity/migrate_script.py)
└── firebase-credentials.json  # Firebase service account key (not in git)
```

## 🚀 Quick Start

### Step 1: Copy Migration Script

```bash
# Copy the migration script
cp ../continuity/migrate_script.py ./migrate.py
```

### Step 2: Install Dependencies

```bash
# Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### Step 3: Set Up MariaDB

Import your SQL file to a local MariaDB/MySQL database:

```bash
# Create database
mysql -u root -p -e "CREATE DATABASE stockdata;"

# Import SQL file
mysql -u root -p stockdata < ../DB/stockdata_1106.sql

# Verify import
mysql -u root -p -e "USE stockdata; SHOW TABLES;"
# Should show: data_time, dividend, horizontal, stock, stock_info
```

### Step 4: Set Up Firebase

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project or select existing
3. Go to Project Settings → Service Accounts
4. Click "Generate New Private Key"
5. Save the JSON file as `firebase-credentials.json` in this directory

### Step 5: Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit .env with your values
```

Edit `.env`:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_actual_password
DB_NAME=stockdata

FIREBASE_CREDENTIALS_PATH=./firebase-credentials.json
DEFAULT_USER_ID=default_user
```

### Step 6: Run Migration

```bash
python migrate.py
```

Expected output:
```
============================================================
🚀 Starting SQL to Firestore Migration
============================================================
🔌 Connecting to MariaDB...
✅ Connected to MariaDB
🔥 Connecting to Firestore...
✅ Connected to Firestore

📈 Migrating stocks and dividends...
  [1/7] Processing 475080 - KODEX 테슬라커버드콜채권혼합액티브
      ✓ Created stock document with 13 dividends
  [2/7] Processing 475720 - RISE 200위클리커버드콜
      ✓ Created stock document with 12 dividends
  ...

📅 Migrating monthly data...
  [1/7] Processing 475080 - KODEX 테슬라커버드콜채권혼합액티브
      ✓ Created 11 monthly documents (231 daily records)
  ...

📏 Migrating horizontal lines...
  ✓ Migrated line line_17 for stock 475080

🔧 Migrating metadata...
  ✓ Created metadata with 7 stock timestamps

🔍 Verifying migration...
  ✓ Stocks collection: 7 documents
  ✓ Sample stock: 475080
      - Name: KODEX 테슬라커버드콜채권혼합액티브
      - Period: 월말
      - Dividends: 1 years
      - Monthly docs: 11
  ✓ Metadata document exists
      - Last update: 2025-11-06 06:40:02
      - Stocks tracked: 7

✅ Verification complete!

============================================================
📊 Migration Summary
============================================================
Stocks migrated: 7
Monthly documents created: 77
Total daily records: 2500
Dividends migrated: 90
Horizontal lines migrated: 1

✅ No errors!
============================================================

🔌 Closed MariaDB connection

🎉 Migration completed successfully!

Next steps:
1. Check Firebase Console to verify data
2. Run test queries to validate data accuracy
3. Proceed to Week 3: Cloud Function development
```

## 🔍 Verification

### Check Firebase Console

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project
3. Go to Firestore Database
4. You should see:
   - `stocks` collection with 7 documents
   - `users` collection with 1 document
   - `metadata` collection with 1 document

### Verify Data Structure

Click on a stock document (e.g., `475080`):
```
stocks/475080/
├── name: "KODEX 테슬라커버드콜채권혼합액티브"
├── period: "월말"
├── dividends: {
│   "2025": {
│     "01-24": 124,
│     "02-27": 112,
│     ...
│   }
│ }
├── updated_at: Timestamp
│
└── monthly (subcollection)
    ├── 2025-01
    │   └── days: {
    │       "02": {close: 9860, volume: 402903, ...},
    │       "03": {close: 9720, volume: 515668, ...}
    │     }
    ├── 2025-02
    ├── 2025-03
    ...
```

## 🔧 Troubleshooting

### Error: Failed to connect to MariaDB

```
❌ Failed to connect to MariaDB: (2003, "Can't connect to MySQL server on 'localhost'")
```

**Solution**:
- Make sure MariaDB/MySQL is running
- Check DB_HOST, DB_PORT in .env
- Verify credentials

### Error: Firebase credentials not found

```
❌ Failed to connect to Firestore: Firebase credentials not found at: ./firebase-credentials.json
```

**Solution**:
- Download Firebase service account key
- Place in migration/ directory
- Update FIREBASE_CREDENTIALS_PATH in .env

### Error: Database 'stockdata' doesn't exist

```
❌ Failed to connect to MariaDB: (1049, "Unknown database 'stockdata'")
```

**Solution**:
```bash
mysql -u root -p -e "CREATE DATABASE stockdata;"
mysql -u root -p stockdata < ../DB/stockdata_1106.sql
```

### Migration runs but shows errors

Check the error messages in the summary. Common issues:
- **Permission denied**: Check Firebase security rules
- **Invalid data**: Check SQL data format
- **Network timeout**: Check internet connection

## 📊 Expected Migration Statistics

For your SQL file (`stockdata_1106.sql`):

| Metric | Value |
|--------|-------|
| Stocks | 7 |
| Stock documents | 7 |
| Monthly documents | ~70-77 |
| Daily data points | ~2,500 |
| Dividends | ~90 |
| Horizontal lines | 1 |
| Total Firestore writes | ~155 |
| Time | 2-5 minutes |
| Cost | $0 (free tier) |

## 🔐 Security Notes

### DO NOT commit these files to git:

- `.env` (contains passwords)
- `firebase-credentials.json` (sensitive)

They are already in `.gitignore`.

### Safe to commit:

- `requirements.txt`
- `.env.example`
- `migrate.py`
- `README.md`

## 📝 Next Steps

After successful migration:

1. **Verify in Firebase Console**
   - Check all 7 stocks exist
   - Open a stock and verify monthly data
   - Check dividends Map structure

2. **Test Queries** (optional)
   ```python
   # Test script in Python console
   import firebase_admin
   from firebase_admin import credentials, firestore

   cred = credentials.Certificate('./firebase-credentials.json')
   firebase_admin.initialize_app(cred)
   db = firestore.client()

   # Get a stock
   stock = db.collection('stocks').document('475080').get()
   print(stock.to_dict()['name'])

   # Get monthly data
   monthly = db.collection('stocks').document('475080') \
     .collection('monthly').document('2025-01').get()
   print(len(monthly.to_dict()['days']))
   ```

3. **Continue to Week 3** in MIGRATION_PLAN.md
   - Set up Cloud Functions
   - Implement daily data updates
   - Schedule automation

## 🆘 Need Help?

1. Check [MIGRATION_GUIDE.md](../continuity/MIGRATION_GUIDE.md) for detailed explanations
2. Review [DATA_STRUCTURE.md](../continuity/DATA_STRUCTURE.md) for structure details
3. Check [MIGRATION_PLAN.md](../continuity/MIGRATION_PLAN.md) for the overall plan

## 📚 Resources

- [Firebase Admin SDK for Python](https://firebase.google.com/docs/admin/setup)
- [Firestore Data Model](https://firebase.google.com/docs/firestore/data-model)
- [PyMySQL Documentation](https://pymysql.readthedocs.io/)
