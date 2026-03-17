import streamlit as st
import pandas as pd
import yfinance as yf
import ta
from streamlit_lightweight_charts import renderLightweightCharts

##########################################################################################
## PART 1: Data Processing & Indicators ##
##########################################################################################

def fetch_stock_data(ticker, period, interval):
    try:
        data = yf.download(ticker, period=period, interval=interval)
        if data.empty:
            return pd.DataFrame()
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

def process_data(data):
    if data.empty: return data
    df = data.copy()
    df.reset_index(inplace=True)
    
    # หาลำดับคอลัมน์เวลา
    time_col = df.columns[0]
    df.rename(columns={time_col: 'time'}, inplace=True)
    df['time'] = df['time'].apply(lambda x: int(x.timestamp()))
    
    # คำนวณ Indicators (จัดการค่า NaN ภายในตัว)
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    
    macd_obj = ta.trend.MACD(df['Close'])
    df['MACD'] = macd_obj.macd()
    df['MACD_Signal'] = macd_obj.macd_signal()
    df['MACD_Diff'] = macd_obj.macd_diff()
    
    # สีสำหรับ Volume และ MACD Histogram
    df['vol_color'] = df.apply(lambda x: 'rgba(38, 166, 154, 0.5)' if x['Close'] >= x['Open'] else 'rgba(239, 83, 80, 0.5)', axis=1)
    df['macd_color'] = df['MACD_Diff'].apply(lambda x: 'rgba(38, 166, 154, 0.8)' if x >= 0 else 'rgba(239, 83, 80, 0.8)')
    
    return df

###############################################
## PART 2: App Layout & Rendering ##
###############################################

st.set_page_config(layout="wide", page_title="Pro Trading Dashboard")
st.title('📈 Pro Trading Dashboard (Stable Version)')

# Sidebar
st.sidebar.header('Chart Settings')
ticker = st.sidebar.text_input('Ticker Symbol', 'NVDA').upper()
time_period = st.sidebar.selectbox('Period', ['3mo', '6mo', '1y', 'max'], index=0)

raw = fetch_stock_data(ticker, time_period, '1d')

if not raw.empty:
    df = process_data(raw)
    
    # Metric Price
    last_p = float(df['Close'].iloc[-1])
    prev_p = float(df['Close'].iloc[-2])
    diff = last_p - prev_p
    p_diff = (diff / prev_p) * 100
    st.metric(f"{ticker}", f"{last_p:.2f} USD", f"{diff:.2f} ({p_diff:.2f}%)")

    # --- 1. กราฟหลัก (Price + SMA + Volume) ---
    st.subheader("Price & Volume")
    
    # เตรียมข้อมูล (ตัด NaN ออกให้หมด)
    candles = df[['time','Open','High','Low','Close']].copy()
    candles.columns = ['time','open','high','low','close']
    
    sma_data = df[['time','SMA_20']].dropna().copy()
    sma_data.columns = ['time','value']
    
    vol_data = [{"time": int(r['time']), "value": float(r['Volume']), "color": r['vol_color']} for _, r in df.iterrows()]

    price_series = [
        {"type": "Candlestick", "data": candles.to_dict('records'), "options": {"upColor": "#26a69a", "downColor": "#ef5350", "borderVisible": False}},
        {"type": "Line", "data": sma_data.to_dict('records'), "options": {"color": "#f29d4b", "lineWidth": 1.5, "title": "SMA 20"}},
        {"type": "Histogram", "data": vol_data, "options": {"priceFormat": {"type": "volume"}, "priceScaleId": "vol_scale", "title": "Volume"}}
    ]
    
    renderLightweightCharts(price_series, {
        "layout": {"background": {"color": "#131722"}, "textColor": "#d1d4dc"},
        "grid": {"vertLines": {"color": "#242832"}, "horzLines": {"color": "#242832"}},
        "priceScale": {"scaleMargins": {"top": 0.1, "bottom": 0.25}},
        "extraPriceScales": {"vol_scale": {"scaleMargins": {"top": 0.7, "bottom": 0}, "visible": False}},
        "timeScale": {"timeVisible": True, "borderColor": "#485c7b"}
    }, key="main_chart")

    # --- 2. กราฟ RSI ---
    st.subheader("RSI (14)")
    rsi_data = df[['time','RSI']].dropna().copy()
    rsi_data.columns = ['time','value']
    
    rsi_series = [{"type": "Line", "data": rsi_data.to_dict('records'), "options": {"color": "#9b72ff", "lineWidth": 2}}]
    
    renderLightweightCharts(rsi_series, {
        "layout": {"background": {"color": "#131722"}, "textColor": "#d1d4dc"},
        "grid": {"vertLines": {"visible": False}, "horzLines": {"color": "#242832"}},
        "height": 150
    }, key="rsi_chart")

    # --- 3. กราฟ MACD ---
    st.subheader("MACD")
    m_line = df[['time','MACD']].dropna().rename(columns={'MACD':'value'}).to_dict('records')
    m_sig = df[['time','MACD_Signal']].dropna().rename(columns={'MACD_Signal':'value'}).to_dict('records')
    m_hist = df[['time','MACD_Diff','macd_color']].dropna().rename(columns={'MACD_Diff':'value','macd_color':'color'}).to_dict('records')

    macd_series = [
        {"type": "Line", "data": m_line, "options": {"color": "#2196f3", "lineWidth": 1.5, "title": "MACD"}},
        {"type": "Line", "data": m_sig, "options": {"color": "#ff5252", "lineWidth": 1.5, "title": "Signal"}},
        {"type": "Histogram", "data": m_hist, "options": {"title": "Histogram"}}
    ]
    
    renderLightweightCharts(macd_series, {
        "layout": {"background": {"color": "#131722"}, "textColor": "#d1d4dc"},
        "grid": {"vertLines": {"visible": False}, "horzLines": {"color": "#242832"}},
        "height": 200
    }, key="macd_chart")

else:
    st.info("กรุณาใส่ชื่อ Ticker หุ้นใน Sidebar เพื่อเริ่มแสดงกราฟ")

st.sidebar.markdown("---")
st.sidebar.caption("Powered by Streamlit & Lightweight Charts")
