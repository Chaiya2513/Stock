import streamlit as st
import pandas as pd
import yfinance as yf
import ta
from streamlit_lightweight_charts import renderLightweightCharts

# 1. Data Layer: จัดการข้อมูลให้สะอาดที่สุด
def fetch_and_clean_data(ticker, period):
    data = yf.download(ticker, period=period, interval='1d')
    if data.empty: return pd.DataFrame()
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    # คำนวณ Indicators
    data['SMA'] = ta.trend.sma_indicator(data['Close'], window=20)
    data['RSI'] = ta.momentum.rsi(data['Close'], window=14)
    macd = ta.trend.MACD(data['Close'])
    data['M'], data['MS'], data['MH'] = macd.macd(), macd.macd_signal(), macd.macd_diff()
    
    # เตรียม Time Index
    data.reset_index(inplace=True)
    data.rename(columns={data.columns[0]: 'time'}, inplace=True)
    data['time'] = data['time'].apply(lambda x: int(x.timestamp()))
    return data

# 2. View Layer: แสดงผลกราฟ
st.set_page_config(layout="wide")
st.title('Professional Stock Analysis')

ticker = st.sidebar.text_input('Ticker', 'AAPL').upper()
df = fetch_and_clean_data(ticker, '1y')

if not df.empty:
    # --- CHART 1: PRICE ---
    st.subheader("Price Chart")
    # ตัดพารามิเตอร์ 'options' ออกทั้งหมดเพื่อเลี่ยง TypeError
    price_data = [
        {"type": "Candlestick", "data": df[['time','Open','High','Low','Close']].rename(columns={'Open':'open','High':'high','Low':'low','Close':'close'}).to_dict('records')},
        {"type": "Line", "data": df[['time','SMA']].dropna().rename(columns={'SMA':'value'}).to_dict('records')}
    ]
    renderLightweightCharts(price_data, key="p1")

    # --- CHART 2: RSI ---
    st.subheader("RSI (14)")
    rsi_data = [{"type": "Line", "data": df[['time','RSI']].dropna().rename(columns={'RSI':'value'}).to_dict('records')}]
    renderLightweightCharts(rsi_data, key="r1")

    # --- CHART 3: MACD ---
    st.subheader("MACD")
    # สำคัญ: ส่งเฉพาะข้อมูลพื้นฐาน (time, value) และตัด 'options' ออก
    macd_data = [
        {"type": "Line", "data": df[['time','M']].dropna().rename(columns={'M':'value'}).to_dict('records')},
        {"type": "Line", "data": df[['time','MS']].dropna().rename(columns={'MS':'value'}).to_dict('records')},
        {"type": "Histogram", "data": df[['time','MH']].dropna().rename(columns={'MH':'value'}).to_dict('records')}
    ]
    renderLightweightCharts(macd_data, key="m1")

else:
    st.info("กรุณาระบุ Ticker")
