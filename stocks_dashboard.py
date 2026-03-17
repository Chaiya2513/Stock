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
        # แก้ไข MultiIndex สำหรับ yfinance version ใหม่
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
    
    # หาลำดับคอลัมน์เวลา (Date หรือ Datetime)
    time_col = df.columns[0]
    df.rename(columns={time_col: 'time'}, inplace=True)
    
    # แปลงเป็น Unix Timestamp สำหรับ Lightweight Charts
    df['time'] = df['time'].apply(lambda x: int(x.timestamp()))
    
    # --- คำนวณ Indicators ---
    # SMA 20
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    
    # RSI (14)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    
    # MACD
    macd_obj = ta.trend.MACD(df['Close'])
    df['MACD'] = macd_obj.macd()
    df['MACD_Signal'] = macd_obj.macd_signal()
    df['MACD_Diff'] = macd_obj.macd_diff()
    
    # กำหนดสี Volume และ MACD Histogram
    df['vol_color'] = df.apply(lambda x: 'rgba(38, 166, 154, 0.5)' if x['Close'] >= x['Open'] else 'rgba(239, 83, 80, 0.5)', axis=1)
    df['macd_color'] = df['MACD_Diff'].apply(lambda x: 'rgba(38, 166, 154, 0.8)' if x >= 0 else 'rgba(239, 83, 80, 0.8)')
    
    return df

###############################################
## PART 2: App Layout & Rendering ##
###############################################

st.set_page_config(layout="wide", page_title="Pro Stock Dashboard")
st.title('📈 Pro Stock Dashboard (TradingView Style)')

# --- Sidebar Settings ---
st.sidebar.header('Chart Settings')
ticker = st.sidebar.text_input('Ticker Symbol', 'TSLA').upper()
time_period = st.sidebar.selectbox('Period', ['1mo', '3mo', '6mo', '1y', 'max'], index=1)
interval = '1d' # ใช้รายวันเพื่อความเสถียรของ Indicator

raw = fetch_stock_data(ticker, time_period, interval)

if not raw.empty:
    df = process_data(raw)
    
    # แสดงราคาล่าสุดและราคาปิดก่อนหน้า
    last_p = float(raw['Close'].iloc[-1])
    prev_p = float(raw['Close'].iloc[-2])
    diff = last_p - prev_p
    p_diff = (diff / prev_p) * 100
    st.metric(f"{ticker} Latest Price", f"{last_p:.2f} USD", f"{diff:.2f} ({p_diff:.2f}%)")

    # --- กราฟที่ 1: Price & Volume ---
    st.subheader("Price & Volume")
    
    price_series = [
        # Candlestick
        {
            "type": "Candlestick",
            "data": df[['time','Open','High','Low','Close']].rename(columns={'Open':'open','High':'high','Low':'low','Close':'close'}).to_dict('records'),
            "options": {"upColor": "#26a69a", "downColor": "#ef5350", "borderVisible": False}
        },
        # SMA 20 Line
        {
            "type": "Line",
            "data": df[['time','SMA_20']].dropna().rename(columns={'SMA_20':'value'}).to_dict('records'),
            "options": {"color": "#f29d4b", "lineWidth": 1.5, "title": "SMA 20"}
        },
        # Volume Histogram (Overlay)
        {
            "type": "Histogram",
            "data": [{"time": r['time'], "value": r['Volume'], "color": r['vol_color']} for _, r in df.iterrows()],
            "options": {"priceFormat": {"type": "volume"}, "priceScaleId": "vol_scale", "title": "Volume"}
        }
    ]
    
    renderLightweightCharts(price_series, {
        "layout": {"background": {"color": "#131722"}, "textColor": "#d1d4dc"},
        "grid": {"vertLines": {"color": "#242832"}, "horzLines": {"color": "#242832"}},
        "priceScale": {"scaleMargins": {"top": 0.1, "bottom": 0.25}},
        "extraPriceScales": {"vol_scale": {"scaleMargins": {"top": 0.7, "bottom": 0}, "visible": False}},
        "timeScale": {"timeVisible": True, "borderColor": "#485c7b"}
    }, key="main_chart")

    # --- กราฟที่ 2: RSI ---
    st.subheader("RSI (14)")
    rsi_series = [{
        "type": "Line",
        "data": df[['time','RSI']].dropna().rename(columns={'RSI':'value'}).to_dict('records'),
        "options": {"color": "#9b72ff", "lineWidth": 2, "title": "RSI"}
    }]
    
    renderLightweightCharts(rsi_series, {
        "layout": {"background": {"color": "#131722"}, "textColor": "#d1d4dc"},
        "grid": {"vertLines": {"visible": False}, "horzLines": {"color": "#242832"}},
        "height": 150
    }, key="rsi_chart")

    # --- กราฟที่ 3: MACD ---
    st.subheader("MACD")
    macd_series = [
        {"type": "Line", "data": df[['time','MACD']].dropna().rename(columns={'MACD':'value'}).to_dict('records'), "options": {"color": "#2196f3", "lineWidth": 1.5, "title": "MACD"}},
        {"type": "Line", "data": df[['time','MACD_Signal']].dropna().rename(columns={'MACD_Signal':'value'}).to_dict('records'), "options": {"color": "#ff5252", "lineWidth": 1.5, "title": "Signal"}},
        {"type": "Histogram", "data": df[['time','MACD_Diff','macd_color']].rename(columns={'MACD_Diff':'value','macd_color':'color'}).to_dict('records'), "options": {"title": "Diff"}}
    ]
    
    renderLightweightCharts(macd_series, {
        "layout": {"background": {"color": "#131722"}, "textColor": "#d1d4dc"},
        "grid": {"vertLines": {"visible": False}, "horzLines": {"color": "#242832"}},
        "height": 200
    }, key="macd_chart")

    # --- Raw Data Expandable ---
    with st.expander("View Raw Historical Data"):
        st.dataframe(raw.tail(20))

else:
    st.warning("Please enter a valid Ticker symbol in the sidebar.")
