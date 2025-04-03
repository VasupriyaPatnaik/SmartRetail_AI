import sqlite3
import pandas as pd

def create_table():
    # Connect to SQLite database
    conn = sqlite3.connect("database/retail.db")
    cursor = conn.cursor()

    # Create Demand Forecasting Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS DemandForecasting (
        "Product ID" INTEGER,
        "Date" TEXT,
        "Store ID" INTEGER,
        "Sales Quantity" INTEGER,
        "Price" REAL,
        "Promotions" TEXT,
        "Seasonality Factors" TEXT,
        "External Factors" TEXT,
        "Demand Trend" TEXT,
        "Customer Segments" TEXT
    )
    """)

    # Create Inventory Monitoring Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS InventoryMonitoring (
        "Product ID" INTEGER,
        "Store ID" INTEGER,
        "Stock Levels" INTEGER,
        "Supplier Lead Time (days)" INTEGER,
        "Stockout Frequency" INTEGER,
        "Reorder Point" INTEGER,
        "Expiry Date" TEXT,
        "Warehouse Capacity" INTEGER,
        "Order Fulfillment Time (days)" INTEGER
    )
    """)

    # Create Pricing Optimization Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS PricingOptimization (
        "Product ID" INTEGER,
        "Store ID" INTEGER,
        "Price" REAL,
        "Competitor Prices" REAL,
        "Discounts" REAL,
        "Sales Volume" INTEGER,
        "Customer Reviews" INTEGER,
        "Return Rate (%)" REAL,
        "Storage Cost" REAL,
        "Elasticity Index" REAL
    )
    """)

    # Commit changes and close connection
    conn.commit()
    conn.close()

def load_data_from_csv(file_path, table_name):
    # Read data from csv file
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return

    # Connect to SQLite database
    conn = sqlite3.connect("database/retail.db")
    cursor = conn.cursor()

    # Insert data into the relevant table
    for row in df.itertuples(index=False):
        cursor.execute(f'''
        INSERT INTO {table_name} ({', '.join([f'"{col}"' for col in df.columns])})
        VALUES ({', '.join(['?' for _ in df.columns])})
        ''', row)

    # Commit and close connection
    conn.commit()
    conn.close()
    print(f"Data from {file_path} has been loaded into {table_name}.")

if __name__ == "__main__":
    create_table()

    # Load your Excel/CSV data into the tables
    # Change the file path as necessary, use forward slashes or double backslashes in paths
    load_data_from_csv('dataset/demand_forecasting.csv', 'DemandForecasting')
    load_data_from_csv('dataset/inventory_monitoring.csv', 'InventoryMonitoring')
    load_data_from_csv('dataset/pricing_optimization.csv', 'PricingOptimization')

    print("Database setup complete!")
