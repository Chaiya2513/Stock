# --- CHART 1: PRICE & SMA ---
    st.subheader(f"Price Chart: {ticker}")
    
    price_series = [
        {"type": "Candlestick", "data": candles},
        {"type": "Line", "data": sma_data}
    ]
    # ส่งแค่ตัวแปรเดียว (หรือสองตัวถ้าต้องการใส่ Option) ห้ามใส่ series= หรือ key=
    renderLightweightCharts(price_series, "main_chart") 

    # --- CHART 2: RSI ---
    st.subheader("RSI (14)")
    rsi_series = [{"type": "Line", "data": rsi_data}]
    renderLightweightCharts(rsi_series, "rsi_chart")

    # --- CHART 3: MACD ---
    st.subheader("MACD")
    macd_series = [
        {"type": "Line", "data": m_line},
        {"type": "Line", "data": m_signal},
        {"type": "Histogram", "data": m_hist}
    ]
    renderLightweightCharts(macd_series, "macd_indicator")
