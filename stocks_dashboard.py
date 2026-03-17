import streamlit as st
import pandas as pd
import yfinance as yf
import ta
from streamlit_lightweight_charts import renderLightweightCharts

# --- 1. Data Layer: ดึงข้อมูลและจัดการโครงสร้างให้ถูกต้อง ---
def fetch_data(ticker, period='1y'):
    try:
        # ใช้ auto_adjust=True เพื่อลดปัญหา MultiIndex และได้ราคาที่ปรับแต่งแล้ว
        data = yf.download(ticker, period=period, interval='1d', progress=False, auto_adjust=True)
        
        if data.empty:
            return pd.DataFrame()

        # แก้ปัญหา MultiIndex (yfinance v0.2.x) ให้เหลือชั้นเดียว
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

def add_indicators(df):
    df = df.copy()
    
    # 1. Moving Average
    df['SMA'] = ta.trend.sma_indicator(df['Close'], window=20)
    
    # 2. RSI
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    
    # 3. MACD
    macd_obj = ta.trend.MACD(df['Close'])
    df['MACD_L'] = macd_obj.macd()
    df['MACD_S'] = macd_obj.macd_signal()
    df['MACD_H'] = macd_obj.macd_diff()
    
    # จัดการเรื่องเวลา (แปลงเป็น String format 'YYYY-MM-DD')
    df = df.reset_index()
    # คอลัมน์แรกมักจะเป็น Date หรือ Datetime
    df.rename(columns={df.columns[0]: 'time'}, inplace=True)
    df['time'] = pd.to_datetime(df['time']).dt.strftime('%Y-%m-%d')
    
    # ลบแถวที่มีค่าว่าง (NaN) ออกเพื่อป้องกันกราฟค้าง
    return df.dropna()

# --- 2. View Layer: แสดงผลบน Streamlit ---
st.set_page_config(layout="wide", page_title="Simple Stock Dashboard")
st.title('📈 Professional Stock Dashboard')

# Sidebar สำหรับตั้งค่า
ticker = st.sidebar.text_input('Ticker Symbol (เช่น AAPL, TSLA, BTC-USD)', 'AAPL').upper()
period = st.sidebar.selectbox('ช่วงเวลา', ['6m', '1y', '2y', '5y'], index=1)

raw_data = fetch_data(ticker, period)

if not raw_data.empty:
    df = add_indicators(raw_data)
    
    # --- CHART 1: PRICE & SMA ---
    st.subheader(f"Price Chart: {ticker}")
    
    # เตรียมข้อมูล (ต้องเป็นตัวพิมพ์เล็กทั้งหมด: open, high, low, close, value)
    price_data = df[['time','Open','High','Low','Close']].rename(
        columns={'Open':'open','High':'high','Low':'low','Close':'close'}
    ).to_dict('records')
    
    sma_data = df[['time','SMA']].rename(columns={'SMA':'value'}).to_dict('records')
    
    # ส่งเฉพาะ positional arguments (ตัวแปรตรงๆ) เพื่อเลี่ยง TypeError
    renderLightweightCharts([
        {"type": "Candlestick", "data": price_data},
        {"type": "Line", "data": sma_data}
    ], "main_chart")

    # --- CHART 2: RSI ---
    st.subheader("RSI (14)")
    rsi_data = df[['time','RSI']].rename(columns={'RSI':'value'}).to_dict('records')
    renderLightweightCharts([{"type": "Line", "data": rsi_data}], "rsi_chart")

    # --- CHART 3: MACD ---
    st.subheader("MACD")
    m_line = df[['time','MACD_L']].rename(columns={'MACD_L':'value'}).to_dict('records')
    m_signal = df[['time','MACD_S']].rename(columns={'MACD_S':'value'}).to_dict('records')
    m_hist = df[['time','MACD_H']].rename(columns={'MACD_H':'value'}).to_dict('records')
    
    renderLightweightCharts([
        {"type": "Line", "data": m_line},
        {"type": "Line", "data": m_signal},
        {"type": "Histogram", "data": m_hist}
    ], "macd_chart")

else:
    st.warning(f"ไม่พบข้อมูลสำหรับ '{ticker}' กรุณาตรวจสอบชื่อย่อหุ้นอีกครั้ง")

# ตกแต่งเพิ่มเติม
st.divider()
st.caption("Data source: Yahoo Finance | สร้างโดย คู่หูเขียนโค้ด")
