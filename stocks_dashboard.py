import streamlit as st
import pandas as pd
import yfinance as yf
import ta
from streamlit_lightweight_charts import renderLightweightCharts

# 1. Data Layer
def fetch_data(ticker, period):
    data = yf.download(ticker, period=period, interval='1d')
    if data.empty: return pd.DataFrame()
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data

def add_indicators(df):
    df = df.copy()
    # คำนวณ Indicators
    df['SMA'] = ta.trend.sma_indicator(df['Close'], 20)
    df['RSI'] = ta.momentum.rsi(df['Close'], 14)
    macd = ta.trend.MACD(df['Close'])
    df['MACD_L'] = macd.macd()
    df['MACD_S'] = macd.macd_signal()
    df['MACD_H'] = macd.macd_diff()
    
    # แปลงเวลา
    df.reset_index(inplace=True)
    df.rename(columns={df.columns[0]: 'time'}, inplace=True)
    df['time'] = df['time'].apply(lambda x: int(x.timestamp()))
    return df

# 2. View Layer
st.set_page_config(layout="wide")
st.title('📈 Professional Stock Dashboard')

ticker = st.sidebar.text_input('Ticker', 'AAPL').upper()
raw = fetch_data(ticker, '1y')

if not raw.empty:
    df = add_indicators(raw)
    
    # --- CHART 1: PRICE ---
    st.subheader("Price Chart")
    price_charts = [
        {"type": "Candlestick", "data": df[['time','Open','High','Low','Close']].rename(columns={'Open':'open','High':'high','Low':'low','Close':'close'}).to_dict('records')},
        {"type": "Line", "data": df[['time','SMA']].dropna().rename(columns={'SMA':'value'}).to_dict('records')}
    ]
    # ส่งค่าเพียง 2 ตัวแปรตามที่ Library กำหนด
    renderLightweightCharts(price_charts, "main_chart")

    # --- CHART 2: RSI ---
    st.subheader("RSI (14)")
    rsi_charts = [{"type": "Line", "data": df[['time','RSI']].dropna().rename(columns={'RSI':'value'}).to_dict('records')}]
    renderLightweightCharts(rsi_charts, "rsi_chart")

    # --- CHART 3: MACD ---
    st.subheader("MACD")
    # ห้ามใส่คีย์ 'options' หรือคีย์อื่นๆ นอกเหนือจาก 'type' และ 'data'
    macd_charts = [
        {"type": "Line", "data": df[['time','MACD_L']].dropna().rename(columns={'MACD_L':'value'}).to_dict('records')},
        {"type": "Line", "data": df[['time','MACD_S']].dropna().rename(columns={'MACD_S':'value'}).to_dict('records')},
        {"type": "Histogram", "data": df[['time','MACD_H']].dropna().rename(columns={'MACD_H':'value'}).to_dict('records')}
    ]
    renderLightweightCharts(macd_charts, "macd_chart")

else:
    st.info("กรุณาระบุ Ticker")
