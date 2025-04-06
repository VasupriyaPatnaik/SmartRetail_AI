import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
from retail_ai import RetailOptimizationSystem
import base64
from io import BytesIO
import json

# Configuration
st.set_page_config(layout="wide", page_title="SmartRetail AI Dashboard")

# # Custom CSS to match your Flask templates
# st.markdown("""
# <style>
#     @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
#     body {
#         font-family: 'Inter', sans-serif;
#     }
    
#     .stApp {
#         background-color: #f8f9fa;
#     }
    
#     .stButton>button {
#         background-color: #2c7bb6;
#         color: white;
#         border-radius: 5px;
#         padding: 0.5rem 1rem;
#         border: none;
#     }
    
#     .stButton>button:hover {
#         background-color: #1a5276;
#         color: white;
#     }
    
#     .metric-card {
#         background: white;
#         border-radius: 10px;
#         padding: 1.5rem;
#         box-shadow: 0 4px 6px rgba(0,0,0,0.1);
#     }
# </style>
# """, unsafe_allow_html=True)

# Initialize system
system = RetailOptimizationSystem()

# --- Helper Functions ---
@st.cache_resource
def get_db_connection():
    return sqlite3.connect("retail.db")

def check_database_initialized():
    try:
        conn = get_db_connection()
        tables = pd.read_sql(
            "SELECT name FROM sqlite_master WHERE type='table'", conn
        )
        required_tables = {'users', 'Stores', 'DemandForecasting', 
                          'InventoryMonitoring', 'PricingOptimization', 
                          'InventoryTransfers'}
        if not required_tables.issubset(set(tables['name'])):
            return False
        return True
    except Exception as e:
        st.error(f"Database check error: {str(e)}")
        return False

def get_products():
    try:
        conn = get_db_connection()
        df = pd.read_sql("SELECT DISTINCT product_id FROM DemandForecasting", conn)
        return df['product_id'].unique().tolist()
    except:
        return []

def get_stores():
    try:
        conn = get_db_connection()
        df = pd.read_sql("SELECT store_id, location, region FROM Stores", conn)
        return df.values.tolist()
    except:
        return []

def get_plot_base64(fig):
    """Convert matplotlib figure to base64 for HTML embedding"""
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches='tight')
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def generate_dashboard():
    """Generate dashboard data matching your Flask templates"""
    results = system.run_daily_cycle()
    
    if results['status'] != 'success':
        return None
    
    # Process visualizations
    viz_data = {}
    for viz_type in ['sales_trend', 'inventory_status', 'pricing_comparison']:
        fig = getattr(system.visualizer, f"create_{viz_type}_plot")(pd.DataFrame())
        viz_data[viz_type] = f"data:image/png;base64,{get_plot_base64(fig)}"
    
    return {
        'metrics': results['dashboard']['metrics'],
        'visualizations': viz_data,
        'recommendations': results['dashboard']['recommendations'],
        'forecast_results': results['forecasting'],
        'inventory_results': results['inventory'],
        'pricing_results': results['pricing']
    }

# --- Main App ---
st.title("📊 SmartRetail AI Dashboard")

# --- Sidebar ---
with st.sidebar:
    st.image("https://via.placeholder.com/150x50?text=SmartRetail+AI", width=150)
    st.header("System Controls")
    
    if not check_database_initialized():
        st.warning("Database not initialized")
        if st.button("Initialize Database"):
            with st.spinner("Initializing..."):
                system.db._initialize_database()
                st.success("Database initialized!")
                st.rerun()
    else:
        st.success("Database ready")
    
    st.header("Data Management")
    if st.button("Generate Test Data"):
        with st.spinner("Generating..."):
            result = system.forecaster.generate_test_data()
            st.success(f"Created {result['products']} products across {result['stores']} stores")
            st.rerun()
    
    with st.expander("Add Sales Record"):
        with st.form("sales_form"):
            product_id = st.number_input("Product ID", min_value=1, value=9001)
            store_id = st.selectbox("Store", get_stores(), format_func=lambda x: f"{x[0]} - {x[1]}")
            date = st.date_input("Date")
            quantity = st.number_input("Quantity", min_value=1, value=10)
            
            if st.form_submit_button("Add Record"):
                with get_db_connection() as conn:
                    conn.execute(
                        "INSERT INTO DemandForecasting VALUES (?, ?, ?, ?, NULL, NULL)",
                        (product_id, store_id[0], date.strftime('%Y-%m-%d'), quantity)
                    )
                    conn.commit()
                st.success("Record added!")
                st.rerun()

# --- Main Tabs ---
tab1, tab2, tab3 = st.tabs(["Dashboard", "Optimizations", "Data Explorer"])

with tab1:
    st.header("Retail Performance Overview")
    
    if st.button("Generate Full Report"):
        dashboard_data = generate_dashboard()
        
        if not dashboard_data:
            st.error("Failed to generate dashboard")
        else:
            # Metrics
            cols = st.columns(4)
            metrics = dashboard_data['metrics']
            cols[0].metric("Total Sales", f"${metrics['total_sales']:,.2f}")
            cols[1].metric("Avg Stock", f"{metrics['avg_stock_level']:,.0f}")
            cols[2].metric("Reorder Alerts", metrics['products_below_reorder'])
            cols[3].metric("Price Gap", f"${metrics['price_difference']:,.2f}")
            
            # Visualizations
            st.subheader("Sales Trends")
            st.markdown(f'<img src="{dashboard_data["visualizations"]["sales_trend"]}" width="100%">', 
                       unsafe_allow_html=True)
            
            st.subheader("Inventory Status")
            st.markdown(f'<img src="{dashboard_data["visualizations"]["inventory_status"]}" width="100%">', 
                       unsafe_allow_html=True)
            
            # Recommendations
            if dashboard_data['recommendations']:
                st.subheader("Action Items")
                for rec in dashboard_data['recommendations']:
                    st.warning(f"{rec['priority'].upper()}: {rec['message']}")

with tab2:
    st.header("AI Optimization Engine")
    
    if st.button("Run Full Optimization"):
        with st.spinner("Running optimizations..."):
            dashboard_data = generate_dashboard()
            
            if dashboard_data:
                st.success("Optimization complete!")
                
                with st.expander("Forecasting Results"):
                    st.write(f"Methods used:")
                    for method, count in dashboard_data['forecast_results']['methods_used'].items():
                        st.write(f"- {method.replace('_', ' ').title()}: {count}")
                
                with st.expander("Inventory Results"):
                    st.write(f"Stock updates: {dashboard_data['inventory_results']['updates']}")
                    st.write(f"Emergencies handled: {dashboard_data['inventory_results']['emergencies_handled']}")
                
                with st.expander("Pricing Results"):
                    st.write(f"Price adjustments: {dashboard_data['pricing_results']['updates']}")

with tab3:
    st.header("Data Explorer")
    
    conn = get_db_connection()
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
    selected_table = st.selectbox("Select Table", tables['name'])
    
    if st.button("Load Data"):
        df = pd.read_sql(f"SELECT * FROM {selected_table} LIMIT 1000", conn)
        st.dataframe(df)
        
        if selected_table == "DemandForecasting":
            st.subheader("Sales Trends")
            trend_df = pd.read_sql("""
                SELECT date, SUM(sales_quantity) as total_sales 
                FROM DemandForecasting 
                GROUP BY date 
                ORDER BY date
            """, conn)
            st.line_chart(trend_df.set_index('date'))

# Footer
st.sidebar.markdown("""
---
**SmartRetail AI**  
Version 1.0  
[Contact Support](mailto:support@smartretailai.com)
""")