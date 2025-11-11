#!/usr/bin/env python3
"""
SQL to Firestore Migration Script
Migrates stock data from MariaDB to Firebase Firestore using Map-based structure

Copy this file to: migration/migrate.py
"""

import pymysql
import argparse
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import os
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv()

# Line style mapping
LINE_STYLE_MAP = {
    0: "solid",
    1: "dashed",
    2: "dotted"
}

# Period enum mapping
PERIOD_MAP = {
    'End': '월말',
    'Mid': '월중',
    'Non': '비해당'
}

class MigrationStats:
    """Track migration statistics"""
    def __init__(self):
        self.stocks_migrated = 0
        self.monthly_docs_created = 0
        self.dividends_migrated = 0
        self.lines_migrated = 0
        self.total_daily_records = 0
        self.errors = []

    def print_summary(self):
        print("\n" + "="*60)
        print("📊 Migration Summary")
        print("="*60)
        print(f"Stocks migrated: {self.stocks_migrated}")
        print(f"Monthly documents created: {self.monthly_docs_created}")
        print(f"Total daily records: {self.total_daily_records}")
        print(f"Dividends migrated: {self.dividends_migrated}")
        print(f"Horizontal lines migrated: {self.lines_migrated}")
        if self.errors:
            print(f"\n⚠️  Errors: {len(self.errors)}")
            for error in self.errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
        else:
            print("\n✅ No errors!")
        print("="*60)


