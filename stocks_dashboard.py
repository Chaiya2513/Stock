import streamlit as st
import pandas as pd
import yfinance as yf
import ta
from streamlit_lightweight_charts import renderLightweightCharts

# --- 1. Data Layer ---
def fetch_data(ticker, period):
    # ดึงข้อมูล และจัดการ MultiIndex ของ yfinance v0.2+
    data = yf.download(ticker, period=period, interval='1d', progress=False)
    if data.empty: 
        return pd.DataFrame()
    
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    return data

def add_indicators(df):
    df = df.copy()
    
    # คำนวณ Indicators
    df['SMA'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    
    macd_obj = ta.trend.MACD(df['Close'])
    df['MACD_L'] = macd_obj.macd()
    df['MACD_S'] = macd_obj.macd_signal()
    df['MACD_H'] = macd_obj.macd_diff()
    
    # เตรียมคอลัมน์ 'time' ให้เป็น String รูปแบบ YYYY-MM-DD
    df = df.reset_index()
    df.rename(columns={df.columns[0]: 'time'}, inplace=True)
    if pd.api.types.is_datetime64_any_dtype(df['time']):
        df['time'] = df['time'].dt.strftime('%Y-%m-%d')
    
    return df

# --- 2. View Layer ---
st.set_page_config(layout="wide", page_title="Stock Analysis")
st.title('📈 Professional Stock Dashboard')

ticker = st.sidebar.text_input('Ticker Symbol', 'AAPL').upper()
raw_data = fetch_data(ticker, '1y')

if not raw_data.empty:
    df = add_indicators(raw_data)
    
    # --- CHART 1: PRICE & SMA ---
    st.subheader(f"Price Chart: {ticker}")
    
    # แปลงข้อมูลเป็น List of Dicts และเปลี่ยนชื่อคอลัมน์เป็นตัวพิมพ์เล็ก (ตาม Spec ของ Library)
    candles = df[['time','Open','High','Low','Close']].rename(
        columns={'Open':'open','High':'high','Low':'low','Close':'close'}
    ).to_dict('records')
    
    sma_data = df[['time','SMA']].dropna().rename(columns={'SMA':'value'}).to_dict('records')
    
    # สร้าง List ของ Series (ห้ามใส่ keyword 'options' เข้าไปในฟังก์ชันหากไม่แน่ใจเวอร์ชัน)
    price_series = [
        {"type": "Candlestick", "data": candles},
        {"type": "Line", "data": sma_data}
    ]
    
    # เรียกใช้โดยส่ง series และระบุ key เพื่อป้องกันการวาดซ้ำ
    renderLightweightCharts(series=price_series, key="main_chart")

    # --- CHART 2: RSI ---
    st.subheader("RSI (14)")
    rsi_data = df[['time','RSI']].dropna().rename(columns={'RSI':'value'}).to_dict('records')
    rsi_series = [{"type": "Line", "data": rsi_data}]
    renderLightweightCharts(series=rsi_series, key="rsi_chart")

    # --- CHART 3: MACD ---
    st.subheader("MACD")
    # แก้ไขชื่อคอลัมน์ให้ตรงกับที่คำนวณไว้ (MACD_L, MACD_S, MACD_H)
    m_line = df[['time','MACD_L']].dropna().rename(columns={'MACD_L':'value'}).to_dict('records')
    m_signal = df[['time','MACD_S']].dropna().rename(columns={'MACD_S':'value'}).to_dict('records')
    m_hist = df[['time','MACD_H']].dropna().rename(columns={'MACD_H':'value'}).to_dict('records')
    
    macd_series = [
        {"type": "Line", "data": m_line},
        {"type": "Line", "data": m_signal},
        {"type": "Histogram", "data": m_hist}
    ]
    renderLightweightCharts(series=macd_series, key="macd_indicator")

else:
    st.error(f"ไม่พบข้อมูลสำหรับ '{ticker}'")
