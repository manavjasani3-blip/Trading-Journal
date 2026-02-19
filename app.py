import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

st.set_page_config(page_title="Mathsuu Trader", layout="wide", initial_sidebar_state="collapsed")

# --- CSS Styling ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Poppins:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    .stApp { background-color: #050505; color: #ffffff; }
    .logo-text { font-family: 'Orbitron', sans-serif; font-size: 42px; font-weight: 700; background: linear-gradient(90deg, #9D4EDD, #00F5FF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .stButton>button { background-color: #9D4EDD; color: white; border-radius: 8px; font-weight: bold; width: 100%; transition: 0.3s;}
    .stButton>button:hover { background-color: #00F5FF; color: black; box-shadow: 0 0 15px #00F5FF;}
    div[data-testid="metric-container"] { background-color: #11131a; border: 1px solid #2d1b4e; padding: 15px; border-radius: 10px; border-left: 4px solid #00F5FF; }
    </style>
""", unsafe_allow_html=True)

# --- GOOGLE SHEETS CONNECTION (CLOUD & LOCAL) ---
@st.cache_resource
def init_connection():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    try:
        # જો વેબસાઈટ લાઈવ (Streamlit Cloud) પર હશે તો અહીંથી પાસવર્ડ લેશે
        creds_dict = json.loads(st.secrets["google_credentials"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    except Exception:
        # જો તમારા લેપટોપમાં રન કરતા હશો તો ફાઈલ માંથી લેશે
        creds = ServiceAccountCredentials.from_json_keyfile_name('secrets.json', scope)
        
    client = gspread.authorize(creds)
    return client.open("Mathsuu_Trader_DB").sheet1

try:
    sheet = init_connection()
except Exception as e:
    st.error("⚠️ ગૂગલ શીટ કનેક્શન એરર. પાસવર્ડ સેટિંગ્સ ચેક કરો.")
    st.stop()

# --- 1. LOGIN SYSTEM ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="logo-text" style="text-align: center;">⚡ Mathsuu Trader</div>', unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #A0AEC0;'>Login to access your personalized journal</p>", unsafe_allow_html=True)
        with st.form("login_form"):
            name = st.text_input("Trader Name (e.g., Manav)")
            submit = st.form_submit_button("Secure Login 🚀")
            if submit and name != "":
                st.session_state.logged_in = True
                st.session_state.username = name
                st.rerun()
else:
    # --- 2. MAIN APP ---
    st.sidebar.success(f"🟢 Active User: {st.session_state.username}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    st.markdown('<div class="logo-text">⚡ Mathsuu Trader</div>', unsafe_allow_html=True)
    
    # --- Fetch Real Data from Google Sheets ---
    data = sheet.get_all_records()
    df_all = pd.DataFrame(data)
    
    if not df_all.empty and 'Trader_Name' in df_all.columns:
        df = df_all[df_all['Trader_Name'] == st.session_state.username].copy()
        if not df.empty:
            df['Actual_PnL'] = pd.to_numeric(df['Actual_PnL'], errors='coerce').fillna(0)
    else:
        df = pd.DataFrame()

    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📝 Add Trade & Rules", "🧠 AI Analytics"])

    # --- TAB 1: DASHBOARD ---
    with tab1:
        dash_page1, dash_page2, dash_page3 = st.tabs(["1️⃣ Overview & Stats", "2️⃣ Charts & Analysis", "3️⃣ Trade List"])
        
        with dash_page1:
            st.markdown("### 📈 Overall Statistics")
            if not df.empty:
                total_pnl = df['Actual_PnL'].sum()
                total_trades = len(df)
                wins = len(df[df['Result'] == 'Win'])
                win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
                biggest_win = df['Actual_PnL'].max()
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Total P&L", f"₹{total_pnl:,.2f}")
                c2.metric("Total Trades", f"{total_trades}")
                c3.metric("Biggest Win", f"₹{biggest_win:,.2f}")
                c4.metric("Win Rate", f"{win_rate:.1f}%")
            else:
                st.info("No trades found. Please add your first trade!")

        with dash_page2:
            st.markdown("### 📊 Visual Analysis")
            if not df.empty:
                fig = px.bar(df, x='Date', y='Actual_PnL', color='Result', 
                             color_discrete_map={'Win': '#00F5FF', 'Loss': '#FF0055', 'Breakeven': '#8892B0'},
                             template="plotly_dark", title="P&L Over Time")
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Not enough data to generate charts.")

        with dash_page3:
            st.markdown("### 📜 Detailed Trade List")
            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No data available.")

    # --- TAB 2: ADD TRADE & RULES ---
    with tab2:
        st.markdown("### 📝 Log Your Real Trade Details")
        with st.form("new_trade_form"):
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                trade_date = st.date_input("Date")
                symbol = st.text_input("Symbol (e.g. RELIANCE)")
                trade_type = st.selectbox("Trade Type", ["Long", "Short"])
                strategy = st.text_input("Strategy Used")
            with col_b:
                quantity = st.number_input("Quantity", min_value=1, value=10)
                entry_price = st.number_input("Entry Price", min_value=0.0, format="%.2f")
                exit_price = st.number_input("Exit Price", min_value=0.0, format="%.2f")
                result = st.selectbox("Trade Result", ["Win", "Loss", "Breakeven"])
            with col_c:
                sl_risk = st.number_input("Stoploss Risk Amount (₹)", min_value=0.0)
                target_rr = st.selectbox("Planned Target (RR)", ["1:1", "1:2", "1:3", "1:4", "1:5+"])
                actual_pnl = st.number_input("Actual P&L Booked (₹)", value=0.0)
            
            st.markdown("#### ✅ Psychology & Rules Checklist")
            r_col1, r_col2 = st.columns(2)
            with r_col1:
                r1 = st.checkbox("1. Strictly followed Stoploss")
                r2 = st.checkbox("2. Held trade until Target or SL")
            with r_col2:
                r3 = st.checkbox("3. Perfect Entry (No FOMO)")
                r4 = st.checkbox("4. Did NOT Overtrade today")
            
            submitted = st.form_submit_button("Save Trade to My Database")
            
            if submitted:
                rules = []
                if r1: rules.append("Strict SL")
                if r2: rules.append("Patience")
                if r3: rules.append("Perfect Entry")
                if r4: rules.append("No Overtrade")
                rules_str = ", ".join(rules) if rules else "No Rules Followed"
                
                new_row = [str(trade_date), st.session_state.username, symbol, trade_type, 
                           strategy, quantity, entry_price, exit_price, result, sl_risk, 
                           target_rr, actual_pnl, rules_str]
                
                with st.spinner("Saving to Google Sheets..."):
                    sheet.append_row(new_row)
                st.success(f"✅ Trade saved for {st.session_state.username}!")
                st.rerun()

    # --- TAB 3: AI ANALYTICS ---
    with tab3:
        st.markdown(f"### 🧠 AI Mentor for {st.session_state.username}")
        if not df.empty:
            if st.button("Generate My AI Analysis"):
                with st.spinner("AI is analyzing your journal..."):
                    st.markdown(f"""
                    <div style='background-color: #1a0b2e; padding: 20px; border-radius: 10px; border-left: 5px solid #FF0055;'>
                        <h4>⚠️ Psychology Alert for {st.session_state.username}</h4>
                        <p>Focus on the 'Rules Followed' column. If 'Patience' is missing frequently, you are exiting trades too early due to fear.</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Please add some trades first so AI can analyze them.")

    st.markdown('<div style="position: fixed; bottom: 15px; right: 25px; font-family: Orbitron; color: #8892B0;">Created by <span style="color:#00F5FF;">manavjasani</span></div>', unsafe_allow_html=True)