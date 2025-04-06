import sqlite3
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
import logging
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from typing import Dict, List, Optional, Tuple, Union, Any
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from dataclasses import dataclass
from pydantic import BaseModel, conint, confloat, validate_arguments
import concurrent.futures
from contextlib import contextmanager
import os
from enum import Enum

# Configure logging for Streamlit
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('frontend.log'),
        logging.StreamHandler()
    ]
)
# ====================== Configuration ======================
class RetailConfig(BaseModel):
    min_data_points: conint(ge=3) = 7
    forecast_days: conint(ge=1) = 30
    safety_stock_multiplier: confloat(ge=1.0) = 1.5
    transfer_cost_per_unit: confloat(ge=0) = 0.5
    max_stockout_frequency: conint(ge=1) = 3
    price_adjustment_range: Tuple[confloat(ge=0), confloat(ge=0)] = (0.8, 1.2)
    competitor_price_range: Tuple[confloat(ge=0), confloat(ge=0)] = (0.9, 1.1)

# ====================== Data Models ======================
class StoreLocation(BaseModel):
    store_id: conint(gt=0)
    location: str
    region: str
    warehouse_proximity: confloat(ge=0)

class InventoryTransferRequest(BaseModel):
    product_id: conint(gt=0)
    from_store: conint(gt=0)
    to_store: conint(gt=0)
    quantity: confloat(gt=0)

class ForecastResult(BaseModel):
    product_id: conint(gt=0)
    store_id: conint(gt=0)
    method: str
    forecast_values: List[confloat(ge=0)]
    forecast_dates: List[str]

# ====================== Enums ======================
class ForecastMethod(str, Enum):
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    SIMPLE_AVERAGE = "simple_average_fallback"

class TransferStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

