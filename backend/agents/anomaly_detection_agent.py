import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import os

class AnomalyDetectionAgent:
    def __init__(self, db_path=r"E:\genai-hackathon\SmartRetail_AI\database\retail.db", 
                 output_dir="results"):
        self.db_path = db_path
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self._verify_tables()

    def _verify_tables(self):
        """Verify required tables and columns exist"""
        required_tables = {
            "DemandForecasting": ["Product ID", "Store ID", "Date", "Sales Quantity"],
            "InventoryMonitoring": ["Product ID", "Store ID", "Stock Levels", "Reorder Point"]
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for table, columns in required_tables.items():
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                    if not cursor.fetchone():
                        raise ValueError(f"Table {table} does not exist in database")
                    
                    cursor.execute(f"PRAGMA table_info({table})")
                    existing_columns = [col[1] for col in cursor.fetchall()]
                    missing = set(columns) - set(existing_columns)
                    if missing:
                        raise ValueError(f"Table {table} missing columns: {missing}")
        except Exception as e:
            logging.error(f"Database verification failed: {str(e)}")
            raise

    def fetch_combined_data(self, lookback_days=30):
        """Fetch combined inventory and sales data with safe calculations"""
        query = """
        SELECT 
            i."Product ID",
            i."Store ID", 
            i."Stock Levels",
            i."Reorder Point",
            COALESCE(SUM(d."Sales Quantity"), 0) as total_sales,
            COUNT(d."Date") as sales_days
        FROM InventoryMonitoring i
        LEFT JOIN DemandForecasting d ON 
            i."Product ID" = d."Product ID" AND 
            i."Store ID" = d."Store ID" AND
            d."Date" >= ?
        GROUP BY i."Product ID", i."Store ID", i."Stock Levels", i."Reorder Point"
        """
        cutoff_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y-%m-%d')
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql(query, conn, params=(cutoff_date,))
                
            if not df.empty:
                # Safe calculation of daily sales and days of stock
                df["daily_sales"] = df.apply(
                    lambda x: x["total_sales"] / x["sales_days"] if x["sales_days"] > 0 else 0,
                    axis=1
                )
                df["days_of_stock"] = df.apply(
                    lambda x: x["Stock Levels"] / x["daily_sales"] if x["daily_sales"] > 0 else np.inf,
                    axis=1
                )
                # Replace infinite values with a large number for display
                df["days_of_stock"] = df["days_of_stock"].replace(np.inf, 999)
            return df
            
        except Exception as e:
            logging.error(f"Error fetching combined data: {str(e)}")
            return pd.DataFrame()

    def detect_anomalies(self):
        """Detect inventory and sales anomalies with safe calculations"""
        data = self.fetch_combined_data()
        if data.empty:
            logging.warning("No data available for anomaly detection")
            return data
            
        try:
            # Calculate sales quartiles safely
            valid_sales = data[data["daily_sales"] > 0]["daily_sales"]
            sales_q1 = valid_sales.quantile(0.25) if not valid_sales.empty else 0
            sales_q3 = valid_sales.quantile(0.75) if not valid_sales.empty else 0
            
            # Detect anomalies
            data['stockout_risk'] = data['Stock Levels'] < data['Reorder Point']
            data['excess_stock'] = data['Stock Levels'] > (3 * data['Reorder Point'])
            data['low_sales'] = (data['daily_sales'] < sales_q1) & (data['Stock Levels'] > 0)
            data['high_sales'] = (data['daily_sales'] > sales_q3) & (data['Stock Levels'] < data['Reorder Point'])
            data['no_recent_sales'] = (data['sales_days'] == 0) & (data['Stock Levels'] > 0)
            
            return data[['Product ID', 'Store ID', 'Stock Levels', 'Reorder Point',
                        'daily_sales', 'days_of_stock', 'stockout_risk', 'excess_stock',
                        'low_sales', 'high_sales', 'no_recent_sales']]
            
        except Exception as e:
            logging.error(f"Error detecting anomalies: {str(e)}")
            return pd.DataFrame()

    def generate_alerts(self, anomalies):
        """Generate actionable alerts with safe numeric handling"""
        alerts = []
        if anomalies.empty:
            return alerts
            
        try:
            # Calculate sales threshold safely
            valid_sales = anomalies[anomalies["daily_sales"] > 0]["daily_sales"]
            sales_q3 = valid_sales.quantile(0.75) if not valid_sales.empty else 0
            
            for _, row in anomalies.iterrows():
                # Safely handle days_of_stock
                days_remaining = int(row['days_of_stock']) if not pd.isna(row['days_of_stock']) and row['days_of_stock'] != np.inf else 999
                
                if row['stockout_risk']:
                    alerts.append({
                        'product_id': row['Product ID'],
                        'store_id': row['Store ID'],
                        'type': 'STOCKOUT_RISK',
                        'message': (f"Stock level {row['Stock Levels']} below reorder point {row['Reorder Point']}. "
                                   f"Estimated days remaining: {days_remaining}"),
                        'severity': 'CRITICAL' if days_remaining < 3 else 'HIGH',
                        'metric': row['Stock Levels'],
                        'threshold': row['Reorder Point']
                    })
                    
                if row['excess_stock']:
                    excess_amount = row['Stock Levels'] - (3 * row['Reorder Point'])
                    alerts.append({
                        'product_id': row['Product ID'],
                        'store_id': row['Store ID'],
                        'type': 'EXCESS_STOCK',
                        'message': f"Excess stock of {excess_amount} units (Current: {row['Stock Levels']}, Threshold: {3 * row['Reorder Point']})",
                        'severity': 'MEDIUM',
                        'metric': row['Stock Levels'],
                        'threshold': 3 * row['Reorder Point']
                    })
                    
                if row['high_sales']:
                    alerts.append({
                        'product_id': row['Product ID'],
                        'store_id': row['Store ID'],
                        'type': 'HIGH_DEMAND',
                        'message': (f"Unusually high sales ({row['daily_sales']:.1f}/day) with low stock. "
                                   f"Reorder immediately to prevent stockout."),
                        'severity': 'HIGH',
                        'metric': row['daily_sales'],
                        'threshold': sales_q3
                    })
                    
                if row['no_recent_sales']:
                    alerts.append({
                        'product_id': row['Product ID'],
                        'store_id': row['Store ID'],
                        'type': 'NO_RECENT_SALES',
                        'message': f"No sales in last 30 days despite having {row['Stock Levels']} units in stock",
                        'severity': 'LOW',
                        'metric': 0,
                        'threshold': 0
                    })
            
            # Sort alerts by severity
            severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
            alerts.sort(key=lambda x: severity_order[x['severity']])
            
        except Exception as e:
            logging.error(f"Error generating alerts: {str(e)}")
        
        return alerts

    def save_alerts(self, alerts):
        """Save alerts to CSV file with error handling"""
        if not alerts:
            return None
            
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"anomaly_alerts_{timestamp}.csv"
            filepath = os.path.join(self.output_dir, filename)
            
            alerts_df = pd.DataFrame(alerts)
            alerts_df.to_csv(filepath, index=False)
            logging.info(f"Saved alerts to {filepath}")
            return filepath
            
        except Exception as e:
            logging.error(f"Error saving alerts: {str(e)}")
            return None

    def run(self):
        """Complete anomaly detection pipeline with robust error handling"""
        logging.info("Starting anomaly detection")
        
        try:
            anomalies = self.detect_anomalies()
            alerts = self.generate_alerts(anomalies)
            
            if alerts:
                saved_path = self.save_alerts(alerts)
                
                print(f"\n=== Anomaly Detection Report ===")
                print(f"Total anomalies detected: {len(alerts)}")
                print(f"Critical/HIGH: {len([a for a in alerts if a['severity'] in ['CRITICAL', 'HIGH']])}")
                print(f"Results saved to: {saved_path}")
                
                print("\nTop 5 alerts:")
                for alert in alerts[:5]:
                    print(f"[{alert['severity']}] {alert['type']} - {alert['message']}")
                
                return alerts
            else:
                logging.info("No anomalies detected")
                return []
                
        except Exception as e:
            logging.error(f"Anomaly detection failed: {str(e)}")
            return []

if __name__ == "__main__":
    agent = AnomalyDetectionAgent()
    agent.run()