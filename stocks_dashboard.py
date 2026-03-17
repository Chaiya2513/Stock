import streamlit as st
import pandas as pd
import yfinance as yf
import ta
from streamlit_lightweight_charts import renderLightweightCharts

# --- 1. Data Layer (ปรับปรุงให้รองรับ MultiIndex 100%) ---
def fetch_data(ticker, period):
    try:
        # ใช้ auto_adjust=True เพื่อให้ได้ราคา Close ที่ปรับแต่งแล้วมาเลย
        data = yf.download(ticker, period=period, interval='1d', progress=False, auto_adjust=True)
        
        if data.empty:
            st.warning(f"Yahoo Finance ไม่คืนข้อมูลสำหรับ {ticker}")
            return pd.DataFrame()

        # แก้ปัญหา MultiIndex ของ yfinance v0.2.0+ 
        # ถ้า columns มีมากกว่า 1 ระดับ ให้ยุบเหลือระดับเดียว
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
            
        # ตรวจสอบว่ามีคอลัมน์ที่จำเป็นไหม
        required_cols = ['Open', 'High', 'Low', 'Close']
        if not all(col in data.columns for col in required_cols):
            st.error(f"ข้อมูลไม่ครบถ้วน คอลัมน์ที่มีคือ: {list(data.columns)}")
            return pd.DataFrame()

        return data
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
        return pd.DataFrame()

def add_indicators(df):
    df = df.copy()
    
    # คำนวณ Indicators (ใช้ window แทนค่าตัวเลขลอยๆ)
    df['SMA'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    
    macd_obj = ta.trend.MACD(df['Close'])
    df['MACD_L'] = macd_obj.macd()
    df['MACD_S'] = macd_obj.macd_signal()
    df['MACD_H'] = macd_obj.macd_diff()
    
    # จัดการเวลา
    df = df.reset_index()
    # ดึงคอลัมน์แรก (ซึ่งมักจะเป็น Date หรือ Datetime) มาเป็น 'time'
    df.rename(columns={df.columns[0]: 'time'}, inplace=True)
    df['time'] = pd.to_datetime(df['time']).dt.strftime('%Y-%m-%d')
    
    return df

# --- 2. View Layer ---
st.set_page_config(layout="wide")
st.title('📈 Professional Stock Dashboard')

ticker = st.sidebar.text_input('Ticker Symbol (e.g., AAPL, TSLA, BTC-USD)', 'AAPL').upper()
period = st.sidebar.selectbox('Period', ['6m', '1y', '2y'], index=1)

raw_data = fetch_data(ticker, period)

if not raw_data.empty:
    # แสดงตัวอย่างข้อมูลที่ดึงมาได้ (เพื่อการตรวจสอบ)
    with st.expander("ดูข้อมูลดิบ (Raw Data Preview)"):
        st.write(raw_data.tail())

    df = add_indicators(raw_data)
    
    # --- กราฟหลัก ---
    st.subheader(f"Price Chart: {ticker}")
    candles = df[['time','Open','High','Low','Close']].rename(
        columns={'Open':'open','High':'high','Low':'low','Close':'close'}
    ).to_dict('records')
    
    sma_data = df[['time','SMA']].dropna().rename(columns={'SMA':'value'}).to_dict('records')
    
    price_series = [
        {"type": "Candlestick", "data": candles},
        {"type": "Line", "data": sma_data}
    ]
    renderLightweightCharts(series=price_series, key="main_chart")

    # --- RSI ---
    st.subheader("RSI (14)")
    rsi_data = df[['time','RSI']].dropna().rename(columns={'RSI':'value'}).to_dict('records')
    renderLightweightCharts(series=[{"type": "Line", "data": rsi_data}], key="rsi_chart")

    # --- MACD ---
    st.subheader("MACD")
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
    st.info("ระบุ Ticker ที่ถูกต้องใน Sidebar เพื่อเริ่มวิเคราะห์")
