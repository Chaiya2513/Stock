import streamlit as st
import pandas as pd
import yfinance as yf
import ta
from streamlit_lightweight_charts import renderLightweightCharts

# --- 1. Data Logic Layer ---
def get_clean_data(ticker, period):
    """ดึงข้อมูลและจัดการ MultiIndex ให้เป็น Single Level"""
    data = yf.download(ticker, period=period, interval='1d')
    if data.empty:
        return pd.DataFrame()
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data

def apply_technical_analysis(df):
    """คำนวณ Indicators และจัดการ Format สำหรับ Lightweight Charts"""
    df = df.copy()
    df.reset_index(inplace=True)
    # เปลี่ยนชื่อ index/date เป็น time และแปลงเป็น Unix Timestamp (Required by Library)
    df.rename(columns={df.columns[0]: 'time'}, inplace=True)
    df['time'] = df['time'].apply(lambda x: int(x.timestamp()))
    
    # คำนวณ Indicators
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    
    macd_obj = ta.trend.MACD(df['Close'])
    df['MACD'] = macd_obj.macd()
    df['MACD_S'] = macd_obj.macd_signal()
    df['MACD_H'] = macd_obj.macd_diff()
    
    # สี Volume และ MACD Histogram (RGBA format)
    df['vol_color'] = df.apply(lambda x: 'rgba(38, 166, 154, 0.5)' if x['Close'] >= x['Open'] else 'rgba(239, 83, 80, 0.5)', axis=1)
    df['macd_color'] = df['MACD_H'].apply(lambda x: 'rgba(38, 166, 154, 0.8)' if x >= 0 else 'rgba(239, 83, 80, 0.8)')
    
    return df

# --- 2. Presentation Layer ---
st.set_page_config(layout="wide", page_title="Professional Stock Dashboard")
st.title('📊 Professional Trading Dashboard')

ticker = st.sidebar.text_input('Ticker Symbol', 'AAPL').upper()
period = st.sidebar.selectbox('Period', ['3mo', '6mo', '1y', 'max'], index=1)

raw_df = get_clean_data(ticker, period)

if not raw_df.empty:
    df = apply_technical_analysis(raw_df)
    
    # --- CHART 1: PRICE & VOLUME ---
    st.subheader("Price Action & Volume")
    
    # รวมข้อมูลและ Options เข้าไปในชุดข้อมูลเดียวตาม API Spec
    price_charts = [
        {
            "type": "Candlestick",
            "data": df[['time','Open','High','Low','Close']].rename(columns={'Open':'open','High':'high','Low':'low','Close':'close'}).to_dict('records'),
            "options": {"upColor": "#26a69a", "downColor": "#ef5350", "borderVisible": False}
        },
        {
            "type": "Line",
            "data": df[['time','SMA_20']].dropna().rename(columns={'SMA_20':'value'}).to_dict('records'),
            "options": {"color": "#f29d4b", "lineWidth": 2, "title": "SMA 20"}
        },
        {
            "type": "Histogram",
            "data": [{"time": r['time'], "value": float(r['Volume']), "color": r['vol_color']} for _, r in df.iterrows()],
            "options": {"priceFormat": {"type": "volume"}, "priceScaleId": "vol", "title": "Volume"}
        }
    ]
    # เรียกใช้ฟังก์ชันด้วย 2 พารามิเตอร์ตาม Signature (charts, key)
    renderLightweightCharts(price_charts, key="main_price")

    # --- CHART 2: RSI ---
    st.subheader("RSI (14)")
    rsi_charts = [{
        "type": "Line", 
        "data": df[['time','RSI']].dropna().rename(columns={'RSI':'value'}).to_dict('records'),
        "options": {"color": "#9b72ff", "lineWidth": 2, "title": "RSI"}
    }]
    renderLightweightCharts(rsi_charts, key="rsi_indicator")

    # --- CHART 3: MACD ---
    st.subheader("MACD")
    macd_charts = [
        {"type": "Line", "data": df[['time','MACD']].dropna().rename(columns={'MACD':'value'}).to_dict('records'), "options": {"color": "#2196f3", "title": "MACD"}},
        {"type": "Line", "data": df[['time','MACD_S']].dropna().rename(columns={'MACD_S':'value'}).to_dict('records'), "options": {"color": "#ff5252", "title": "Signal"}},
        {"type": "Histogram", "data": df[['time','MACD_H','macd_color']].dropna().rename(columns={'MACD_H':'value','macd_color':'color'}).to_dict('records'), "options": {"title": "Histogram"}}
    ]
    renderLightweightCharts(macd_charts, key="macd_indicator")

else:
    st.info("กรุณาระบุ Ticker ที่ถูกต้องเพื่อแสดงข้อมูล")

st.sidebar.markdown("---")
st.sidebar.caption("Stable Professional Version 1.0")
