import sqlite3
import pandas as pd

# def check_data():
#     conn = sqlite3.connect(r"E:\genai-hackathon\SmartRetail_AI\database\retail.db")
    
#     # Check exact filter conditions
#     test_query = """
#     SELECT COUNT(*) as count 
#     FROM DemandForecasting
#     WHERE "Product ID" = 4277 
#     AND "Store ID" = 48
#     AND "Date" >= '2024-10-04'
#     """
    
#     # Check all available dates
#     date_query = """
#     SELECT MIN("Date") as earliest, MAX("Date") as latest 
#     FROM DemandForecasting
#     WHERE "Product ID" = 4277 
#     AND "Store ID" = 48
#     """
    
#     counts = pd.read_sql(test_query, conn)
#     dates = pd.read_sql(date_query, conn)
    
#     print(f"Records found: {counts['count'][0]}")
#     print(f"Date range: {dates['earliest'][0]} to {dates['latest'][0]}")
    
#     # Show sample records
#     print("\nSample records:")
#     print(pd.read_sql("SELECT * FROM DemandForecasting WHERE \"Product ID\" = 4277 LIMIT 3", conn))

# if __name__ == "__main__":
#     check_data()

with sqlite3.connect(r"E:\genai-hackathon\SmartRetail_AI\database\retail.db") as conn:
    print(pd.read_sql("SELECT * FROM DemandForecasting WHERE \"Product ID\" = 4277 AND \"Store ID\" = 48", conn))