class FirestoreMigration:
    """Handle migration from SQL to Firestore"""

    def __init__(self, limit=None, offset=None):
        self.stats = MigrationStats()
        self.db_connection = None
        self.firestore_db = None
        self.limit = limit
        self.offset = offset

    def connect_mariadb(self):
        """Connect to MariaDB database"""
        print("🔌 Connecting to MariaDB...")
        try:
            self.db_connection = pymysql.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 3306)),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME'),
                cursorclass=pymysql.cursors.DictCursor
            )
            print("✅ Connected to MariaDB")
        except Exception as e:
            print(f"❌ Failed to connect to MariaDB: {e}")
            raise

    def connect_firestore(self):
        """Initialize Firebase Admin SDK"""
        print("🔥 Connecting to Firestore...")
        try:
            cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
            if not os.path.exists(cred_path):
                raise FileNotFoundError(f"Firebase credentials not found at: {cred_path}")

            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            self.firestore_db = firestore.client()
            print("✅ Connected to Firestore")
        except Exception as e:
            print(f"❌ Failed to connect to Firestore: {e}")
            raise

    def fetch_stock_info(self):
        """Fetch stock info from SQL, with optional limit and offset"""
        query = "SELECT Code, Name, Period FROM stock_info ORDER BY Code"
        
        # Safely convert limit and offset to integers
        limit_val = int(self.limit) if self.limit is not None else None
        offset_val = int(self.offset) if self.offset is not None else None

        if limit_val is not None:
            query += f" LIMIT {limit_val}"
        if offset_val is not None:
            query += f" OFFSET {offset_val}"
        
        with self.db_connection.cursor() as cursor:
            print(f"  Executing query: {query}")
            cursor.execute(query)
            return cursor.fetchall()

    def fetch_dividends_by_code(self, code):
        """Fetch dividends for a specific stock"""
        with self.db_connection.cursor() as cursor:
            cursor.execute(
                "SELECT Date, Price FROM dividend WHERE Code = %s ORDER BY Date",
                (code,)
            )
            return cursor.fetchall()

    def fetch_stock_data_by_code(self, code):
        """Fetch daily stock data for a specific stock"""
        with self.db_connection.cursor() as cursor:
            cursor.execute(
                """SELECT Date, Open, High, Low, Close, Volume
                   FROM stock WHERE Code = %s ORDER BY Date""",
                (code,)
            )
            return cursor.fetchall()

    def fetch_horizontal_lines(self):
        """Fetch all horizontal lines"""
        with self.db_connection.cursor() as cursor:
            cursor.execute(
                """SELECT id, color, created_at, line_style, line_width,
                          memo, price, stock_code, updated_at
                   FROM horizontal"""
            )
            return cursor.fetchall()

    def fetch_data_time(self):
        """Fetch data time records"""
        with self.db_connection.cursor() as cursor:
            cursor.execute("SELECT Code, Time FROM data_time")
            return cursor.fetchall()

    def transform_dividends_to_map(self, dividends):
        """
        Transform dividend list to nested Map structure

        Input: [{'Date': '2025-01-24', 'Price': 124}, ...]
        Output: {'2025': {'01-24': 124}, ...}
        """
        dividend_map = {}

        for div in dividends:
            date_str = div['Date'].strftime('%Y-%m-%d') if hasattr(div['Date'], 'strftime') else str(div['Date'])
            price = int(div['Price'])

            year, month, day = date_str.split('-')
            month_day = f"{month}-{day}"

            if year not in dividend_map:
                dividend_map[year] = {}

            dividend_map[year][month_day] = price

        return dividend_map

    def transform_stock_data_to_monthly(self, stock_data):
        """
        Transform daily stock data to monthly Map structure

        Input: [{'Date': '2025-01-02', 'Open': 9895, ...}, ...]
        Output: {'2025-01': {'02': {close: 9860, ...}}, ...}
        """
        monthly_data = defaultdict(dict)

        for row in stock_data:
            date_str = row['Date'].strftime('%Y-%m-%d') if hasattr(row['Date'], 'strftime') else str(row['Date'])

            year, month, day = date_str.split('-')
            year_month = f"{year}-{month}"

            # Create day data
            monthly_data[year_month][day] = {
                'close': int(row['Close']),
                'volume': int(row['Volume']),
                'open': int(row['Open']),
                'low': int(row['Low']),
                'high': int(row['High'])
            }

        return dict(monthly_data)

    def migrate_stocks(self):
        """Migrate stock_info and dividends to stocks/{code}"""
        print("\n📈 Migrating stocks and dividends...")

        stock_infos = self.fetch_stock_info()
        total = len(stock_infos)

        for idx, stock_info in enumerate(stock_infos, 1):
            code = stock_info['Code']
            name = stock_info['Name']
            period = PERIOD_MAP.get(stock_info['Period'], stock_info['Period'])

            print(f"  [{idx}/{total}] Processing {code} - {name}")

            try:
                # Fetch dividends
                dividends = self.fetch_dividends_by_code(code)
                dividend_map = self.transform_dividends_to_map(dividends)
                self.stats.dividends_migrated += len(dividends)

                # Create stock document
                stock_doc_ref = self.firestore_db.collection('stocks').document(code)
                stock_doc_ref.set({
                    'name': name,
                    'period': period,
                    'dividends': dividend_map,
                    'updated_at': firestore.SERVER_TIMESTAMP
                })

                self.stats.stocks_migrated += 1
                print(f"      ✓ Created stock document with {len(dividends)} dividends")

            except Exception as e:
                error_msg = f"Error migrating stock {code}: {e}"
                print(f"      ✗ {error_msg}")
                self.stats.errors.append(error_msg)

    def migrate_monthly_data(self):
        """Migrate stock table to stocks/{code}/monthly/{YYYY-MM}"""
        print("\n📅 Migrating monthly data...")

        stock_infos = self.fetch_stock_info()
        total = len(stock_infos)

        for idx, stock_info in enumerate(stock_infos, 1):
            code = stock_info['Code']
            name = stock_info['Name']

            print(f"  [{idx}/{total}] Processing {code} - {name}")

            try:
                # Fetch all stock data
                stock_data = self.fetch_stock_data_by_code(code)
                self.stats.total_daily_records += len(stock_data)

                # Transform to monthly Map structure
                monthly_data = self.transform_stock_data_to_monthly(stock_data)

                # Create monthly documents
                batch = self.firestore_db.batch()
                batch_count = 0

                for year_month, days in monthly_data.items():
                    monthly_ref = (self.firestore_db.collection('stocks')
                                  .document(code)
                                  .collection('monthly')
                                  .document(year_month))

                    batch.set(monthly_ref, {'days': days})
                    batch_count += 1
                    self.stats.monthly_docs_created += 1

                    # Firestore batch limit is 500, commit if near limit
                    if batch_count >= 400:
                        batch.commit()
                        batch = self.firestore_db.batch()
                        batch_count = 0

                # Commit remaining
                if batch_count > 0:
                    batch.commit()

                print(f"      ✓ Created {len(monthly_data)} monthly documents ({len(stock_data)} daily records)")

            except Exception as e:
                error_msg = f"Error migrating monthly data for {code}: {e}"
                print(f"      ✗ {error_msg}")
                self.stats.errors.append(error_msg)

    def migrate_horizontal_lines(self):
        """Migrate horizontal lines to users/{userId}/lines/{lineId}"""
        print("\n📏 Migrating horizontal lines...")

        default_user_id = os.getenv('DEFAULT_USER_ID', 'default_user')
        lines = self.fetch_horizontal_lines()

        if not lines:
            print("  ℹ️  No horizontal lines to migrate")
            return

        for line in lines:
            line_id = f"line_{line['id']}"

            try:
                line_ref = (self.firestore_db.collection('users')
                           .document(default_user_id)
                           .collection('lines')
                           .document(line_id))

                line_ref.set({
                    'stockCode': line['stock_code'],
                    'price': float(line['price']),
                    'color': line['color'],
                    'style': LINE_STYLE_MAP.get(line['line_style'], 'solid'),
                    'width': int(line['line_width']),
                    'memo': line['memo'],
                    'created_at': line['created_at'],
                    'updated_at': line['updated_at']
                })

                self.stats.lines_migrated += 1
                print(f"  ✓ Migrated line {line_id} for stock {line['stock_code']}")

            except Exception as e:
                error_msg = f"Error migrating line {line_id}: {e}"
                print(f"  ✗ {error_msg}")
                self.stats.errors.append(error_msg)

    def migrate_metadata(self):
        """Migrate data_time to metadata/system"""
        print("\n🔧 Migrating metadata...")

        try:
            data_times = self.fetch_data_time()

            # Create stocks timestamp map
            stocks_map = {}
            latest_time = None

            for dt in data_times:
                code = dt['Code']
                time = dt['Time']
                stocks_map[code] = time

                if latest_time is None or time > latest_time:
                    latest_time = time

            # Create metadata document
            metadata_ref = self.firestore_db.collection('metadata').document('system')
            metadata_ref.set({
                'lastUpdate': latest_time,
                'lastSuccessfulUpdate': latest_time,
                'updateStatus': 'success',
                'stocks': stocks_map,
                'stats': {
                    'totalStocks': len(stocks_map),
                    'lastCalculated': firestore.SERVER_TIMESTAMP
                }
            })

            print(f"  ✓ Created metadata with {len(stocks_map)} stock timestamps")

        except Exception as e:
            error_msg = f"Error migrating metadata: {e}"
            print(f"  ✗ {error_msg}")
            self.stats.errors.append(error_msg)

    def verify_migration(self):
        """Verify migration data"""
        print("\n🔍 Verifying migration...")

        try:
            # Verify stocks collection
            stock_count = len(list(self.firestore_db.collection('stocks').stream()))
            print(f"  ✓ Stocks collection: {stock_count} documents")

            # Verify a sample stock
            if stock_count > 0:
                sample_stock = self.firestore_db.collection('stocks').limit(1).stream()
                for stock in sample_stock:
                    stock_data = stock.to_dict()
                    print(f"  ✓ Sample stock: {stock.id}")
                    print(f"      - Name: {stock_data.get('name')}")
                    print(f"      - Period: {stock_data.get('period')}")
                    print(f"      - Dividends: {len(stock_data.get('dividends', {}))} years")

                    # Check monthly data
                    monthly_docs = self.firestore_db.collection('stocks').document(stock.id).collection('monthly').stream()
                    monthly_count = len(list(monthly_docs))
                    print(f"      - Monthly docs: {monthly_count}")

            # Verify metadata
            metadata = self.firestore_db.collection('metadata').document('system').get()
            if metadata.exists:
                meta_data = metadata.to_dict()
                print(f"  ✓ Metadata document exists")
                print(f"      - Last update: {meta_data.get('lastUpdate')}")
                print(f"      - Stocks tracked: {len(meta_data.get('stocks', {}))}")

            print("\n✅ Verification complete!")

        except Exception as e:
            print(f"⚠️  Verification error: {e}")

    def run(self):
        """Run the complete migration"""
        print("="*60)
        print("🚀 Starting SQL to Firestore Migration")
        print("="*60)

        try:
            # Connect to databases
            self.connect_mariadb()
            self.connect_firestore()

            # Run migration steps
            self.migrate_stocks()
            self.migrate_monthly_data()
            self.migrate_horizontal_lines()
            self.migrate_metadata()

            # Verify
            self.verify_migration()

            # Print summary
            self.stats.print_summary()

            return True

        except Exception as e:
            print(f"\n❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            # Clean up connections
            if self.db_connection:
                self.db_connection.close()
                print("\n🔌 Closed MariaDB connection")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="SQL to Firestore Migration Script. Use --limit and --offset to migrate in chunks.")
    parser.add_argument('--limit', type=int, help='Number of stock records to process.')
    parser.add_argument('--offset', type=int, help='Offset to start processing stock records from.')
    args = parser.parse_args()

    if args.limit is not None:
        print(f"▶️  Running in chunk mode: LIMIT={args.limit}, OFFSET={args.offset or 0}")

    # Check environment variables
    required_vars = ['DB_USER', 'DB_PASSWORD', 'DB_NAME', 'FIREBASE_CREDENTIALS_PATH']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please create a .env file based on .env.example")
        return

    # Run migration
    migration = FirestoreMigration(limit=args.limit, offset=args.offset)
    success = migration.run()

    if success:
        print("\n🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Check Firebase Console to verify data")
        if args.limit is not None:
            next_offset = (args.offset or 0) + args.limit
            print("2. To migrate the next chunk, run:")
            print(f"   python migrate.py --limit {args.limit} --offset {next_offset}")
        else:
            print("2. Proceed to Week 3: Cloud Function development")
    else:
        print("\n⚠️  Migration completed with errors. Please review the error messages above.")


if __name__ == '__main__':
    main()
