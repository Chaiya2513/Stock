import streamlit as st
import pandas as pd
import yfinance as yf
import ta
from streamlit_lightweight_charts import renderLightweightCharts

##########################################################################################
## PART 1: Data Processing ##
##########################################################################################

def fetch_stock_data(ticker, period, interval):
    try:
        data = yf.download(ticker, period=period, interval=interval)
        if data.empty: return pd.DataFrame()
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except: return pd.DataFrame()

def process_data(data):
    if data.empty: return data
    df = data.copy()
    df.reset_index(inplace=True)
    # เปลี่ยนชื่อคอลัมน์วันที่เป็น time และแปลงเป็น Unix Timestamp
    df.rename(columns={df.columns[0]: 'time'}, inplace=True)
    df['time'] = df['time'].apply(lambda x: int(x.timestamp()))
    
    # คำนวณ Indicators
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    df['MACD_S'] = macd.macd_signal()
    df['MACD_H'] = macd.macd_diff()
    
    # สี Volume และ MACD
    df['v_col'] = df.apply(lambda x: 'rgba(38, 166, 154, 0.5)' if x['Close'] >= x['Open'] else 'rgba(239, 83, 80, 0.5)', axis=1)
    df['m_col'] = df['MACD_H'].apply(lambda x: 'rgba(38, 166, 154, 0.8)' if x >= 0 else 'rgba(239, 83, 80, 0.8)')
    return df

###############################################
## PART 2: App Layout & Fixed Rendering ##
###############################################

st.set_page_config(layout="wide", page_title="Stable Stock Dashboard")
st.title('🚀 Stable Stock Dashboard')

ticker = st.sidebar.text_input('Ticker Symbol', 'TSLA').upper()
time_period = st.sidebar.selectbox('Period', ['3mo', '6mo', '1y'], index=0)

raw = fetch_stock_data(ticker, time_period, '1d')

if not raw.empty:
    df = process_data(raw)
    
    # Common Chart Options
    chart_opts = {
        "layout": {"background": {"color": "#131722"}, "textColor": "#d1d4dc"},
        "grid": {"vertLines": {"color": "#242832"}, "horzLines": {"color": "#242832"}},
        "timeScale": {"timeVisible": True}
    }

    # --- 1. Main Chart (Price + Volume) ---
    st.subheader("Price & Volume")
    price_series = [
        {"type": "Candlestick", "data": df[['time','Open','High','Low','Close']].rename(columns={'Open':'open','High':'high','Low':'low','Close':'close'}).to_dict('records'), "options": {"upColor": "#26a69a", "downColor": "#ef5350", "borderVisible": False}},
        {"type": "Line", "data": df[['time','SMA_20']].dropna().rename(columns={'SMA_20':'value'}).to_dict('records'), "options": {"color": "#f29d4b", "lineWidth": 1.5, "title": "SMA 20"}},
        {"type": "Histogram", "data": [{"time": r['time'], "value": r['Volume'], "color": r['v_col']} for _, r in df.iterrows()], "options": {"priceFormat": {"type": "volume"}, "priceScaleId": "vol", "title": "Volume"}}
    ]
    # รวม Options เข้าไปในตัวแปรเดียวกับที่ Library ต้องการ (ถ้า Library version นี้ต้องการแค่ list ของ series)
    renderLightweightCharts(charts=price_series, key="main")

    # --- 2. RSI ---
    st.subheader("RSI")
    rsi_series = [{"type": "Line", "data": df[['time','RSI']].dropna().rename(columns={'RSI':'value'}).to_dict('records'), "options": {"color": "#9b72ff", "lineWidth": 2}}]
    renderLightweightCharts(charts=rsi_series, key="rsi")

    # --- 3. MACD ---
    st.subheader("MACD")
    macd_series = [
        {"type": "Line", "data": df[['time','MACD']].dropna().rename(columns={'MACD':'value'}).to_dict('records'), "options": {"color": "#2196f3", "lineWidth": 1, "title": "MACD"}},
        {"type": "Line", "data": df[['time','MACD_S']].dropna().rename(columns={'MACD_S':'value'}).to_dict('records'), "options": {"color": "#ff5252", "lineWidth": 1, "title": "Signal"}},
        {"type": "Histogram", "data": df[['time','MACD_H','m_col']].dropna().rename(columns={'MACD_H':'value','m_col':'color'}).to_dict('records')}
    ]
    renderLightweightCharts(charts=macd_series, key="macd")

else:
    st.info("กรุณาป้อน Ticker หุ้น")
