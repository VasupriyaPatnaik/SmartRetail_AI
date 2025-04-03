import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

class DemandForecastingAgent:
    def __init__(self, db_path, output_dir="results"):
        self.db_path = db_path
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)  # Create directory if doesn't exist
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def _forecast_exists(self, product_id, store_id):
        """Check if forecast already exists for this product/store"""
        existing_files = [f for f in os.listdir(self.output_dir) 
                        if f.startswith(f"product_{product_id}_store_{store_id}")]
        return len(existing_files) > 0
    
    def get_all_products(self):
        """Get all available product/store combinations"""
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql("""
                SELECT DISTINCT "Product ID", "Store ID" 
                FROM DemandForecasting
            """, conn)
    
    def load_product_data(self, product_id, store_id):
        """Load all data for a specific product/store"""
        with sqlite3.connect(self.db_path) as conn:
            data = pd.read_sql(f"""
                SELECT "Date" as ds, "Sales Quantity" as y
                FROM DemandForecasting
                WHERE "Product ID" = {product_id}
                AND "Store ID" = {store_id}
                ORDER BY ds
            """, conn)
            if not data.empty:
                data['ds'] = pd.to_datetime(data['ds'])
            return data
    
    def generate_basic_forecast(self, data, periods=30):
        """Generate simple forecast when data is limited"""
        if len(data) == 1:
            # Constant forecast
            return pd.DataFrame({
                'ds': pd.date_range(
                    start=data['ds'].iloc[0],
                    periods=periods+1,
                    freq='D'
                )[1:],
                'yhat': np.full(periods, data['y'].iloc[0])
            })
        elif len(data) == 2:
            # Linear projection
            x = (data['ds'] - data['ds'].iloc[0]).dt.days.values
            y = data['y'].values
            slope = (y[1] - y[0]) / (x[1] - x[0])
            
            future_dates = pd.date_range(
                start=data['ds'].iloc[-1],
                periods=periods+1,
                freq='D'
            )[1:]
            future_x = (future_dates - data['ds'].iloc[0]).days.values
            
            return pd.DataFrame({
                'ds': future_dates,
                'yhat': y[0] + slope * future_x
            })
        return None
    
    def analyze_data_quality(self):
        """Analyze the database for forecasting potential"""
        with sqlite3.connect(self.db_path) as conn:
            stats = pd.read_sql("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT "Product ID") as unique_products,
                    COUNT(DISTINCT "Store ID") as unique_stores,
                    MIN("Date") as earliest_date,
                    MAX("Date") as latest_date
                FROM DemandForecasting
            """, conn).iloc[0]
            
            distribution = pd.read_sql("""
                SELECT 
                    "Product ID",
                    "Store ID", 
                    COUNT(*) as records,
                    MIN("Date") as first_date,
                    MAX("Date") as last_date
                FROM DemandForecasting
                GROUP BY "Product ID", "Store ID"
                ORDER BY records DESC
            """, conn)
            
            return stats, distribution
    
    def save_forecast(self, forecast, product_id, store_id):
        """Save forecast to CSV in output directory only if it doesn't exist"""
        if self._forecast_exists(product_id, store_id):
            existing_files = [f for f in os.listdir(self.output_dir) 
                            if f.startswith(f"product_{product_id}_store_{store_id}")]
            return os.path.join(self.output_dir, existing_files[0])
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"product_{product_id}_store_{store_id}_{timestamp}.csv"
        filepath = os.path.join(self.output_dir, filename)
        forecast.to_csv(filepath, index=False)
        return filepath
    
    def run_analysis(self):
        """Run complete analysis and attempt forecasting"""
        # 1. Analyze data quality
        stats, distribution = self.analyze_data_quality()
        
        print("\n=== Database Summary ===")
        print(f"Total records: {stats['total_records']}")
        print(f"Unique products: {stats['unique_products']}")
        print(f"Unique stores: {stats['unique_stores']}")
        print(f"Date range: {stats['earliest_date']} to {stats['latest_date']}")
        
        print("\n=== Record Distribution ===")
        print(distribution.describe())
        
        # 2. Try forecasting with best available data
        best_candidate = distribution.iloc[0]
        product_id = best_candidate['Product ID']
        store_id = best_candidate['Store ID']
        record_count = best_candidate['records']
        
        print(f"\nAttempting forecast for Product {product_id} at Store {store_id} ({record_count} records)...")
        
        if self._forecast_exists(product_id, store_id):
            print("\nForecast already exists for this product/store combination")
            existing_file = self.save_forecast(None, product_id, store_id)
            print(f"Existing forecast file: {existing_file}")
            return
        
        data = self.load_product_data(product_id, store_id)
        forecast = self.generate_basic_forecast(data)
        
        if forecast is not None:
            saved_path = self.save_forecast(forecast, product_id, store_id)
            print("\nForecast generated successfully!")
            print(forecast.head())
            print(f"\nResults saved to: {saved_path}")
        else:
            print("\nForecast generation failed. Recommendations:")
            if stats['total_records'] < 10:
                print("- Add more historical data (minimum 10 records recommended)")
            elif distribution['records'].max() < 3:
                print("- Need at least 3 data points per product/store for basic forecasting")
            else:
                print("- Data may need cleaning or different forecasting approach")

if __name__ == "__main__":
    # Initialize with your database path
    agent = DemandForecastingAgent(
        db_path=r"E:\genai-hackathon\SmartRetail_AI\database\retail.db"
    )
    
    # Run the analysis
    agent.run_analysis()