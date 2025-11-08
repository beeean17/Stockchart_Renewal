# Migration Setup Steps

## Current Progress
- [x] Migration script copied
- [x] .env file created
- [ ] Configure database credentials
- [ ] Install Python packages
- [ ] Set up MariaDB
- [ ] Get Firebase credentials
- [ ] Run migration

---

## Step 1: Configure Database Credentials ⏳

Edit `migration/.env` and update your database password:

```env
DB_PASSWORD=your_actual_password
```

**If you don't have MariaDB set up yet**, you can:
- Option A: Install MariaDB locally
- Option B: Use MySQL (compatible)
- Option C: Use Docker: `docker run --name mariadb -e MYSQL_ROOT_PASSWORD=yourpassword -p 3306:3306 -d mariadb`

---

## Step 2: Install Python Dependencies

```bash
cd migration
pip install -r requirements.txt
```

This installs:
- firebase-admin (for Firestore)
- pymysql (for database connection)
- python-dotenv (for .env file)

---

## Step 3: Set Up MariaDB Database

### Create database and import SQL:

```bash
# Create database
mysql -u root -p -e "CREATE DATABASE stockdata;"

# Import your SQL file
mysql -u root -p stockdata < ../DB/stockdata_1106.sql

# Verify import
mysql -u root -p -e "USE stockdata; SHOW TABLES;"
```

You should see 5 tables:
- data_time
- dividend
- horizontal
- stock
- stock_info

---

## Step 4: Get Firebase Credentials

### A. Create/Select Firebase Project

1. Go to https://console.firebase.google.com/
2. Create new project or select existing
3. Project name: "stock-chart-app" (or your choice)

### B. Enable Firestore

1. In Firebase Console, go to "Firestore Database"
2. Click "Create Database"
3. Start in **Production mode** (we'll set rules later)
4. Choose location: **asia-northeast3 (Seoul)** or asia-northeast1 (Tokyo)

### C. Download Service Account Key

1. Go to **Project Settings** (gear icon)
2. Go to **Service Accounts** tab
3. Click **"Generate New Private Key"**
4. Save the downloaded JSON file as:
   `migration/firebase-credentials.json`

⚠️ Keep this file secure! Don't commit to git.

---

## Step 5: Verify Setup

Run the check script:

```bash
cd migration
python -c "
import os

print('Checking setup...')
print()

# Check .env
print('1. .env file:', 'OK' if os.path.exists('.env') else 'MISSING')

# Check Firebase credentials
print('2. Firebase credentials:', 'OK' if os.path.exists('firebase-credentials.json') else 'MISSING')

# Check packages
try:
    import pymysql
    print('3. pymysql package: OK')
except:
    print('3. pymysql package: MISSING (run: pip install -r requirements.txt)')

try:
    import firebase_admin
    print('4. firebase-admin package: OK')
except:
    print('4. firebase-admin package: MISSING (run: pip install -r requirements.txt)')
"
```

---

## Step 6: Run Migration

Once all checks pass:

```bash
cd migration
python migrate.py
```

Expected output:
```
============================================================
Starting SQL to Firestore Migration
============================================================
Connecting to MariaDB... OK
Connecting to Firestore... OK

Migrating stocks and dividends...
  [1/7] Processing 475080 - KODEX 테슬라커버드콜채권혼합액티브
      Created stock document with 13 dividends
...

Migration Summary
Stocks migrated: 7
Monthly documents created: 77
Total daily records: 2500
Dividends migrated: 90

Migration completed successfully!
```

---

## Step 7: Verify in Firebase Console

1. Go to Firebase Console
2. Navigate to **Firestore Database**
3. You should see:
   - **stocks** collection (7 documents)
   - **users** collection (1 document)
   - **metadata** collection (1 document)

4. Click on a stock document (e.g., 475080):
   - Check `name`, `period` fields
   - Check `dividends` Map structure
   - Check `monthly` subcollection

---

## Troubleshooting

### "Cannot connect to MariaDB"
- Check if MariaDB is running
- Verify DB_USER and DB_PASSWORD in .env
- Try: `mysql -u root -p -e "SHOW DATABASES;"`

### "Firebase credentials not found"
- Make sure file is named exactly `firebase-credentials.json`
- Check it's in the `migration/` directory
- Verify path in .env file

### "ModuleNotFoundError"
- Run: `pip install -r requirements.txt`
- Make sure you're in the migration directory

### "Database 'stockdata' doesn't exist"
- Run: `mysql -u root -p -e "CREATE DATABASE stockdata;"`
- Import SQL: `mysql -u root -p stockdata < ../DB/stockdata_1106.sql`

---

## Quick Command Reference

```bash
# Install packages
pip install -r requirements.txt

# Create database
mysql -u root -p -e "CREATE DATABASE stockdata;"

# Import SQL
mysql -u root -p stockdata < ../DB/stockdata_1106.sql

# Run migration
python migrate.py

# Check MariaDB
mysql -u root -p -e "USE stockdata; SELECT COUNT(*) FROM stock;"

# Test Firebase (after migration)
python -c "
import firebase_admin
from firebase_admin import credentials, firestore
cred = credentials.Certificate('./firebase-credentials.json')
firebase_admin.initialize_app(cred)
db = firestore.client()
print('Stocks:', len(list(db.collection('stocks').stream())))
"
```

---

## Need Help?

Check these files for more details:
- `README.md` - Full documentation
- `../continuity/MIGRATION_GUIDE.md` - Detailed transformation guide
- `../continuity/MIGRATION_PLAN.md` - Overall migration plan
