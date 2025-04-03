import sqlite3
import pandas as pd
import os
from datetime import datetime
import logging

class SupplierAgent:
    def __init__(self, db_path, results_dir="results"):
        self.db_path = db_path
        self.results_dir = results_dir
        os.makedirs(self.results_dir, exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
    
    def _table_exists(self, table_name):
        """Check if a table exists in the database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='{table_name}'
            """)
            return cursor.fetchone() is not None

    def _migrate_restock_orders_table(self):
        """Handle table migration with primary key constraint"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if we need to migrate
                cursor.execute("PRAGMA table_info(RestockOrders)")
                columns = [col[1] for col in cursor.fetchall()]
                
                needs_migration = any(col not in columns for col in ['Order Date', 'Status'])
                
                if needs_migration:
                    # Create temporary table with new schema
                    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS RestockOrders_new (
                        "Order ID" INTEGER PRIMARY KEY AUTOINCREMENT,
                        "Product ID" INTEGER,
                        "Store ID" INTEGER,
                        "Order Quantity" INTEGER,
                        "Order Date" TEXT,
                        "Status" TEXT DEFAULT 'Pending'
                    )
                    """)
                    
                    # Copy data from old table (without primary key)
                    cursor.execute("""
                    INSERT INTO RestockOrders_new 
                    ("Product ID", "Store ID", "Order Quantity", "Order Date", "Status")
                    SELECT 
                        "Product ID", 
                        "Store ID", 
                        "Order Quantity",
                        date('now') as "Order Date",
                        'Pending' as "Status"
                    FROM RestockOrders
                    """)
                    
                    # Drop old table and rename new one
                    cursor.execute("DROP TABLE RestockOrders")
                    cursor.execute("ALTER TABLE RestockOrders_new RENAME TO RestockOrders")
                    
                    conn.commit()
                    logging.info("Successfully migrated RestockOrders table")
                
        except Exception as e:
            logging.error(f"Error during migration: {str(e)}")
            # If migration fails, continue with existing table
            return False
        return True

    def create_restock_orders_table(self):
        """Create or migrate RestockOrders table"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create new table if it doesn't exist
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS RestockOrders (
                    "Order ID" INTEGER PRIMARY KEY AUTOINCREMENT,
                    "Product ID" INTEGER,
                    "Store ID" INTEGER,
                    "Order Quantity" INTEGER,
                    "Order Date" TEXT,
                    "Status" TEXT DEFAULT 'Pending'
                )
                """)
                
                # If table exists with old schema, migrate it
                if self._table_exists('RestockOrders'):
                    if not self._migrate_restock_orders_table():
                        # If migration failed, ensure at least the basic columns exist
                        cursor.execute("PRAGMA table_info(RestockOrders)")
                        columns = [col[1] for col in cursor.fetchall()]
                        
                        if 'Order Date' not in columns:
                            cursor.execute("ALTER TABLE RestockOrders ADD COLUMN 'Order Date' TEXT")
                        if 'Status' not in columns:
                            cursor.execute("ALTER TABLE RestockOrders ADD COLUMN 'Status' TEXT DEFAULT 'Pending'")
                        conn.commit()
                        logging.warning("Using limited table schema - no primary key")
                
                conn.commit()
                logging.info("RestockOrders table ready")
                
        except Exception as e:
            logging.error(f"Error preparing RestockOrders table: {str(e)}")
            raise

    def fetch_inventory_data(self):
        """Fetch inventory data that needs restocking"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if not self._table_exists('InventoryMonitoring'):
                    raise ValueError("InventoryMonitoring table does not exist")
                
                query = '''
                SELECT * 
                FROM InventoryMonitoring 
                WHERE "Stock Levels" < "Reorder Point"
                '''
                inventory_data = pd.read_sql(query, conn)
                
                if inventory_data.empty:
                    logging.info("No inventory items below reorder point")
                return inventory_data
                
        except Exception as e:
            logging.error(f"Error fetching inventory data: {str(e)}")
            return pd.DataFrame()

    def fetch_demand_forecasts(self):
        """Fetch demand forecasts"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if not self._table_exists('DemandForecasting'):
                    raise ValueError("DemandForecasting table does not exist")
                
                query = '''
                SELECT "Product ID", "Store ID", "Sales Quantity"
                FROM DemandForecasting
                '''
                forecast_data = pd.read_sql(query, conn)
                
                if forecast_data.empty:
                    logging.warning("No demand forecast data found")
                return forecast_data
                
        except Exception as e:
            logging.error(f"Error fetching demand forecasts: {str(e)}")
            return pd.DataFrame()

    def create_restock_orders(self, inventory_data, demand_forecasts):
        """Generate restock orders with safety stock"""
        orders = []
        
        if inventory_data.empty or demand_forecasts.empty:
            return orders
            
        for _, row in inventory_data.iterrows():
            forecast = demand_forecasts[
                (demand_forecasts['Product ID'] == row['Product ID']) & 
                (demand_forecasts['Store ID'] == row['Store ID'])
            ]
            
            if not forecast.empty:
                forecasted_demand = forecast['Sales Quantity'].values[0]
                safety_stock = row['Reorder Point'] * 0.2
                order_quantity = max(0, (forecasted_demand + safety_stock) - row['Stock Levels'])
                
                if order_quantity > 0:
                    orders.append({
                        'Product ID': row['Product ID'],
                        'Store ID': row['Store ID'],
                        'Order Quantity': int(round(order_quantity)),
                        'Order Date': datetime.now().strftime('%Y-%m-%d'),
                        'Status': 'Pending'
                    })
        
        return orders

    def save_orders_to_csv(self, orders):
        """Save orders to CSV file"""
        if not orders:
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"restock_orders_{timestamp}.csv"
        filepath = os.path.join(self.results_dir, filename)
        
        orders_df = pd.DataFrame(orders)
        orders_df.to_csv(filepath, index=False)
        logging.info(f"Saved restock orders to {filepath}")
        return filepath

    def place_restock_orders(self, orders):
        """Insert orders into database"""
        if not orders:
            logging.info("No orders to place")
            return False
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Get existing columns
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(RestockOrders)")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Prepare data for insertion
                data_to_insert = []
                for order in orders:
                    data_to_insert.append(tuple(
                        order[col] for col in columns 
                        if col in order and col != 'Order ID'
                    ))
                
                # Build and execute insert statement
                cols = [f'"{col}"' for col in columns if col != 'Order ID']
                placeholders = ','.join(['?'] * len(cols))
                query = f"""
                INSERT INTO RestockOrders ({','.join(cols)})
                VALUES ({placeholders})
                """
                
                cursor.executemany(query, data_to_insert)
                conn.commit()
                
                # Save CSV with all data regardless
                self.save_orders_to_csv(orders)
                logging.info(f"Successfully placed {len(orders)} restocking orders")
                return True
                
        except Exception as e:
            logging.error(f"Error placing orders: {str(e)}")
            return False

    def automate_restocking(self):
        """Complete restocking workflow"""
        logging.info("Starting automated restocking process")
        
        try:
            # Prepare table
            self.create_restock_orders_table()
            
            # Get data
            inventory_data = self.fetch_inventory_data()
            demand_forecasts = self.fetch_demand_forecasts()
            
            # Generate orders
            orders = self.create_restock_orders(inventory_data, demand_forecasts)
            
            # Place orders
            if orders:
                success = self.place_restock_orders(orders)
                if success:
                    logging.info("Restocking process completed successfully")
                    return True
            
            logging.info("No restocking required at this time")
            return False
            
        except Exception as e:
            logging.error(f"Restocking process failed: {str(e)}")
            return False

if __name__ == "__main__":
    supplier_agent = SupplierAgent(
        db_path=r"E:\genai-hackathon\SmartRetail_AI\database\retail.db"
    )
    
    supplier_agent.automate_restocking()