import streamlit as st
import pandas as pd
import yfinance as yf
import ta
from streamlit_lightweight_charts import renderLightweightCharts

# 1. Data Layer
def fetch_data(ticker, period):
    # เพิ่ม progress=False เพื่อไม่ให้แสดง log ใน console ของ streamlit
    data = yf.download(ticker, period=period, interval='1d', progress=False)
    if data.empty: 
        return pd.DataFrame()
    
    # จัดการ MultiIndex (yfinance v0.2.x+)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    return data

def add_indicators(df):
    df = df.copy()
    # คำนวณ Indicators (ตรวจสอบให้แน่ใจว่าคอลัมน์ 'Close' มีอยู่)
    df['SMA'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    
    macd_obj = ta.trend.MACD(df['Close'])
    df['MACD_L'] = macd_obj.macd()
    df['MACD_S'] = macd_obj.macd_signal()
    df['MACD_H'] = macd_obj.macd_diff()
    
    # เตรียมคอลัมน์ 'time' สำหรับ Lightweight Charts
    df = df.reset_index()
    # เปลี่ยนชื่อคอลัมน์แรก (Date) เป็น 'time' และแปลงเป็น Timestamp
    df.rename(columns={df.columns[0]: 'time'}, inplace=True)
    df['time'] = df['time'].dt.strftime('%Y-%m-%d') # ใช้รูปแบบ String YYYY-MM-DD จะเสถียรกว่า
    
    return df

# 2. View Layer
st.set_page_config(layout="wide")
st.title('📈 Professional Stock Dashboard')

ticker = st.sidebar.text_input('Ticker', 'AAPL').upper()
raw = fetch_data(ticker, '1y')

if not raw.empty:
    df = add_indicators(raw)
    
    # ตัวเลือกพื้นฐานสำหรับกราฟ
    chart_options = {
        "layout": {"background": {"type": "solid", "color": "white"}, "textColor": "black"},
        "height": 400,
        "width": 1000,
    }

    # --- CHART 1: PRICE & SMA ---
    st.subheader(f"Price Chart: {ticker}")
    
    # เตรียมข้อมูล Candlestick
    candles = df[['time','Open','High','Low','Close']].rename(
        columns={'Open':'open','High':'high','Low':'low','Close':'close'}
    ).to_dict('records')
    
    # เตรียมข้อมูล SMA (Line)
    sma_line = df[['time','SMA']].dropna().rename(columns={'SMA':'value'}).to_dict('records')
    
    price_series = [
        {"type": "Candlestick", "data": candles, "options": {"upColor": "#26a69a", "downColor": "#ef5350"}},
        {"type": "Line", "data": sma_line, "options": {"color": "#2196f3", "lineWidth": 2}}
    ]
    renderLightweightCharts(price_series, "main_chart")

    # --- CHART 2: RSI ---
    st.subheader("RSI (14)")
    rsi_data = df[['time','RSI']].dropna().rename(columns={'RSI':'value'}).to_dict('records')
    rsi_series = [{"type": "Line", "data": rsi_data, "options": {"color": "#9c27b0"}}]
    renderLightweightCharts(rsi_series, "rsi_chart")

    # --- CHART 3: MACD ---
    st.subheader("MACD")
    macd_l = df[['time','MACD_L']].dropna().rename(columns={'MACD_L':'value'}).to_dict('records')
    macd_s = df[['time','MACD_S']].dropna().rename(columns={'MACD_S':'value'}).to_dict('records')
    macd_h = df[['time','MACD_H']].dropna().rename(columns={'MACD_H':'value'}).to_dict('records')
    
    macd_series = [
        {"type": "Line", "data": macd_l, "options": {"color": "#2196f3", "lineWidth": 1}},
        {"type": "Line", "data": macd_s, "options": {"color": "#ff9800", "lineWidth": 1}},
        {"type": "Histogram", "data": macd_h, "options": {"color": "#ef5350"}}
    ]
    renderLightweightCharts(macd_series, "macd_chart")

else:
    st.error(f"ไม่พบข้อมูลสำหรับ Ticker: {ticker} หรือกรุณากรอกชื่อหุ้น")
