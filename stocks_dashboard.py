import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import ta

##########################################################################################
## PART 1: Define Functions ##
##########################################################################################

def fetch_stock_data(ticker, period, interval):
    data = yf.download(ticker, period=period, interval=interval)
    
    # แก้ไข Error: ยุบหัวคอลัมน์จาก MultiIndex ให้เป็นชั้นเดียว (Single Level)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    return data

def process_data(data):
    if data.empty:
        return data
    if data.index.tzinfo is None:
        data.index = data.index.tz_localize('UTC')
    data.index = data.index.tz_convert('US/Eastern')
    data.reset_index(inplace=True)
    # ปรับชื่อคอลัมน์วันที่ให้เป็นมาตรฐาน
    if 'Date' in data.columns:
        data.rename(columns={'Date': 'Datetime'}, inplace=True)
    return data

def calculate_metrics(data):
    # มั่นใจว่าเป็นค่าตัวเลขเดี่ยวๆ (Scalar) ด้วย float()
    last_close = float(data['Close'].iloc[-1])
    prev_close = float(data['Close'].iloc[0])
    change = last_close - prev_close
    pct_change = (change / prev_close) * 100
    high = float(data['High'].max())
    low = float(data['Low'].min())
    volume = int(data['Volume'].sum())
    return last_close, change, pct_change, high, low, volume

def add_technical_indicators(data):
    # Library 'ta' ต้องการข้อมูลแบบ Series (1 มิติ) 
    # การจัดการ MultiIndex ใน fetch_stock_data จะช่วยแก้ Error ตรงนี้
    data['SMA_20'] = ta.trend.sma_indicator(data['Close'], window=20)
    data['EMA_20'] = ta.trend.ema_indicator(data['Close'], window=20)
    return data

###############################################
## PART 2: App Layout ##
###############################################

st.set_page_config(layout="wide")
st.title('Real Time Stock Dashboard')

# 2A: SIDEBAR PARAMETERS
st.sidebar.header('Chart Parameters')
ticker = st.sidebar.text_input('Ticker', 'ADBE').upper()
time_period = st.sidebar.selectbox('Time Period', ['1d', '1wk', '1mo', '1y', 'max'])
chart_type = st.sidebar.selectbox('Chart Type', ['Candlestick', 'Line'])
indicators = st.sidebar.multiselect('Technical Indicators', ['SMA 20', 'EMA 20'])

interval_mapping = {
    '1d': '1m', '1wk': '30m', '1mo': '1d', '1y': '1wk', 'max': '1wk'
}

# 2B: MAIN CONTENT AREA (รันทันที ไม่ต้องกดปุ่ม Update)
data = fetch_stock_data(ticker, time_period, interval_mapping[time_period])

if not data.empty:
    data = process_data(data)
    data = add_technical_indicators(data)
    last_close, change, pct_change, high, low, volume = calculate_metrics(data)
    
    # แสดงผล Metric หลัก
    st.metric(label=f"{ticker} Last Price", value=f"{last_close:.2f} USD", delta=f"{change:.2f} ({pct_change:.2f}%)")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("High", f"{high:.2f} USD")
    col2.metric("Low", f"{low:.2f} USD")
    col3.metric("Volume", f"{volume:,}")
    
    # วาดกราฟ
    fig = go.Figure()
    if chart_type == 'Candlestick':
        fig.add_trace(go.Candlestick(x=data['Datetime'],
                                     open=data['Open'], high=data['High'],
                                     low=data['Low'], close=data['Close'], name='Market Data'))
    else:
        fig.add_trace(go.Scatter(x=data['Datetime'], y=data['Close'], mode='lines', name='Close Price'))
    
    # เพิ่ม Indicators
    for indicator in indicators:
        if indicator == 'SMA 20':
            fig.add_trace(go.Scatter(x=data['Datetime'], y=data['SMA_20'], name='SMA 20', line=dict(color='orange')))
        elif indicator == 'EMA 20':
            fig.add_trace(go.Scatter(x=data['Datetime'], y=data['EMA_20'], name='EMA 20', line=dict(color='blue')))
    
    fig.update_layout(title=f'{ticker} {time_period.upper()} Chart', height=600, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # ตารางข้อมูล
    with st.expander("Show Raw Data"):
        st.subheader('Historical Data')
        st.dataframe(data[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']])
else:
    st.error("ไม่สามารถดึงข้อมูลได้ โปรดตรวจสอบชื่อ Ticker อีกครั้ง")

# 2C: SIDEBAR PRICES
st.sidebar.header('Real-Time Stock Prices')
stock_symbols = ['AAPL', 'GOOGL', 'AMZN', 'MSFT']
for symbol in stock_symbols:
    rt_data = fetch_stock_data(symbol, '1d', '5m') # ใช้ 5m เพื่อลดภาระ API
    if not rt_data.empty:
        # ใช้ float() เพื่อป้องกัน Error Data Shape ใน Metric Sidebar
        l_price = float(rt_data['Close'].iloc[-1])
        f_open = float(rt_data['Open'].iloc[0])
        diff = l_price - f_open
        p_diff = (diff / f_open) * 100
        st.sidebar.metric(f"{symbol}", f"{l_price:.2f} USD", f"{diff:.2f} ({p_diff:.2f}%)")

st.sidebar.subheader('About')
st.sidebar.info('Dashboard นี้จะอัปเดตข้อมูลอัตโนมัติเมื่อคุณเปลี่ยนตัวเลือกในแถบด้านข้าง')
