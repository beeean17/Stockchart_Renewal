#!/usr/bin/env python3
"""
Migration Setup Checker
Checks if all requirements are met before running migration
"""

import os
import sys

def check_setup():
    """Check if everything is ready for migration"""
    print("="*60)
    print("🔍 Migration Setup Checker")
    print("="*60)

    all_good = True

    # 1. Check .env file
    print("\n1. Checking .env file...")
    if os.path.exists('.env'):
        print("   ✅ .env file exists")

        # Check required variables
        from dotenv import load_dotenv
        load_dotenv()

        required_vars = ['DB_USER', 'DB_PASSWORD', 'DB_NAME', 'FIREBASE_CREDENTIALS_PATH']
        missing = []

        for var in required_vars:
            if not os.getenv(var):
                missing.append(var)

        if missing:
            print(f"   ⚠️  Missing variables in .env: {', '.join(missing)}")
            all_good = False
        else:
            print("   ✅ All required variables present")
    else:
        print("   ❌ .env file not found")
        print("   → Create it: cp .env.example .env")
        all_good = False

    # 2. Check Firebase credentials
    print("\n2. Checking Firebase credentials...")
    if os.path.exists('.env'):
        from dotenv import load_dotenv
        load_dotenv()
        cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH', './firebase-credentials.json')

        if os.path.exists(cred_path):
            print(f"   ✅ Firebase credentials found at {cred_path}")
        else:
            print(f"   ❌ Firebase credentials not found at {cred_path}")
            print("   → Download from Firebase Console:")
            print("      1. Go to Project Settings → Service Accounts")
            print("      2. Click 'Generate New Private Key'")
            print(f"      3. Save as {cred_path}")
            all_good = False
    else:
        print("   ⚠️  Cannot check (no .env file)")

    # 3. Check Python packages
    print("\n3. Checking Python packages...")
    try:
        import pymysql
        print("   ✅ pymysql installed")
    except ImportError:
        print("   ❌ pymysql not installed")
        print("   → Run: pip install -r requirements.txt")
        all_good = False

    try:
        import firebase_admin
        print("   ✅ firebase-admin installed")
    except ImportError:
        print("   ❌ firebase-admin not installed")
        print("   → Run: pip install -r requirements.txt")
        all_good = False

    try:
        import dotenv
        print("   ✅ python-dotenv installed")
    except ImportError:
        print("   ❌ python-dotenv not installed")
        print("   → Run: pip install -r requirements.txt")
        all_good = False

    # 4. Check MariaDB connection (if .env exists)
    print("\n4. Checking MariaDB connection...")
    if os.path.exists('.env'):
        try:
            import pymysql
            from dotenv import load_dotenv
            load_dotenv()

            connection = pymysql.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 3306)),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME')
            )
            connection.close()
            print("   ✅ Successfully connected to MariaDB")

            # Check if tables exist
            connection = pymysql.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 3306)),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME')
            )
            cursor = connection.cursor()
            cursor.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            connection.close()

            required_tables = ['stock_info', 'stock', 'dividend', 'horizontal', 'data_time']
            missing_tables = [t for t in required_tables if t not in tables]

            if missing_tables:
                print(f"   ⚠️  Missing tables: {', '.join(missing_tables)}")
                print("   → Import SQL file:")
                print(f"      mysql -u {os.getenv('DB_USER')} -p {os.getenv('DB_NAME')} < ../DB/stockdata_1106.sql")
                all_good = False
            else:
                print(f"   ✅ All required tables present: {', '.join(tables)}")

        except Exception as e:
            print(f"   ❌ Cannot connect to MariaDB: {e}")
            print("   → Check your .env configuration")
            print("   → Make sure MariaDB is running")
            all_good = False
    else:
        print("   ⚠️  Cannot check (no .env file)")

    # 5. Check SQL file
    print("\n5. Checking SQL data file...")
    if os.path.exists('../DB/stockdata_1106.sql'):
        print("   ✅ SQL file found at ../DB/stockdata_1106.sql")
    else:
        print("   ❌ SQL file not found at ../DB/stockdata_1106.sql")
        all_good = False

    # Summary
    print("\n" + "="*60)
    if all_good:
        print("✅ All checks passed! Ready to migrate.")
        print("\nRun migration:")
        print("  python migrate.py")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        print("\nQuick setup:")
        print("  1. cp .env.example .env")
        print("  2. Edit .env with your credentials")
        print("  3. pip install -r requirements.txt")
        print("  4. Download Firebase credentials")
        print("  5. Import SQL: mysql -u root -p < ../DB/stockdata_1106.sql")
    print("="*60)

    return all_good

if __name__ == '__main__':
    success = check_setup()
    sys.exit(0 if success else 1)
