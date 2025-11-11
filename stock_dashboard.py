import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io

# Page configuration
st.set_page_config(
    page_title="Stock Market Dashboard",
    page_icon="📈",
    layout="wide"
)

# Title and description
st.title("📊 Interactive Stock Market Statistics Dashboard")
st.markdown("### Real-time Stock Data Analysis and Visualization")

# Sidebar for user inputs
st.sidebar.header("Dashboard Controls")

# Stock symbol input
default_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
stock_symbols = st.sidebar.multiselect(
    "Select Stock Symbols",
    options=["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META", "NFLX", "AMD", "INTC"],
    default=default_symbols[:2]
)

# Date range selection
st.sidebar.subheader("Date Range")
date_range = st.sidebar.selectbox(
    "Select Period",
    ["1 Week", "1 Month", "3 Months", "6 Months", "1 Year", "Custom"]
)

if date_range == "Custom":
    start_date = st.sidebar.date_input("Start Date", datetime.now() - timedelta(days=90))
    end_date = st.sidebar.date_input("End Date", datetime.now())
else:
    end_date = datetime.now()
    if date_range == "1 Week":
        start_date = end_date - timedelta(days=14)  # Extended to ensure we get data
    elif date_range == "1 Month":
        start_date = end_date - timedelta(days=35)
    elif date_range == "3 Months":
        start_date = end_date - timedelta(days=95)
    elif date_range == "6 Months":
        start_date = end_date - timedelta(days=185)
    else:  # 1 Year
        start_date = end_date - timedelta(days=370)

# Chart type selection
chart_type = st.sidebar.selectbox(
    "Chart Type",
    ["Candlestick", "Line Chart", "Area Chart", "OHLC"]
)

# Function to fetch stock data
@st.cache_data(ttl=300)
def get_stock_data(symbol, start, end):
    try:
        stock = yf.Ticker(symbol)
        # Convert dates to string format for yfinance
        start_str = start.strftime('%Y-%m-%d') if hasattr(start, 'strftime') else str(start)
        end_str = end.strftime('%Y-%m-%d') if hasattr(end, 'strftime') else str(end)
        
        data = stock.history(start=start_str, end=end_str)
        
        if data.empty:
            st.warning(f"No data returned for {symbol}. Try a different date range.")
            return None, None
            
        return data, stock.info
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {str(e)}")
        return None, None

# Function to calculate statistics
def calculate_statistics(data):
    """
    Calculate price differences and percentage changes for stock data
    
    Key Calculations:
    1. Price Difference = Current Price - Previous Price
    2. Percentage Change = (Price Difference / Previous Price) × 100
    """
    if data is None or data.empty:
        return None
    
    # Get the most recent closing price (current price)
    current_price = data['Close'].iloc[-1]
    
    # Get the first closing price in the selected period (opening price)
    previous_price = data['Close'].iloc[0]
    
    # CALCULATION 1: Price Difference (in dollars)
    price_change = current_price - previous_price
    
    # CALCULATION 2: Percentage Change
    percentage_change = (price_change / previous_price) * 100
    
    # Additional statistics
    stats = {
        'Current Price': current_price,
        'Opening Price': previous_price,
        'High': data['High'].max(),
        'Low': data['Low'].min(),
        'Price Change': price_change,              # ← Price Difference
        'Percentage Change': percentage_change,    # ← Percentage Change
        'Average Volume': data['Volume'].mean()
    }
    return stats

