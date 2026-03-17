import streamlit as st
import pandas as pd
import yfinance as yf
import ta
from streamlit_lightweight_charts import renderLightweightCharts

# --- 1. Data Layer ---
def fetch_data(ticker, period):
    # ดึงข้อมูลจาก Yahoo Finance
    data = yf.download(ticker, period=period, interval='1d', progress=False)
    if data.empty: 
        return pd.DataFrame()
    
    # จัดการกรณี yfinance ส่งมาเป็น MultiIndex (สำหรับ v0.2.x ขึ้นไป)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    return data

def add_indicators(df):
    df = df.copy()
    
    # คำนวณ Moving Average และ RSI
    df['SMA'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    
    # คำนวณ MACD
    macd_obj = ta.trend.MACD(df['Close'])
    df['MACD_L'] = macd_obj.macd()
    df['MACD_S'] = macd_obj.macd_signal()
    df['MACD_H'] = macd_obj.macd_diff()
    
    # เตรียมคอลัมน์ 'time' (ต้องเป็น String รูปแบบ YYYY-MM-DD หรือ Timestamp)
    df = df.reset_index()
    df.rename(columns={df.columns[0]: 'time'}, inplace=True)
    df['time'] = df['time'].dt.strftime('%Y-%m-%d') 
    
    return df

# --- 2. View Layer (Streamlit) ---
st.set_page_config(layout="wide", page_title="Stock Dashboard")
st.title('📈 Professional Stock Dashboard')

# Sidebar สำหรับเลือกหุ้น
ticker = st.sidebar.text_input('Ticker Symbol', 'AAPL').upper()
period = st.sidebar.selectbox('Period', ['1y', '2y', '5y', 'max'], index=0)

raw_data = fetch_data(ticker, period)

if not raw_data.empty:
    df = add_indicators(raw_data)
    
    # --- CHART 1: PRICE & SMA ---
    st.subheader(f"Price Chart: {ticker}")
    
    # จัดเตรียมข้อมูลให้ตรงตาม Format (ตัวพิมพ์เล็ก: open, high, low, close, value)
    candles = df[['time','Open','High','Low','Close']].rename(
        columns={'Open':'open','High':'high','Low':'low','Close':'close'}
    ).to_dict('records')
    
    sma_data = df[['time','SMA']].dropna().rename(columns={'SMA':'value'}).to_dict('records')
    
    price_series = [
        {"type": "Candlestick", "data": candles},
        {"type": "Line", "data": sma_data}
    ]
    # เรียกใช้โดยส่งแค่ series และ key เพื่อความปลอดภัยจาก TypeError
    renderLightweightCharts(price_series, key="main_chart")

    # --- CHART 2: RSI ---
    st.subheader("RSI (14)")
    rsi_data = df[['time','RSI']].dropna().rename(columns={'RSI':'value'}).to_dict('records')
    rsi_series = [{"type": "Line", "data": rsi_data}]
    renderLightweightCharts(rsi_series, key="rsi_chart")

    # --- CHART 3: MACD ---
    st.subheader("MACD")
    # ตรวจสอบชื่อคอลัมน์ให้ตรงกับที่คำนวณไว้ (MACD_L, MACD_S, MACD_H)
    m_line = df[['time','MACD_L']].dropna().rename(columns={'MACD_L':'value'}).to_dict('records')
    m_signal = df[['time','MACD_S']].dropna().rename(columns={'MACD_S':'value'}).to_dict('records')
    m_hist = df[['time','MACD_H']].dropna().rename(columns={'MACD_H':'value'}).to_dict('records')
    
    macd_series = [
        {"type": "Line", "data": m_line},
        {"type": "Line", "data": m_signal},
        {"type": "Histogram", "data": m_hist}
    ]
    renderLightweightCharts(macd_series, key="macd_chart")

else:
    st.error(f"ไม่พบข้อมูลสำหรับหุ้น '{ticker}' กรุณาตรวจสอบชื่อ Ticker อีกครั้ง")

# ส่วนท้าย
st.markdown("---")
st.caption("Data provided by Yahoo Finance | Built with Streamlit & Lightweight Charts")