# ====================== Database Manager ======================
class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = logging.getLogger('RetailAI.DatabaseManager')
        self._initialize_database()  # This calls the method we're updating

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _initialize_database(self):
        """Initialize database with all required tables"""
        with self.get_connection() as conn:
            # Add users table to required tables
            required_tables = {
                'users',
                'Stores', 
                'DemandForecasting',
                'InventoryMonitoring',
                'PricingOptimization',
                'InventoryTransfers'
            }
            
            # Check existing tables
            existing_tables = {row['name'] for row in 
                conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
            
            # Create users table if needed
            if 'users' not in existing_tables:
                conn.execute("""
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Only create tables that don't exist
                tables_to_create = required_tables - existing_tables
                
                if not tables_to_create:
                    self.logger.info("All required tables already exist")
                    return
                
                self.logger.info(f"Creating missing tables: {tables_to_create}")
                
                # Create Stores table if needed
                if 'Stores' in tables_to_create:
                    conn.execute("""
                        CREATE TABLE Stores (
                            store_id INTEGER PRIMARY KEY,
                            location TEXT,
                            region TEXT,
                            warehouse_proximity REAL
                        )
                    """)
                
                # Create DemandForecasting table if needed
                if 'DemandForecasting' in tables_to_create:
                    conn.execute("""
                        CREATE TABLE DemandForecasting (
                            product_id INTEGER,
                            store_id INTEGER,
                            date TEXT,
                            sales_quantity REAL,
                            demand_trend TEXT,
                            forecast_method TEXT,
                            PRIMARY KEY (product_id, store_id, date),
                            FOREIGN KEY (store_id) REFERENCES Stores(store_id)
                        )
                    """)
                
                # Create InventoryMonitoring table if needed
                if 'InventoryMonitoring' in tables_to_create:
                    conn.execute("""
                        CREATE TABLE InventoryMonitoring (
                            product_id INTEGER,
                            store_id INTEGER,
                            stock_levels REAL,
                            reorder_point REAL,
                            recommended_stock REAL,
                            supplier_lead_time INTEGER,
                            stockout_frequency INTEGER,
                            last_optimization_date TEXT,
                            PRIMARY KEY (product_id, store_id),
                            FOREIGN KEY (store_id) REFERENCES Stores(store_id)
                        )
                    """)
                
                # Create PricingOptimization table if needed
                if 'PricingOptimization' in tables_to_create:
                    conn.execute("""
                        CREATE TABLE PricingOptimization (
                            product_id INTEGER,
                            store_id INTEGER,
                            price REAL,
                            competitor_prices REAL,
                            elasticity_index REAL,
                            sales_volume REAL,
                            discounts REAL,
                            last_price_change TEXT,
                            price_change_reason TEXT,
                            PRIMARY KEY (product_id, store_id),
                            FOREIGN KEY (store_id) REFERENCES Stores(store_id)
                        )
                    """)
                
                # Create InventoryTransfers table if needed
                if 'InventoryTransfers' in tables_to_create:
                    conn.execute("""
                        CREATE TABLE InventoryTransfers (
                            transfer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            product_id INTEGER,
                            from_store INTEGER,
                            to_store INTEGER,
                            quantity REAL,
                            cost REAL,
                            timestamp TEXT,
                            status TEXT DEFAULT 'pending',
                            FOREIGN KEY (product_id) REFERENCES DemandForecasting(product_id),
                            FOREIGN KEY (from_store) REFERENCES Stores(store_id),
                            FOREIGN KEY (to_store) REFERENCES Stores(store_id)
                        )
                    """)
    
    def reset_database(self):
        """Drop all tables and recreate them (use with caution)"""
        with self.get_connection() as conn:
            # Drop tables in reverse order of dependency
            conn.execute("DROP TABLE IF EXISTS InventoryTransfers")
            conn.execute("DROP TABLE IF EXISTS PricingOptimization")
            conn.execute("DROP TABLE IF EXISTS InventoryMonitoring")
            conn.execute("DROP TABLE IF EXISTS DemandForecasting")
            conn.execute("DROP TABLE IF EXISTS Stores")
            conn.commit()
            self.logger.info("Database initialization completed")

# ====================== Demand Forecasting ======================
class DemandForecaster:
    def __init__(self, db_manager: DatabaseManager, config: RetailConfig):
        self.db = db_manager
        self.config = config
        self.logger = logging.getLogger('RetailAI.Forecaster')

    def check_data_quality(self) -> Dict[str, Any]:
        """Enhanced data quality check with better validation"""
        with self.db.get_connection() as conn:
            try:
                counts = pd.read_sql(f"""
                    SELECT 
                        product_id,
                        store_id, 
                        COUNT(*) as record_count,
                        MIN(date) as first_date,
                        MAX(date) as last_date,
                        JULIANDAY(MAX(date)) - JULIANDAY(MIN(date)) as days_covered,
                        SUM(sales_quantity) as total_sales
                    FROM DemandForecasting
                    WHERE sales_quantity > 0
                    GROUP BY product_id, store_id
                    HAVING COUNT(*) >= {self.config.min_data_points}
                       AND JULIANDAY(MAX(date)) - JULIANDAY(MIN(date)) >= {self.config.min_data_points - 1}
                       AND SUM(sales_quantity) > 0
                    ORDER BY record_count DESC
                """, conn)
                
                data_status = {
                    'total_products': len(counts),
                    'products_with_sufficient_data': len(counts),
                    'avg_records_per_product': float(counts['record_count'].mean()),
                    'avg_days_covered': float(counts['days_covered'].mean()),
                    'status': 'sufficient' if len(counts) > 0 else 'insufficient'
                }
                
                self.logger.info("Data quality check completed", extra=data_status)
                return data_status
            except Exception as e:
                self.logger.error(f"Data quality check failed: {str(e)}")
                return {'status': 'error', 'error': str(e)}

    def _generate_forecast(self, product_id: int, store_id: int, data: pd.DataFrame) -> ForecastResult:
        """Generate forecast for a single product-store combination"""
        try:
            if len(data) < self.config.min_data_points:
                forecast_values = [float(data['sales_quantity'].mean())] * self.config.forecast_days
                method = ForecastMethod.SIMPLE_AVERAGE
            else:
                model = ExponentialSmoothing(
                    data.set_index('date')['sales_quantity'],
                    seasonal='add',
                    seasonal_periods=7
                ).fit()
                forecast_values = model.forecast(self.config.forecast_days).tolist()
                method = ForecastMethod.EXPONENTIAL_SMOOTHING
            
            forecast_dates = pd.date_range(
                start=datetime.now() + timedelta(days=1),
                periods=self.config.forecast_days
            ).strftime('%Y-%m-%d').tolist()
            
            return ForecastResult(
                product_id=product_id,
                store_id=store_id,
                method=method,
                forecast_values=[float(x) for x in forecast_values],
                forecast_dates=forecast_dates
            )
        except Exception as e:
            self.logger.error(f"Forecast failed for product {product_id} at store {store_id}: {str(e)}")
            forecast_values = [float(data['sales_quantity'].mean())] * self.config.forecast_days
            return ForecastResult(
                product_id=product_id,
                store_id=store_id,
                method=ForecastMethod.SIMPLE_AVERAGE,
                forecast_values=forecast_values,
                forecast_dates=pd.date_range(
                    start=datetime.now() + timedelta(days=1),
                    periods=self.config.forecast_days
                ).strftime('%Y-%m-%d').tolist()
            )

    def generate_forecasts(self) -> List[ForecastResult]:
        """Generate forecasts for all products using parallel processing"""
        with self.db.get_connection() as conn:
            products = pd.read_sql(f"""
                SELECT DISTINCT product_id, store_id 
                FROM DemandForecasting
                WHERE sales_quantity IS NOT NULL
                AND sales_quantity > 0
                GROUP BY product_id, store_id
                HAVING COUNT(*) >= {self.config.min_data_points}
            """, conn)
    
        if products.empty:
            self.logger.warning("No products with sufficient data for forecasting")
            return []
    
        forecasts = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_product = {}
        
            for _, row in products.iterrows():
                product_id = int(row['product_id'])
                store_id = int(row['store_id'])
            
                with self.db.get_connection() as conn:
                    data = pd.read_sql(f"""
                        SELECT date, sales_quantity
                        FROM DemandForecasting
                        WHERE product_id={product_id} 
                        AND store_id={store_id}
                        AND sales_quantity > 0
                        ORDER BY date
                    """, conn, parse_dates=['date'])
            
                future = executor.submit(
                    self._generate_forecast, 
                    product_id, 
                    store_id, 
                    data
                )
                future_to_product[future] = (product_id, store_id)
        
            for future in concurrent.futures.as_completed(future_to_product):
                product_id, store_id = future_to_product[future]
                try:
                    forecast = future.result()
                    forecasts.append(forecast)
                
                    # Store the forecast in database
                    with self.db.get_connection() as conn:
                        conn.execute("""
                            INSERT OR REPLACE INTO DemandForecasting
                            (product_id, store_id, date, demand_trend, forecast_method)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            product_id,
                            store_id,
                            datetime.now().strftime('%Y-%m-%d'),
                            forecast.json(),
                            forecast.method.value
                        ))
                        conn.commit()
                
                except Exception as e:
                    self.logger.error(f"Error processing forecast for product {product_id} at store {store_id}: {str(e)}")
    
            self.logger.info(f"Generated {len(forecasts)} forecasts")
            return forecasts

    def generate_test_data(self, days: int = 60, stores: int = 5, products: int = 50):
        """Generate complete test dataset with realistic patterns"""
        # Ensure we have enough days for forecasting
        days = max(days, self.config.min_data_points * 2)
        dates = pd.date_range(end=datetime.today(), periods=days).date
        
        with self.db.get_connection() as conn:
            # Clear existing data first
            conn.execute("DELETE FROM DemandForecasting")
            conn.execute("DELETE FROM InventoryMonitoring")
            conn.execute("DELETE FROM PricingOptimization")
            conn.execute("DELETE FROM Stores")
            
            # Generate store locations
            store_locations = [
                (i, f"Location {i}", f"Region {i%3}", round(np.random.uniform(0.5, 5.0), 1))
                for i in range(1, stores+1)
            ]
            conn.executemany(
                "INSERT INTO Stores VALUES (?, ?, ?, ?)",
                store_locations
            )
            
            # Generate product data with realistic patterns
            for product in range(1, products+1):
                product_id = 9000 + product
                base_price = round(np.random.uniform(5, 50), 2)
                seasonality = np.random.randint(3, 10)
                
                for store in range(1, stores+1):
                    base_qty = np.random.randint(5, 30)
                    
                    # Generate sales data with weekday/weekend patterns
                    sales_data = []
                    for date in dates:
                        # Base quantity + seasonality + random variation
                        qty = base_qty + (seasonality if date.weekday() in [5,6] else 0)
                        qty += np.random.randint(-3, 4)
                        qty = max(1, qty)
                        
                        sales_data.append((
                            product_id,
                            store,
                            date.strftime('%Y-%m-%d'),
                            float(qty),
                            None,
                            None
                        ))
                    
                    # Batch insert sales data
                    conn.executemany(
                        "INSERT INTO DemandForecasting VALUES (?, ?, ?, ?, ?, ?)",
                        sales_data
                    )
                    
                    # Generate initial inventory data
                    conn.execute("""
                        INSERT INTO InventoryMonitoring VALUES (
                            ?, ?, ?, ?, ?, ?, ?, ?
                        )
                    """, (
                        product_id,
                        store,
                        float(np.random.randint(20, 100)),  # Stock Levels
                        float(base_qty * 2),  # Reorder Point
                        float(base_qty * 3),  # Recommended Stock
                        np.random.randint(1, 14),  # Supplier Lead Time
                        0,  # Stockout Frequency
                        None  # Last Optimization Date
                    ))
                    
                    # Generate pricing data with competitor prices
                    conn.execute("""
                        INSERT INTO PricingOptimization VALUES (
                            ?, ?, ?, ?, ?, ?, ?, ?, ?
                        )
                    """, (
                        product_id,
                        store,
                        float(base_price),
                        float(round(base_price * np.random.uniform(*self.config.competitor_price_range), 2)),
                        float(round(np.random.uniform(0.5, 2.0), 2)),
                        float(base_qty),  # Sales Volume
                        0.0,  # Discounts
                        None,  # Last Price Change
                        None  # Price Change Reason
                    ))
            
            conn.commit()
        
        self.logger.info(f"Generated test data for {stores} stores and {products} products")
        return {'status': 'success', 'stores': stores, 'products': products}