# Main content
if stock_symbols:
    # Create tabs for each stock
    tabs = st.tabs(stock_symbols)
    
    # Store all data for export
    all_data = {}
    
    for i, symbol in enumerate(stock_symbols):
        with tabs[i]:
            st.subheader(f"{symbol} Stock Analysis")
            
            # Fetch data
            with st.spinner(f"Loading data for {symbol}..."):
                data, info = get_stock_data(symbol, start_date, end_date)
            
            if data is not None and not data.empty:
                all_data[symbol] = data
                
                # Calculate statistics
                stats = calculate_statistics(data)
                
                # Display key metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Current Price",
                        f"${stats['Current Price']:.2f}",
                        f"{stats['Price Change']:.2f} ({stats['Percentage Change']:.2f}%)"
                    )
                
                with col2:
                    st.metric("High", f"${stats['High']:.2f}")
                
                with col3:
                    st.metric("Low", f"${stats['Low']:.2f}")
                
                with col4:
                    st.metric("Avg Volume", f"{stats['Average Volume']:,.0f}")
                
                # Highlight Price Change Calculations
                st.markdown("---")
                st.subheader("📊 Price Change Analysis")
                
                col_calc1, col_calc2, col_calc3 = st.columns(3)
                
                with col_calc1:
                    st.markdown("**Opening Price (Start of Period)**")
                    st.markdown(f"### ${stats['Opening Price']:.2f}")
                
                with col_calc2:
                    change_color = "green" if stats['Price Change'] >= 0 else "red"
                    arrow = "↑" if stats['Price Change'] >= 0 else "↓"
                    st.markdown("**Price Difference**")
                    st.markdown(f"### :{change_color}[{arrow} ${abs(stats['Price Change']):.2f}]")
                    st.caption(f"Formula: Current Price - Opening Price")
                
                with col_calc3:
                    st.markdown("**Percentage Change**")
                    st.markdown(f"### :{change_color}[{arrow} {abs(stats['Percentage Change']):.2f}%]")
                    st.caption(f"Formula: (Price Change / Opening Price) × 100")
                
                st.markdown("---")
                
                # Create chart based on selection
                fig = go.Figure()
                
                if chart_type == "Candlestick":
                    fig.add_trace(go.Candlestick(
                        x=data.index,
                        open=data['Open'],
                        high=data['High'],
                        low=data['Low'],
                        close=data['Close'],
                        name=symbol
                    ))
                elif chart_type == "OHLC":
                    fig.add_trace(go.Ohlc(
                        x=data.index,
                        open=data['Open'],
                        high=data['High'],
                        low=data['Low'],
                        close=data['Close'],
                        name=symbol
                    ))
                elif chart_type == "Line Chart":
                    fig.add_trace(go.Scatter(
                        x=data.index,
                        y=data['Close'],
                        mode='lines',
                        name=symbol,
                        line=dict(width=2)
                    ))
                else:  # Area Chart
                    fig.add_trace(go.Scatter(
                        x=data.index,
                        y=data['Close'],
                        fill='tozeroy',
                        name=symbol,
                        line=dict(width=2)
                    ))
                
                fig.update_layout(
                    title=f"{symbol} Stock Price - {chart_type}",
                    xaxis_title="Date",
                    yaxis_title="Price (USD)",
                    height=500,
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Volume chart
                fig_volume = go.Figure()
                fig_volume.add_trace(go.Bar(
                    x=data.index,
                    y=data['Volume'],
                    name='Volume',
                    marker_color='lightblue'
                ))
                fig_volume.update_layout(
                    title=f"{symbol} Trading Volume",
                    xaxis_title="Date",
                    yaxis_title="Volume",
                    height=300
                )
                st.plotly_chart(fig_volume, use_container_width=True)
                
                # Detailed statistics table
                with st.expander("View Detailed Statistics"):
                    stats_df = pd.DataFrame({
                        'Metric': list(stats.keys()),
                        'Value': [f"${v:.2f}" if isinstance(v, float) and 'Volume' not in k else f"{v:,.2f}" for k, v in stats.items()]
                    })
                    st.table(stats_df)
                
                # Recent data table
                with st.expander("View Recent Data"):
                    st.dataframe(data.tail(10).style.format({
                        'Open': '${:.2f}',
                        'High': '${:.2f}',
                        'Low': '${:.2f}',
                        'Close': '${:.2f}',
                        'Volume': '{:,.0f}'
                    }))
            else:
                st.error(f"No data available for {symbol}")
    
    # Export functionality
    st.sidebar.markdown("---")
    st.sidebar.subheader("Export Data")
    
    if all_data:
        export_format = st.sidebar.selectbox("Export Format", ["CSV", "Excel"])
        
        if st.sidebar.button("📥 Export Data"):
            if export_format == "CSV":
                # Combine all data
                combined_data = pd.DataFrame()
                for symbol, data in all_data.items():
                    data_copy = data.copy()
                    data_copy['Symbol'] = symbol
                    combined_data = pd.concat([combined_data, data_copy])
                
                csv = combined_data.to_csv(index=True)
                st.sidebar.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"stock_data_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                # Create Excel file with multiple sheets
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    for symbol, data in all_data.items():
                        data.to_excel(writer, sheet_name=symbol)
                
                st.sidebar.download_button(
                    label="Download Excel",
                    data=buffer.getvalue(),
                    file_name=f"stock_data_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

else:
    st.warning("⚠️ Please select at least one stock symbol from the sidebar to begin analysis.")

# Footer
st.markdown("---")
st.markdown("""
**Dashboard Features:**
- 📊 Multiple stock comparison
- 📈 Various chart types (Candlestick, Line, Area, OHLC)
- 📉 Price change calculations
- 📥 CSV and Excel export
- 🔄 Real-time data updates
- 📊 Volume analysis

*Data provided by Yahoo Finance*
""")