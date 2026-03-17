import streamlit as st
import pandas as pd
import yfinance as yf
import ta
from streamlit_lightweight_charts import renderLightweightCharts

# --- 1. Data Layer ---
def fetch_data(ticker, period):
    data = yf.download(ticker, period=period, interval='1d')
    if data.empty: return pd.DataFrame()
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data

def process_indicators(df):
    df = df.copy()
    # คำนวณ Indicators ก่อน Reset Index เพื่อใช้ Index เดิมในการจัดการค่า NaN
    df['SMA'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    macd_obj = ta.trend.MACD(df['Close'])
    df['M'] = macd_obj.macd()
    df['MS'] = macd_obj.macd_signal()
    df['MH'] = macd_obj.macd_diff()
    
    # จัดการสี Volume (RGBA)
    df['v_c'] = df.apply(lambda x: 'rgba(38,166,154,0.5)' if x['Close'] >= x['Open'] else 'rgba(239,83,80,0.5)', axis=1)
    df['m_c'] = df['MH'].apply(lambda x: 'rgba(38,166,154,0.8)' if x >= 0 else 'rgba(239,83,80,0.8)')
    
    # แปลงเวลาเป็น Unix Timestamp
    df.reset_index(inplace=True)
    df.rename(columns={df.columns[0]: 'time'}, inplace=True)
    df['time'] = df['time'].apply(lambda x: int(x.timestamp()))
    return df

# --- 2. View Layer ---
st.set_page_config(layout="wide")
st.title('📊 Professional Stock Analysis')

ticker = st.sidebar.text_input('Ticker', 'AAPL').upper()
raw = fetch_data(ticker, '1y')

if not raw.empty:
    df = process_indicators(raw)
    
    # --- CHART 1: PRICE ---
    # กรองเฉพาะแถวที่ไม่มี NaN สำหรับซีรีส์นั้นๆ เพื่อป้องกัน TypeError
    c_data = df[['time','Open','High','Low','Close']].rename(columns={'Open':'open','High':'high','Low':'low','Close':'close'}).to_dict('records')
    s_data = df[['time','SMA']].dropna().rename(columns={'SMA':'value'}).to_dict('records')
    v_data = [{"time": int(r['time']), "value": float(r['Volume']), "color": r['v_c']} for _, r in df.iterrows()]

    renderLightweightCharts([
        {"type": "Candlestick", "data": c_data},
        {"type": "Line", "data": s_data, "options": {"color": "#f29d4b", "lineWidth": 2}},
        {"type": "Histogram", "data": v_data, "options": {"priceScaleId": "vol"}}
    ], key="p_chart")

    # --- CHART 2: RSI ---
    rsi_data = df[['time','RSI']].dropna().rename(columns={'RSI':'value'}).to_dict('records')
    renderLightweightCharts([{"type": "Line", "data": rsi_data, "options": {"color": "#9b72ff"}}], key="r_chart")

    # --- CHART 3: MACD ---
    # แยกดึงข้อมูลแต่ละเส้นและจัดการ NaN ให้เรียบร้อยก่อนส่ง
    m_line = df[['time','M']].dropna().rename(columns={'M':'value'}).to_dict('records')
    s_line = df[['time','MS']].dropna().rename(columns={'MS':'value'}).to_dict('records')
    h_line = df[['time','MH','m_c']].dropna().rename(columns={'MH':'value','m_c':'color'}).to_dict('records')

    renderLightweightCharts([
        {"type": "Line", "data": m_line, "options": {"color": "#2196f3"}},
        {"type": "Line", "data": s_line, "options": {"color": "#ff5252"}},
        {"type": "Histogram", "data": h_line}
    ], key="m_chart")

else:
    st.info("กรุณาระบุ Ticker")