# ====================== Inventory Optimization ======================
class InventoryOptimizer:
    def __init__(self, db_manager: DatabaseManager, config: RetailConfig):
        self.db = db_manager
        self.config = config
        self.logger = logging.getLogger('RetailAI.Inventory')

    def _get_transfer_cost(self, from_store: int, to_store: int) -> float:
        """Calculate transfer cost between stores"""
        with self.db.get_connection() as conn:
            distance = conn.execute("""
                SELECT ABS(s1.warehouse_proximity - s2.warehouse_proximity) * 10
                FROM Stores s1, Stores s2
                WHERE s1.store_id = ? AND s2.store_id = ?
            """, (from_store, to_store)).fetchone()[0]
        
        return round(float(distance) * self.config.transfer_cost_per_unit, 2)

    def handle_stockout_emergency(self, product_id: int, store_id: int, needed_quantity: float) -> Dict[str, Any]:
        """Coordinate inventory transfers for stockout situations"""
        with self.db.get_connection() as conn:
            # Find available inventory in other stores
            alternatives = pd.read_sql(f"""
                SELECT 
                    im.store_id, 
                    im.stock_levels,
                    im.stock_levels - im.reorder_point AS available_quantity,
                    s.location
                FROM InventoryMonitoring im
                JOIN Stores s ON im.store_id = s.store_id
                WHERE im.product_id = {product_id}
                AND im.stock_levels > im.reorder_point * 1.2
                AND im.store_id != {store_id}
                ORDER BY 
                    s.warehouse_proximity - (SELECT warehouse_proximity FROM Stores WHERE store_id = {store_id}),
                    im.stock_levels DESC
                LIMIT 5
            """, conn)

            if not alternatives.empty:
                best_option = None
                min_cost = float('inf')
                
                for _, alt in alternatives.iterrows():
                    transfer_qty = min(needed_quantity, float(alt['available_quantity']))
                    cost = self._get_transfer_cost(int(alt['store_id']), store_id) * transfer_qty
                    time = abs(int(alt['store_id']) - store_id) * 0.5  # 0.5 hours per unit distance
                    
                    if cost < min_cost and transfer_qty >= needed_quantity * 0.7:
                        best_option = {
                            'source_store': int(alt['store_id']),
                            'transfer_quantity': float(transfer_qty),
                            'estimated_cost': float(cost),
                            'estimated_time': float(time),
                            'source_location': str(alt['location'])
                        }
                        min_cost = cost
                
                if best_option:
                    # Create transfer record
                    transfer_id = conn.execute("""
                        INSERT INTO InventoryTransfers
                        (product_id, from_store, to_store, quantity, cost, timestamp, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        RETURNING transfer_id
                    """, (
                        product_id,
                        best_option['source_store'],
                        store_id,
                        best_option['transfer_quantity'],
                        best_option['estimated_cost'],
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        TransferStatus.PENDING.value
                    )).fetchone()[0]
                    
                    # Update inventory levels
                    conn.execute(f"""
                        UPDATE InventoryMonitoring
                        SET stock_levels = stock_levels - {best_option['transfer_quantity']}
                        WHERE product_id = {product_id}
                        AND store_id = {best_option['source_store']}
                    """)
                    
                    conn.execute(f"""
                        UPDATE InventoryMonitoring
                        SET stock_levels = stock_levels + {best_option['transfer_quantity']}
                        WHERE product_id = {product_id}
                        AND store_id = {store_id}
                    """)
                    
                    conn.commit()
                    
                    return {
                        'status': 'transfer_available',
                        'transfer_id': transfer_id,
                        **best_option,
                        'message': f"Transfer arranged from Store {best_option['source_store']}"
                    }

            return {
                'status': 'need_urgent_replenishment',
                'product_id': product_id,
                'store_id': store_id,
                'needed_quantity': needed_quantity,
                'message': "No suitable transfer options found"
            }

    def optimize_inventory_levels(self) -> Dict[str, Any]:
        """Run complete inventory optimization"""
        updates = 0
        emergencies_handled = 0
        
        with self.db.get_connection() as conn:
            # Handle critical stockouts
            stockouts = pd.read_sql("""
                SELECT product_id, store_id, 
                       reorder_point - stock_levels AS shortage
                FROM InventoryMonitoring
                WHERE stock_levels < reorder_point * 0.8
                AND stockout_frequency < ?
            """, conn, params=[self.config.max_stockout_frequency])
            
            for _, row in stockouts.iterrows():
                result = self.handle_stockout_emergency(
                    int(row['product_id']),
                    int(row['store_id']),
                    float(row['shortage'])
                )
                if result['status'] == 'transfer_available':
                    emergencies_handled += 1
            
            # Normal inventory optimization
            forecasts = pd.read_sql("""
                SELECT product_id, store_id, demand_trend 
                FROM DemandForecasting 
                WHERE date = (SELECT MAX(date) FROM DemandForecasting)
                AND demand_trend IS NOT NULL
            """, conn)
            
            if not forecasts.empty:
                inventory = pd.read_sql("SELECT * FROM InventoryMonitoring", conn)
                merged = pd.merge(
                    inventory,
                    forecasts,
                    on=['product_id', 'store_id'],
                    how='left'
                )
                
                update_data = []
                for _, row in merged.iterrows():
                    try:
                        forecast = json.loads(row['demand_trend'])
                        weekly_demand = np.mean([float(x) for x in forecast['forecast_values'][:7]])
                        safety_stock = max(self.config.safety_stock_multiplier * weekly_demand, 5)
                        
                        lead_time = float(row['supplier_lead_time'] or 7)
                        lead_time_demand = (lead_time / 7) * weekly_demand
                        reorder_point = round(lead_time_demand + safety_stock)
                        
                        update_data.append((
                            float(reorder_point),
                            float(round(reorder_point * 1.2)),
                            float(reorder_point),
                            datetime.now().strftime('%Y-%m-%d'),
                            int(row['product_id']),
                            int(row['store_id'])
                        ))
                    except Exception as e:
                        self.logger.error(f"Inventory update failed for product {row['product_id']} at store {row['store_id']}: {str(e)}")
                
                # Batch update inventory
                conn.executemany("""
                    UPDATE InventoryMonitoring 
                    SET reorder_point = ?,
                        recommended_stock = ?,
                        stockout_frequency = CASE 
                            WHEN stock_levels < ? THEN 1 
                            ELSE 0 
                        END,
                        last_optimization_date = ?
                    WHERE product_id = ? AND store_id = ?
                """, update_data)
                updates = len(update_data)
                conn.commit()
        
        self.logger.info(
            "Inventory optimization completed",
            extra={'updates': updates, 'emergencies_handled': emergencies_handled}
        )
        return {
            'status': 'success',
            'updates': updates,
            'emergencies_handled': emergencies_handled
        }

