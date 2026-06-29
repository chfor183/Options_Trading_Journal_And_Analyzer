import streamlit as st

st.set_page_config(page_title="Research References", page_icon="🔍", layout="wide")
st.title("Research References")

# Use 3 columns to make the layout compact
col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.subheader("📈 Ticker Research")
        ticker = st.text_input("Enter Ticker Symbol:", value="TSLA", label_visibility="collapsed", placeholder="Enter Ticker (e.g. TSLA)").strip().upper()
        
        if ticker:
            lower_ticker = ticker.lower()
            ticker_links = [
                ("Barchart.com", f"https://www.barchart.com/stocks/quotes/{ticker}/overview"),
                ("Marketbeat.com", f"https://www.marketbeat.com/stocks/NASDAQ/{ticker}/"),
                ("Tipranks.com", f"https://www.tipranks.com/stocks/{lower_ticker}"),
                ("Stockanalysis.com", f"https://stockanalysis.com/stocks/{lower_ticker}/"),
                ("Finance.yahoo.com", f"https://finance.yahoo.com/quote/{ticker}/"),
                ("Optioncharts.io", f"https://optioncharts.io/options/{ticker}")
            ]
            
            for name, url in ticker_links:
                st.markdown(f"**<a href='{url}' target='_blank' style='text-decoration: none;'>🔗 {name}</a>**", unsafe_allow_html=True)

with col2:
    with st.container(border=True):
        st.subheader("🛠️ Tools")
        st.markdown("**<a href='https://simplywall.st/dashboard' target='_blank' style='text-decoration: none;'>🔗 Simply Wall St Dashboard</a>**", unsafe_allow_html=True)
        st.markdown("**<a href='https://optionstrat.com/' target='_blank' style='text-decoration: none;'>🔗 OptionStrat</a>**", unsafe_allow_html=True)
        st.markdown("**<a href='https://www.optionsprofitcalculator.com/' target='_blank' style='text-decoration: none;'>🔗 Options Profit Calculator</a>**", unsafe_allow_html=True)
        st.markdown("**<a href='https://www.dataroma.com/m/home.php' target='_blank' style='text-decoration: none;'>🔗 Dataroma</a>**", unsafe_allow_html=True)
        st.markdown("**<a href='https://www.tradinghours.com/markets/nyse' target='_blank' style='text-decoration: none;'>🔗 Trading Hours</a>**", unsafe_allow_html=True)
        st.markdown("**<a href='https://finviz.com/map?t=geo' target='_blank' style='text-decoration: none;'>🔗 Finviz Map</a>**", unsafe_allow_html=True)

    with st.container(border=True):
        st.subheader("🎭 Sentiment")
        st.markdown("**<a href='https://www.cnn.com/markets/fear-and-greed' target='_blank' style='text-decoration: none;'>🔗 CNN Fear and Greed</a>**", unsafe_allow_html=True)
        st.markdown("**<a href='https://www.aaii.com/sentiment-survey' target='_blank' style='text-decoration: none;'>🔗 AAII Sentiment Survey</a>**", unsafe_allow_html=True)
        st.markdown("**<a href='https://truflation.com/indexes' target='_blank' style='text-decoration: none;'>🔗 Truflation</a>**", unsafe_allow_html=True)
        st.markdown("**<a href='https://www.currentmarketvaluation.com/' target='_blank' style='text-decoration: none;'>🔗 Current Market Valuation</a>**", unsafe_allow_html=True)

with col3:
    with st.container(border=True):
        st.subheader("📰 News")
        st.markdown("**<a href='https://ground.news/' target='_blank' style='text-decoration: none;'>🔗 Ground News</a>**", unsafe_allow_html=True)
        st.markdown("**<a href='https://www.nbcnews.com/' target='_blank' style='text-decoration: none;'>🔗 NBC News</a>**", unsafe_allow_html=True)
        st.markdown("**<a href='https://www.cnbc.com/' target='_blank' style='text-decoration: none;'>🔗 CNBC</a>**", unsafe_allow_html=True)

    with st.container(border=True):
        st.subheader("🔎 Screener")
        st.markdown("**<a href='https://finviz.com/screener' target='_blank' style='text-decoration: none;'>🔗 Finviz Screener</a>**", unsafe_allow_html=True)

    with st.container(border=True):
        st.subheader("💰 Earning")
        st.markdown("**<a href='https://earningshub.com/earnings-calendar/this-week' target='_blank' style='text-decoration: none;'>🔗 Earnings Hub</a>**", unsafe_allow_html=True)

    with st.container(border=True):
        st.subheader("🪙 Crypto")
        st.markdown("**<a href='https://www.coingecko.com/' target='_blank' style='text-decoration: none;'>🔗 CoinGecko</a>**", unsafe_allow_html=True)
