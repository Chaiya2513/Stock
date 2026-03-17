import streamlit as st
import pandas as pd
import yfinance as yf
import ta
from streamlit_lightweight_charts import renderLightweightCharts

# --- 1. Data Layer ---
def fetch_data(ticker, period='1y'):
    try:
        # ใช้ auto_adjust=True เพื่อลดโครงสร้าง MultiIndex
        data = yf.download(ticker, period=period, interval='1d', progress=False, auto_adjust=True)
        if data.empty:
            return pd.DataFrame()
        
        # ยุบ Index ให้เหลือชั้นเดียวแน่นอน
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

def add_indicators(df):
    df = df.copy()
    # คำนวณเทคนิคอล
    df['SMA'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    macd = ta.trend.MACD(df['Close'])
    df['MACD_L'] = macd.macd()
    df['MACD_S'] = macd.macd_signal()
    df['MACD_H'] = macd.macd_diff()
    
    # จัดการเวลาให้เป็น String format ที่ Lightweight Charts ต้องการ
    df = df.reset_index()
    df.rename(columns={df.columns[0]: 'time'}, inplace=True)
    df['time'] = pd.to_datetime(df['time']).dt.strftime('%Y-%m-%d')
    
    # สำคัญมาก: ตัดค่า NaN ออก เพราะ Library จะไม่แสดงผลถ้ามีค่าว่างใน Data
    return df.dropna()

# --- 2. View Layer ---
st.set_page_config(layout="wide")
st.title('📈 Professional Stock Dashboard')

ticker = st.sidebar.text_input('Ticker Symbol', 'AAPL').upper()
raw_data = fetch_data(ticker, '1y')

# ตั้งค่า Options พื้นฐานเพื่อให้กราฟมีขนาด (สำคัญมาก)
chart_options = {
    "height": 400,
    "rightPriceScale": {"visible": True, "borderColor": "rgba(197, 203, 206, 1)"},
    "layout": {"background": {"type": "solid", "color": "white"}, "textColor": "black"},
}

if not raw_data.empty:
    df = add_indicators(raw_data)
    
    # --- CHART 1: PRICE ---
    st.subheader(f"Price Chart: {ticker}")
    price_data = df[['time','Open','High','Low','Close']].rename(
        columns={'Open':'open','High':'high','Low':'low','Close':'close'}
    ).to_dict('records')
    
    sma_data = df[['time','SMA']].rename(columns={'SMA':'value'}).to_dict('records')
    
    # ส่งข้อมูลเป็นลิสต์ และตามด้วย options (ถ้า Library ต้องการ)
    # หากยังไม่ขึ้น ให้ลองลบ chart_options ออกเหลือแค่ renderLightweightCharts(series)
    renderLightweightCharts([
        {"type": "Candlestick", "data": price_data},
        {"type": "Line", "data": sma_data, "options": {"color": "#2196f3"}}
    ], "chart1")

    # --- CHART 2: RSI ---
    st.subheader("RSI (14)")
    rsi_data = df[['time','RSI']].rename(columns={'RSI':'value'}).to_dict('records')
    renderLightweightCharts([
        {"type": "Line", "data": rsi_data, "options": {"color": "#9c27b0"}}
    ], "chart2")

    # --- CHART 3: MACD ---
    st.subheader("MACD")
    m_l = df[['time','MACD_L']].rename(columns={'MACD_L':'value'}).to_dict('records')
    m_s = df[['time','MACD_S']].rename(columns={'MACD_S':'value'}).to_dict('records')
    m_h = df[['time','MACD_H']].rename(columns={'MACD_H':'value'}).to_dict('records')
    
    renderLightweightCharts([
        {"type": "Line", "data": m_l, "options": {"color": "#2196f3"}},
        {"type": "Line", "data": m_s, "options": {"color": "#ff9800"}},
        {"type": "Histogram", "data": m_h, "options": {"color": "#ef5350"}}
    ], "chart3")

else:
    st.info("กรุณากรอก Ticker ให้ถูกต้อง")