# ====================== Pricing Optimization ======================
class PricingOptimizer:
    def __init__(self, db_manager: DatabaseManager, config: RetailConfig):
        self.db = db_manager
        self.config = config
        self.logger = logging.getLogger('RetailAI.Pricing')

    def optimize_prices(self) -> Dict[str, Any]:
        """Adjust prices based on demand forecasts and competition"""
        updates = 0
        
        with self.db.get_connection() as conn:
            forecasts = pd.read_sql("""
                SELECT product_id, store_id, demand_trend, forecast_method
                FROM DemandForecasting 
                WHERE date = (SELECT MAX(date) FROM DemandForecasting)
                AND demand_trend IS NOT NULL
            """, conn)
            
            if not forecasts.empty:
                pricing = pd.read_sql("SELECT * FROM PricingOptimization", conn)
                merged = pd.merge(
                    pricing,
                    forecasts,
                    on=['product_id', 'store_id'],
                    how='left'
                )
                
                update_data = []
                for _, row in merged.iterrows():
                    try:
                        forecast = json.loads(row['demand_trend'])
                        forecast_avg = np.mean([float(x) for x in forecast['forecast_values']])
                        current_volume = float(row['sales_volume'] or forecast_avg)
                        
                        if current_volume <= 0:
                            continue
                            
                        demand_change = (forecast_avg - current_volume) / current_volume
                        elasticity = float(row['elasticity_index'] or 1.0)
                        new_price = float(row['price']) * (1 + (demand_change * elasticity))
                        
                        # Apply price constraints
                        min_price = float(row['price']) * self.config.price_adjustment_range[0]
                        if pd.notna(row['competitor_prices']):
                            min_price = max(min_price, float(row['competitor_prices']) * 0.9)
                        
                        max_price = float(row['price']) * self.config.price_adjustment_range[1]
                        if pd.notna(row['competitor_prices']):
                            max_price = min(max_price, float(row['competitor_prices']) * 1.1)
                        
                        new_price = np.clip(new_price, min_price, max_price)
                        discount = max(float(row['price']) - new_price, 0)
                        
                        update_data.append((
                            float(new_price),
                            float(discount),
                            datetime.now().strftime('%Y-%m-%d'),
                            f"Optimized based on {row['forecast_method']} forecast",
                            int(row['product_id']),
                            int(row['store_id'])
                        ))
                    except Exception as e:
                        self.logger.error(f"Pricing update failed for product {row['product_id']} at store {row['store_id']}: {str(e)}")
                
                # Batch update pricing
                conn.executemany("""
                    UPDATE PricingOptimization 
                    SET price = ?,
                        discounts = ?,
                        last_price_change = ?,
                        price_change_reason = ?
                    WHERE product_id = ? AND store_id = ?
                """, update_data)
                updates = len(update_data)
                conn.commit()
        
        self.logger.info("Pricing optimization completed", extra={'updates': updates})
        return {'status': 'success', 'updates': updates}

