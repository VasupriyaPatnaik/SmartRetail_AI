from flask import Flask, jsonify
import sqlite3
import pandas as pd

app = Flask(__name__)

# Fetch demand forecasting data
@app.route('/forecast', methods=['GET'])
def get_forecast():
    conn = sqlite3.connect("database/retail.db")
    df = pd.read_sql_query("SELECT * FROM DemandForecasting", conn)
    conn.close()
    
    forecast_data = df[['Date', 'Sales Quantity']].rename(columns={"Date": "date", "Sales Quantity": "sales_quantity"}).to_dict(orient="records")
    return jsonify(forecast_data)

if __name__ == '__main__':
    app.run(debug=True)
