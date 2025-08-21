import streamlit as st
import pandas as pd
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Fund Analysis Tool",
    page_icon="📊",
    layout="wide"
)

# --- Header ---
st.title("📈 Mutual Fund Predictive Alert System")
st.markdown("This tool analyzes historical NAV data from a CSV file you provide.")
st.markdown("---")

# --- File Uploader ---
st.header("1. Upload Your Fund's NAV Data")
uploaded_file = st.file_uploader("Choose a CSV file with 'Date' and 'NAV' columns", type="csv")

nav_data = None

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        date_col = next((col for col in df.columns if 'date' in col.lower()), None)
        nav_col = next((col for col in df.columns if 'nav' in col.lower() or 'net asset value' in col.lower()), None)

        if date_col and nav_col:
            nav_data = df[[date_col, nav_col]].copy()
            nav_data.columns = ['Date', 'NAV']
            nav_data['Date'] = pd.to_datetime(nav_data['Date'])
            nav_data.set_index('Date', inplace=True)
            nav_data['NAV'] = pd.to_numeric(nav_data['NAV'], errors='coerce')
            nav_data.dropna(inplace=True)
            nav_data.sort_index(inplace=True)
            st.success("CSV file processed successfully!")
        else:
            st.error("Could not find 'Date' and 'NAV' columns in the uploaded file. Please check the CSV.")
    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")

st.markdown("---")

# --- Analysis Section (only appears if data is loaded) ---
if nav_data is not None and not nav_data.empty:
    st.header("2. Analysis and Predictions")

    # --- Next-Day Prediction Module ---
    tomorrow_date = (datetime.now() + pd.Timedelta(days=1)).strftime('%B %d, %Y')
    st.subheader(f"Next-Day Investment Signal (for {tomorrow_date})")
    if len(nav_data) > 20:
        nav_data_df = nav_data.copy()
        nav_data_df['SMA_5'] = nav_data_df['NAV'].rolling(window=5).mean()
        nav_data_df['SMA_20'] = nav_data_df['NAV'].rolling(window=20).mean()

        last_sma_5 = nav_data_df['SMA_5'].iloc[-1]
        last_sma_20 = nav_data_df['SMA_20'].iloc[-1]
        last_nav = nav_data_df['NAV'].iloc[-1]
        prev_nav = nav_data_df['NAV'].iloc[-2]

        col1, col2, col3 = st.columns(3)
        if last_sma_5 < last_sma_20 and last_nav < prev_nav:
            dip_probability, signal_text, signal_color = "High", "CAUTION", "red"
            reason = "Short-term momentum is negative."
        else:
            dip_probability, signal_text, signal_color = "Low", "STABLE", "green"
            reason = "Short-term momentum is stable or positive."

        with col1: st.metric("Next-Day Dip Probability", dip_probability)
        with col2: st.markdown(f"## <span style='color:{signal_color};'>Signal: {signal_text}</span>", unsafe_allow_html=True)
        with col3: st.info(f"**Reasoning:** {reason}")
    else:
        st.warning("Not enough data for a daily signal (requires >20 data points).")

    # --- Historical Data Chart with Time Filters ---
    st.subheader("Historical Fund Performance (NAV)")

    # NEW: Time period selection
    time_period = st.radio(
        "Select Graph Period:",
        ('1M', '1Y', '3Y', '5Y', 'Overall'),
        index=4, # Default selection is 'Overall'
        horizontal=True,
    )

    # Filter data based on selection
    today = pd.Timestamp.now()
    data_to_plot = nav_data.copy()

    if time_period == '1M':
        data_to_plot = nav_data[nav_data.index >= (today - pd.DateOffset(months=1))]
    elif time_period == '1Y':
        data_to_plot = nav_data[nav_data.index >= (today - pd.DateOffset(years=1))]
    elif time_period == '3Y':
        data_to_plot = nav_data[nav_data.index >= (today - pd.DateOffset(years=3))]
    elif time_period == '5Y':
        data_to_plot = nav_data[nav_data.index >= (today - pd.DateOffset(years=5))]

    # Display chart with the filtered data
    if not data_to_plot.empty:
        st.line_chart(data_to_plot['NAV'])
    else:
        st.warning(f"No data available for the selected '{time_period}' period in the uploaded file.")

else:
    st.info("Upload a CSV file to begin analysis.")