# ====================== Visualization ======================
class RetailVisualizer:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self.logger = logging.getLogger('RetailAI.Visualizer')
        os.makedirs('visualizations', exist_ok=True)

    def save_visualization(self, plt_figure, filename: str) -> str:
        """Save visualization to file and return path"""
        path = f"visualizations/{filename}.png"
        plt_figure.savefig(path, format='png', bbox_inches='tight', dpi=100)
        plt.close(plt_figure)
        self.logger.info(f"Saved visualization to {path}")
        return path

    def create_sales_trend_plot(self, data: pd.DataFrame) -> str:
        """Generate sales trend visualization"""
        fig, ax = plt.subplots(figsize=(12, 6))
        if not data.empty and 'date' in data.columns and 'sales_quantity' in data.columns:
            try:
                # Convert date and ensure proper sorting
                data['date'] = pd.to_datetime(data['date'])
                data = data.sort_values('date')
                
                # Group by date and sum sales
                sales_trend = data.groupby('date')['sales_quantity'].sum()
                
                # Plot with improved styling
                sales_trend.plot(
                    title='7-Day Sales Trend', 
                    marker='o',
                    linestyle='-',
                    color='#2c7bb6',
                    ax=ax
                )
                ax.set_ylabel('Total Sales Quantity', fontsize=12)
                ax.set_xlabel('Date', fontsize=12)
                ax.grid(True, linestyle='--', alpha=0.7)
                plt.xticks(rotation=45)
            except Exception as e:
                self.logger.error(f"Error creating sales trend plot: {str(e)}")
                ax.text(0.5, 0.5, 'Error showing sales trend', 
                        ha='center', va='center', fontsize=12)
                ax.set_title('Sales Trend Error')
        else:
            ax.text(0.5, 0.5, 'No sales data available', 
                    ha='center', va='center', fontsize=12)
            ax.set_title('Sales Trend (No Data)')
        return self.save_visualization(fig, "sales_trend")

    def create_inventory_status_plot(self, data: pd.DataFrame) -> str:
        """Generate inventory status visualization"""
        fig, ax = plt.subplots(figsize=(12, 6))
        if data.empty or 'store_id' not in data.columns:
            ax.text(0.5, 0.5, 'No inventory data available', 
                    ha='center', va='center', fontsize=12)
            ax.set_title('Inventory Status (No Data)')
        else:
            try:
                # Ensure numeric data types
                data['stock_levels'] = pd.to_numeric(data['stock_levels'], errors='coerce')
                data['reorder_point'] = pd.to_numeric(data['reorder_point'], errors='coerce')
                
                inventory_data = data.groupby('store_id').agg({
                    'stock_levels': 'mean',
                    'reorder_point': 'mean'
                }).reset_index()
                
                if not inventory_data.empty:
                    # Plot with improved styling
                    inventory_data.plot(
                        x='store_id', 
                        y=['stock_levels', 'reorder_point'],
                        kind='bar', 
                        title='Average Stock Levels vs Reorder Points by Store',
                        color=['#2c7bb6', '#d7191c'],
                        ax=ax
                    )
                    ax.set_ylabel('Quantity', fontsize=12)
                    ax.set_xlabel('Store ID', fontsize=12)
                    ax.legend(['Stock Levels', 'Reorder Point'])
                    ax.grid(True, linestyle='--', alpha=0.7)
                else:
                    ax.text(0.5, 0.5, 'No inventory data available', 
                            ha='center', va='center', fontsize=12)
                    ax.set_title('Inventory Status (No Data)')
            except Exception as e:
                self.logger.error(f"Error creating inventory plot: {str(e)}")
                ax.text(0.5, 0.5, 'Error showing inventory status', 
                        ha='center', va='center', fontsize=12)
                ax.set_title('Inventory Status Error')
        return self.save_visualization(fig, "inventory_status")

    def create_pricing_comparison_plot(self, data: pd.DataFrame) -> str:
        """Generate pricing comparison visualization"""
        fig, ax = plt.subplots(figsize=(12, 6))
        if data.empty or 'product_id' not in data.columns:
            ax.text(0.5, 0.5, 'No pricing data available', 
                    ha='center', va='center', fontsize=12)
            ax.set_title('Pricing Comparison (No Data)')
            ax.axis('off')
        else:
            try:
                # Ensure numeric data types
                data['price'] = pd.to_numeric(data['price'], errors='coerce')
                data['competitor_prices'] = pd.to_numeric(data['competitor_prices'], errors='coerce')
                
                # Get top 20 products by sales volume
                pricing_data = data.groupby('product_id').agg({
                    'price': 'mean',
                    'competitor_prices': 'mean'
                }).reset_index().head(20)
                
                if not pricing_data.empty:
                    # Plot with improved styling
                    pricing_data.plot(
                        x='product_id', 
                        y=['price', 'competitor_prices'],
                        kind='bar', 
                        title='Our Price vs Competitor Prices (Top 20 Products)',
                        color=['#2c7bb6', '#fdae61'],
                        ax=ax
                    )
                    ax.set_ylabel('Price ($)', fontsize=12)
                    ax.set_xlabel('Product ID', fontsize=12)
                    ax.legend(['Our Price', 'Competitor Price'])
                    ax.grid(True, linestyle='--', alpha=0.7)
                    plt.xticks(rotation=45)
                else:
                    ax.text(0.5, 0.5, 'No pricing data available', 
                            ha='center', va='center', fontsize=12)
                    ax.set_title('Pricing Comparison (No Data)')
                    ax.axis('off')
            except Exception as e:
                self.logger.error(f"Failed to create pricing plot: {str(e)}")
                ax.text(0.5, 0.5, 'Error generating pricing comparison', 
                        ha='center', va='center', fontsize=12)
                ax.set_title('Pricing Comparison Error')
                ax.axis('off')
        return self.save_visualization(fig, "pricing_comparison")

    def generate_dashboard(self) -> Dict[str, Any]:
        """Create comprehensive dashboard with robust error handling"""
        try:
            with self.db.get_connection() as conn:
                data = pd.read_sql("""
                    SELECT df.product_id, df.store_id, df.date,
                           df.sales_quantity, df.demand_trend,
                           im.stock_levels, im.reorder_point,
                           po.price, po.competitor_prices
                    FROM DemandForecasting df
                    JOIN InventoryMonitoring im ON df.product_id = im.product_id 
                                            AND df.store_id = im.store_id
                    JOIN PricingOptimization po ON df.product_id = po.product_id 
                                            AND df.store_id = po.store_id
                    WHERE df.date >= date('now', '-7 days')
                """, conn)
            
            # Convert data types with error handling
            try:
                data['date'] = pd.to_datetime(data['date'])
                numeric_cols = ['sales_quantity', 'stock_levels', 'reorder_point', 'price', 'competitor_prices']
                for col in numeric_cols:
                    if col in data.columns:
                        data[col] = pd.to_numeric(data[col], errors='coerce')
            except Exception as e:
                self.logger.error(f"Data conversion error: {str(e)}")
            
            # Calculate metrics with NaN handling
            metrics = {
                'total_sales': float(data['sales_quantity'].sum()) if 'sales_quantity' in data.columns and not data['sales_quantity'].isnull().all() else 0.0,
                'avg_stock_level': float(data['stock_levels'].mean()) if 'stock_levels' in data.columns and not data['stock_levels'].isnull().all() else 0.0,
                'products_below_reorder': int((data['stock_levels'] < data['reorder_point']).sum() 
                                   if all(col in data.columns and not data[col].isnull().all() 
                                         for col in ['stock_levels', 'reorder_point']) 
                                   else 0),
                'price_difference': float((data['price'] - data['competitor_prices']).mean()) 
                               if all(col in data.columns and not data[col].isnull().all() 
                                     for col in ['price', 'competitor_prices']) 
                               else 0.0
            }

            dashboard = {
                'visualizations': {
                    'sales_trend': self.create_sales_trend_plot(data),
                    'inventory_status': self.create_inventory_status_plot(data),
                    'pricing_comparison': self.create_pricing_comparison_plot(data)
                },
                'metrics': metrics,
                'recommendations': []
            }
            
            # Generate recommendations with error checking
            if all(col in data.columns for col in ['stock_levels', 'reorder_point']):
                low_stock = data[data['stock_levels'] < data['reorder_point']]
                if not low_stock.empty:
                    dashboard['recommendations'].append({
                        'type': 'inventory',
                        'priority': 'high',
                        'message': f"{len(low_stock)} products below reorder point need attention"
                    })
            
            if all(col in data.columns for col in ['price', 'competitor_prices']):
                price_gap = data[data['price'] > data['competitor_prices'] * 1.1]
                if not price_gap.empty:
                    dashboard['recommendations'].append({
                        'type': 'pricing',
                        'priority': 'medium',
                        'message': f"{len(price_gap)} products priced >10% above competitors"
                    })
            
            self.logger.info("Dashboard generated successfully")
            return dashboard
            
        except Exception as e:
            self.logger.error(f"Dashboard generation failed: {str(e)}")
            return {
                'error': str(e),
                'visualizations': {
                    'error': 'Failed to generate visualizations'
                },
                'metrics': {},
                'recommendations': []
            }

