import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta
import logging

class StockOptimizationAgent:
    def __init__(self, db_path, output_dir="results"):
        self.db_path = db_path
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
    def fetch_demand_forecast(self):
        """Fetch forecasted sales data from the database with error handling."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get the most recent forecast for each product/store combination
                query = """
                SELECT 
                    df."Product ID",
                    df."Store ID",
                    df."Date",
                    df."Sales Quantity",
                    df."Price",
                    df."Demand Trend"
                FROM DemandForecasting df
                INNER JOIN (
                    SELECT "Product ID", "Store ID", MAX("Date") as max_date
                    FROM DemandForecasting
                    GROUP BY "Product ID", "Store ID"
                ) latest ON df."Product ID" = latest."Product ID" 
                        AND df."Store ID" = latest."Store ID" 
                        AND df."Date" = latest.max_date
                """
                df = pd.read_sql_query(query, conn)
                
                if df.empty:
                    raise ValueError("No demand forecast data found in database")
                    
                logging.info(f"Successfully loaded {len(df)} demand forecast records")
                return df
                
        except sqlite3.Error as e:
            logging.error(f"Database error: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Error fetching demand forecast: {str(e)}")
            return None

    def optimize_stock_levels(self, demand_forecast, safety_stock_ratio=0.2, lead_time_days=7):
        """
        Calculate optimized stock levels with advanced considerations.
        
        Args:
            demand_forecast: DataFrame with demand predictions
            safety_stock_ratio: Percentage buffer for safety stock
            lead_time_days: Estimated days for restocking
            
        Returns:
            DataFrame with optimized stock levels
        """
        try:
            # Calculate base stock needs
            demand_forecast['DailyDemand'] = demand_forecast['Sales Quantity']
            
            # Adjust for demand trend
            demand_forecast['TrendFactor'] = demand_forecast['Demand Trend'].apply(
                lambda x: 1.2 if x == 'Increasing' else 0.8 if x == 'Decreasing' else 1.0
            )
            
            # Calculate optimized stock
            demand_forecast['OptimizedStock'] = (
                demand_forecast['DailyDemand'] * 
                (1 + safety_stock_ratio) * 
                demand_forecast['TrendFactor'] *
                (1 + lead_time_days/30)  # Account for lead time
            ).round().astype(int)
            
            # Ensure minimum stock level
            demand_forecast['OptimizedStock'] = demand_forecast['OptimizedStock'].clip(lower=1)
            
            return demand_forecast[[
                'Product ID', 'Store ID', 'Date', 
                'DailyDemand', 'OptimizedStock'
            ]]
            
        except Exception as e:
            logging.error(f"Error optimizing stock levels: {str(e)}")
            return None

    def save_optimized_stock(self, optimized_stock):
        """Save optimized stock levels to database and CSV."""
        if optimized_stock is None or optimized_stock.empty:
            logging.error("No optimized stock data to save")
            return False
            
        try:
            # Save to SQLite database
            with sqlite3.connect(self.db_path) as conn:
                optimized_stock.to_sql(
                    'OptimizedStock', 
                    conn, 
                    if_exists='replace', 
                    index=False
                )
            
            # Save to CSV with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_path = os.path.join(self.output_dir, f"optimized_stock_{timestamp}.csv")
            optimized_stock.to_csv(csv_path, index=False)
            
            logging.info(f"Optimized stock saved to database and {csv_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving optimized stock: {str(e)}")
            return False

    def generate_replenishment_orders(self, optimized_stock):
        """Generate suggested replenishment orders based on current inventory."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get current inventory levels
                inventory = pd.read_sql("""
                    SELECT "Product ID", "Store ID", "CurrentStock"
                    FROM CurrentInventory
                """, conn)
                
                if inventory.empty:
                    logging.warning("No current inventory data found")
                    return None
                
                # Merge with optimized stock
                merged = pd.merge(
                    optimized_stock,
                    inventory,
                    on=['Product ID', 'Store ID'],
                    how='left'
                ).fillna(0)
                
                # Calculate order quantities
                merged['OrderQuantity'] = (
                    merged['OptimizedStock'] - merged['CurrentStock']
                ).clip(lower=0)
                
                return merged[
                    merged['OrderQuantity'] > 0
                ][['Product ID', 'Store ID', 'OrderQuantity']]
                
        except Exception as e:
            logging.error(f"Error generating replenishment orders: {str(e)}")
            return None

if __name__ == "__main__":
    # Initialize with your database path
    db_path = r"E:\genai-hackathon\SmartRetail_AI\database\retail.db"
    agent = StockOptimizationAgent(db_path)
    
    # Step 1: Fetch demand forecast
    demand_forecast = agent.fetch_demand_forecast()
    if demand_forecast is None:
        print("Failed to fetch demand forecast data")
        exit()
    
    # Step 2: Optimize stock levels
    optimized_stock = agent.optimize_stock_levels(demand_forecast)
    if optimized_stock is None:
        print("Failed to optimize stock levels")
        exit()
    
    # Step 3: Save results
    if not agent.save_optimized_stock(optimized_stock):
        print("Failed to save optimized stock levels")
        exit()
    
    # Step 4: Generate replenishment orders
    replenishment_orders = agent.generate_replenishment_orders(optimized_stock)
    if replenishment_orders is not None:
        print("\nSuggested Replenishment Orders:")
        print(replenishment_orders)
        
        # Save orders to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        orders_path = os.path.join(agent.output_dir, f"replenishment_orders_{timestamp}.csv")
        replenishment_orders.to_csv(orders_path, index=False)
        print(f"\nOrders saved to {orders_path}")
    
    print("\nStock optimization process completed successfully")