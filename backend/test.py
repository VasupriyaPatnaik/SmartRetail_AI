# import sqlite3
# # import pandas as pd

# conn = sqlite3.connect("database/retail.db")
# # query = "SELECT * FROM DemandForecasting"
# # df = pd.read_sql(query, conn)
# # print(df.head())  # Explore your data
# # conn.close()

# # Check the column names of the DemandForecasting table
# cursor = conn.execute("PRAGMA table_info(DemandForecasting);")
# for row in cursor:
#     print(row)

import sqlite3
import pandas as pd

def check_database(db_path):
    with sqlite3.connect(db_path) as conn:
        # Check if table exists
        tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
        print("Tables in database:")
        print(tables)
        
        # Check DemandForecasting data
        try:
            data = pd.read_sql("SELECT * FROM DemandForecasting LIMIT 5", conn)
            print("\nSample DemandForecasting data:")
            print(data)
            print(f"\nTotal records: {len(pd.read_sql('SELECT * FROM DemandForecasting', conn))}")
        except Exception as e:
            print(f"\nError reading DemandForecasting: {str(e)}")

if __name__ == "__main__":
    check_database(r"E:\genai-hackathon\SmartRetail_AI\database\retail.db")