# ====================== Main System ======================
class RetailOptimizationSystem:
    def __init__(self, db_path: str = "retail.db", config: Optional[RetailConfig] = None):
        self.db = DatabaseManager(db_path)
        self.config = config or RetailConfig()
        
        # Initialize components
        self.forecaster = DemandForecaster(self.db, self.config)
        self.inventory = InventoryOptimizer(self.db, self.config)
        self.pricing = PricingOptimizer(self.db, self.config)
        self.visualizer = RetailVisualizer(self.db)
        
        self.logger = logging.getLogger('RetailAI.System')
        self.logger.info("Retail Optimization System initialized")

    def run_daily_cycle(self) -> Dict[str, Any]:
        """Execute complete optimization cycle"""
        results = {
            'forecasting': {},
            'inventory': {},
            'pricing': {},
            'dashboard': {},
            'status': 'success',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            # Check data quality and generate test data if needed
            data_status = self.forecaster.check_data_quality()
            if data_status.get('status') in ['empty', 'insufficient']:
                self.logger.warning("Insufficient data - generating test data")
                self.forecaster.generate_test_data()
                data_status = self.forecaster.check_data_quality()  # Re-check after generation
            
            # Run forecasting
            forecasts = self.forecaster.generate_forecasts()
            results['forecasting'] = {
                'forecasts_generated': len(forecasts),
                'methods_used': {}
            }
            
            # Initialize all possible methods
            for method in ForecastMethod:
                results['forecasting']['methods_used'][method.value] = 0
                
            # Count actual methods used
            for f in forecasts:
                results['forecasting']['methods_used'][f.method] += 1
            
            # Run inventory optimization
            inventory_results = self.inventory.optimize_inventory_levels()
            results['inventory'] = inventory_results
            
            # Run pricing optimization
            pricing_results = self.pricing.optimize_prices()
            results['pricing'] = pricing_results
            
            # Generate dashboard
            results['dashboard'] = self.visualizer.generate_dashboard()
            
        except Exception as e:
            self.logger.error(f"System error: {str(e)}", exc_info=True)
            results['status'] = 'failed'
            results['error'] = str(e)
        
        self.logger.info("Daily cycle completed", extra={'results': results})
        return results

# ====================== Main Execution ======================
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('retail_ai.log'),
            logging.StreamHandler()
        ]
    )
    
    # Initialize and run the system
    system = RetailOptimizationSystem()
    
    # Run the optimization cycle
    results = system.run_daily_cycle()
    
    # Print formatted results
    print("\n" + "="*40)
    print("=== RETAIL OPTIMIZATION RESULTS ===".center(40))
    print("="*40)
    
    print(f"\nStatus: {results['status']}")
    print(f"Timestamp: {results['timestamp']}")
    
    if results['status'] == 'success':
        # Forecasting section
        print("\n" + "-"*40)
        print("FORECASTING".center(40))
        print("-"*40)
        print(f"Total Forecasts: {results['forecasting']['forecasts_generated']}")
        print("Methods Used:")
        for method, count in sorted(results['forecasting']['methods_used'].items()):
            print(f"  • {method.replace('_', ' ').title()}: {count}")
        
        # Inventory section
        print("\n" + "-"*40)
        print("INVENTORY".center(40))
        print("-"*40)
        print(f"Stock Updates: {results['inventory']['updates']}")
        print(f"Emergencies Handled: {results['inventory']['emergencies_handled']}")
        
        # Pricing section
        print("\n" + "-"*40)
        print("PRICING".center(40))
        print("-"*40)
        print(f"Price Adjustments: {results['pricing']['updates']}")
        
        # Dashboard section
        print("\n" + "-"*40)
        print("DASHBOARD".center(40))
        print("-"*40)
        metrics = results['dashboard']['metrics']
        print(f"Total Sales: ${metrics['total_sales']:,.2f}")
        print(f"Avg Stock Level: {metrics['avg_stock_level']:,.1f} units")
        print(f"Products Needing Attention: {metrics['products_below_reorder']}")
        print(f"Avg Price Difference: ${metrics['price_difference']:,.2f}")
        
        # Recommendations
        print("\n" + "-"*40)
        print("RECOMMENDATIONS".center(40))
        print("-"*40)
        if results['dashboard']['recommendations']:
            for rec in results['dashboard']['recommendations']:
                print(f"[{rec['priority'].upper()}] {rec['message']}")
        else:
            print("No critical recommendations at this time")
        
        # Visualization confirmation
        print("\nVisualizations saved to 'visualizations/' directory:")
        print("  • sales_trend.png")
        print("  • inventory_status.png")
        print("  • pricing_comparison.png")
        
        # Save full results
        with open('optimization_results.json', 'w') as f:
            json.dump(results, f, indent=2)
            print("\nComplete results saved to 'optimization_results.json'")
    else:
        print("\nError occurred:")
        print(f"  • {results.get('error', 'Unknown error')}")