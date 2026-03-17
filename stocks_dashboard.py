import streamlit as st
import pandas as pd
import yfinance as yf
import ta
from streamlit_lightweight_charts import renderLightweightCharts

##########################################################################################
## PART 1: Data Processing & Indicators Logic ##
##########################################################################################

def fetch_stock_data(ticker, period):
    try:
        # ดึงข้อมูลรายวัน (1d) เพื่อความแม่นยำของ Indicator
        data = yf.download(ticker, period=period, interval='1d')
        if data.empty:
            return pd.DataFrame()
        # แก้ไขปัญหา MultiIndex จาก yfinance version ใหม่
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        return data
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

def process_indicators(data):
    if data.empty: return data
    df = data.copy()
    df.reset_index(inplace=True)
    
    # หาลำดับคอลัมน์เวลาและแปลงเป็น Unix Timestamp
    time_col = df.columns[0]
    df.rename(columns={time_col: 'time'}, inplace=True)
    df['time'] = df['time'].apply(lambda x: int(x.timestamp()))
    
    # --- คำนวณ Indicators (ป้องกัน NaN) ---
    df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
    df['RSI'] = ta.momentum.rsi(df['Close'], window=14)
    
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

st.set_page_config(layout="wide", page_title="Ultimate Stock Dashboard")
st.title('📊 Ultimate TradingView Dashboard')

# Sidebar Settings
st.sidebar.header('Chart Parameters')
ticker = st.sidebar.text_input('Ticker Symbol', 'NVDA').upper()
time_period = st.sidebar.selectbox('Period', ['3mo', '6mo', '1y', 'max'], index=1)

raw_data = fetch_stock_data(ticker, time_period)

if not raw_data.empty:
    df = process_indicators(raw_data)
    
    # --- ส่วนที่ 1: กราฟราคาและโวลลุ่ม (Price & Volume) ---
    st.subheader(f"Price Chart: {ticker}")
    
    # เตรียมข้อมูล (ตัด NaN ออก)
    price_series = [
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
            "options": {"priceFormat": {"type": "volume"}, "priceScaleId": "vol_scale", "title": "Volume"}
        }
    ]
    
    renderLightweightCharts(
        charts=price_series,
        options={
            "layout": {"background": {"color": "#131722"}, "textColor": "#d1d4dc"},
            "grid": {"vertLines": {"color": "#242832"}, "horzLines": {"color": "#242832"}},
            "priceScale": {"scaleMargins": {"top": 0.1, "bottom": 0.3}},
            "extraPriceScales": {"vol_scale": {"scaleMargins": {"top": 0.7, "bottom": 0}, "visible": False}},
            "timeScale": {"timeVisible": True, "borderColor": "#485c7b"}
        },
        key="main_price_chart"
    )

    # --- ส่วนที่ 2: RSI (หน้าต่างแยก) ---
    st.subheader("RSI (14)")
    rsi_series = [{
        "type": "Line",
        "data": df[['time','RSI']].dropna().rename(columns={'RSI':'value'}).to_dict('records'),
        "options": {"color": "#9b72ff", "lineWidth": 2}
    }]
    
    renderLightweightCharts(
        charts=rsi_series,
        options={
            "layout": {"background": {"color": "#131722"}, "textColor": "#d1d4dc"},
            "grid": {"horzLines": {"color": "#242832"}, "vertLines": {"visible": False}},
            "height": 150
        },
        key="rsi_sub_chart"
    )

    # --- ส่วนที่ 3: MACD (หน้าต่างแยก) ---
    st.subheader("MACD")
    macd_series = [
        {"type": "Line", "data": df[['time','MACD']].dropna().rename(columns={'MACD':'value'}).to_dict('records'), "options": {"color": "#2196f3", "lineWidth": 1.5, "title": "MACD"}},
        {"type": "Line", "data": df[['time','MACD_Signal']].dropna().rename(columns={'MACD_Signal':'value'}).to_dict('records'), "options": {"color": "#ff5252", "lineWidth": 1.5, "title": "Signal"}},
        {"type": "Histogram", "data": df[['time','MACD_Diff','macd_color']].dropna().rename(columns={'MACD_Diff':'value','macd_color':'color'}).to_dict('records'), "options": {"title": "Histogram"}}
    ]
    
    renderLightweightCharts(
        charts=macd_series,
        options={
            "layout": {"background": {"color": "#131722"}, "textColor": "#d1d4dc"},
            "grid": {"horzLines": {"color": "#242832"}, "vertLines": {"visible": False}},
            "height": 200
        },
        key="macd_sub_chart"
    )

else:
    st.info("กรุณาป้อน Ticker หุ้นในช่อง Sidebar เพื่อเริ่มวิเคราะห์")

st.sidebar.markdown("---")
st.sidebar.caption("TradingView-style Lightweight Charts")
