import streamlit as st
import pandas as pd
import yfinance as yf
import ta
from streamlit_lightweight_charts import renderLightweightCharts

##########################################################################################
## PART 1: Data & Indicators Logic ##
##########################################################################################

def fetch_stock_data(ticker, period, interval):
    data = yf.download(ticker, period=period, interval=interval)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data

def process_data(data):
    if data.empty: return data
    df = data.copy()
    df.reset_index(inplace=True)
    time_col = df.columns[0]
    df.rename(columns={time_col: 'time'}, inplace=True)
    df['time'] = df['time'].apply(lambda x: int(x.timestamp()))
    
    # คำนวณ Indicators
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    # RSI
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    # MACD
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

st.set_page_config(layout="wide", page_title="Advanced Trading Dashboard")
st.title('🚀 Advanced Trading Dashboard (RSI & MACD)')

ticker = st.sidebar.text_input('Ticker Symbol', 'TSLA').upper()
time_period = st.sidebar.selectbox('Period', ['1mo', '3mo', '6mo', '1y', 'max'], index=1)
show_vol = st.sidebar.checkbox('Show Volume', value=True)

raw = fetch_stock_data(ticker, time_period, '1d')

if not raw.empty:
    df = process_data(raw)
    
    # --- 1. กราฟหลัก (Price + SMA + Volume) ---
    st.subheader(f"Price Chart: {ticker}")
    main_series = [
        {"type": "Candlestick", "data": df[['time','Open','High','Low','Close']].rename(columns={'Open':'open','High':'high','Low':'low','Close':'close'}).to_dict('records'), "options": {"upColor": "#26a69a", "downColor": "#ef5350", "borderVisible": False}},
        {"type": "Line", "data": df[['time','SMA_20']].dropna().rename(columns={'SMA_20':'value'}).to_dict('records'), "options": {"color": "#f29d4b", "lineWidth": 1, "title": "SMA 20"}}
    ]
    if show_vol:
        vol_data = [{"time": r['time'], "value": r['Volume'], "color": r['vol_color']} for _, r in df.iterrows()]
        main_series.append({"type": "Histogram", "data": vol_data, "options": {"priceFormat": {"type": "volume"}, "priceScaleId": "vol", "title": "Volume"}})

    renderLightweightCharts(main_series, {
        "layout": {"background": {"color": "#131722"}, "textColor": "#d1d4dc"},
        "grid": {"vertLines": {"color": "#242832"}, "horzLines": {"color": "#242832"}},
        "priceScale": {"scaleMargins": {"top": 0.1, "bottom": 0.2}},
        "extraPriceScales": {"vol": {"scaleMargins": {"top": 0.7, "bottom": 0}, "visible": False}}
    })

    # --- 2. กราฟ RSI (หน้าต่างแยก) ---
    st.subheader("Relative Strength Index (RSI)")
    rsi_series = [
        {"type": "Line", "data": df[['time','RSI']].dropna().rename(columns={'RSI':'value'}).to_dict('records'), "options": {"color": "#9b72ff", "lineWidth": 2}},
    ]
    renderLightweightCharts(rsi_series, {
        "layout": {"background": {"color": "#131722"}, "textColor": "#d1d4dc"},
        "grid": {"vertLines": {"visible": False}, "horzLines": {"color": "#242832"}},
        "priceScale": {"scaleMargins": {"top": 0.1, "bottom": 0.1}},
        "height": 150 # ปรับความสูงให้เล็กลง
    })

    # --- 3. กราฟ MACD (หน้าต่างแยก) ---
    st.subheader("MACD (Moving Average Convergence Divergence)")
    macd_series = [
        {"type": "Line", "data": df[['time','MACD']].dropna().rename(columns={'MACD':'value'}).to_dict('records'), "options": {"color": "#2196f3", "lineWidth": 1.5, "title": "MACD"}},
        {"type": "Line", "data": df[['time','MACD_Signal']].dropna().rename(columns={'MACD_Signal':'value'}).to_dict('records'), "options": {"color": "#ff5252", "lineWidth": 1.5, "title": "Signal"}},
        {"type": "Histogram", "data": df[['time','MACD_Diff','macd_color']].rename(columns={'MACD_Diff':'value','macd_color':'color'}).to_dict('records'), "options": {"title": "Histogram"}}
    ]
    renderLightweightCharts(macd_series, {
        "layout": {"background": {"color": "#131722"}, "textColor": "#d1d4dc"},
        "grid": {"vertLines": {"visible": False}, "horzLines": {"color": "#242832"}},
        "height": 200
    })

else:
    st.error("Data not found.")
