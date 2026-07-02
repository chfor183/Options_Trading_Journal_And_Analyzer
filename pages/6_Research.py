import streamlit as st

st.set_page_config(page_title="Research References", page_icon="🔍", layout="wide")

# Custom CSS to reduce spacing, margins, and container padding
st.markdown("""
<style>
    /* Reduce padding between streamlit components */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1.5rem !important;
    }
    div[data-testid="stVerticalBlock"] > div {
        padding-bottom: 0px !important;
    }
    /* Style container headers and items for maximum compactness */
    .compact-header {
        font-size: 1.15rem !important;
        font-weight: bold;
        margin-bottom: 6px !important;
        margin-top: 0px !important;
    }
    .link-item {
        margin-bottom: 2px !important;
        font-size: 0.95rem !important;
        font-weight: bold !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("Research References")

# Use 3 columns to make the layout compact
col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown('<div class="compact-header">📈 Ticker Research</div>', unsafe_allow_html=True)
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
                st.markdown(f"<div class='link-item'><a href='{url}' target='_blank' style='text-decoration: none;'>🔗 {name}</a></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="compact-header">📊 Technical Analysis</div>', unsafe_allow_html=True)
        st.markdown("<div class='link-item'><a href='https://www.tradingview.com/' target='_blank' style='text-decoration: none;'>🔗 TradingView</a></div>", unsafe_allow_html=True)
        st.markdown("<div class='link-item'><a href='https://www.tradingview.com/chart/' target='_blank' style='text-decoration: none;'>🔗 TradingView Charts</a></div>", unsafe_allow_html=True)
        st.markdown("<div class='link-item'><a href='https://www.tradingview.com/heatmap/stock' target='_blank' style='text-decoration: none;'>🔗 TradingView Stock Heatmap</a></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="compact-header">🔎 Screener</div>', unsafe_allow_html=True)
        st.markdown("<div class='link-item'><a href='https://finviz.com/screener' target='_blank' style='text-decoration: none;'>🔗 Finviz Screener</a></div>", unsafe_allow_html=True)

with col2:
    with st.container(border=True):
        st.markdown('<div class="compact-header">🛠️ Tools</div>', unsafe_allow_html=True)
        st.markdown("<div class='link-item'><a href='https://simplywall.st/dashboard' target='_blank' style='text-decoration: none;'>🔗 Simply Wall St</a></div>", unsafe_allow_html=True)
        st.markdown("<div class='link-item'><a href='https://streetstats.finance/' target='_blank' style='text-decoration: none;'>🔗 StreetStats</a></div>", unsafe_allow_html=True)
        st.markdown("<div class='link-item'><a href='https://optionstrat.com/' target='_blank' style='text-decoration: none;'>🔗 OptionStrat</a></div>", unsafe_allow_html=True)
        st.markdown("<div class='link-item'><a href='https://www.optionsprofitcalculator.com/' target='_blank' style='text-decoration: none;'>🔗 Options Profit Calculator</a></div>", unsafe_allow_html=True)
        st.markdown("<div class='link-item'><a href='https://www.dataroma.com/m/home.php' target='_blank' style='text-decoration: none;'>🔗 Dataroma</a></div>", unsafe_allow_html=True)
        st.markdown("<div class='link-item'><a href='https://www.tradinghours.com/markets/nyse' target='_blank' style='text-decoration: none;'>🔗 Trading Hours</a></div>", unsafe_allow_html=True)
        st.markdown("<div class='link-item'><a href='https://finviz.com/map?t=geo' target='_blank' style='text-decoration: none;'>🔗 Finviz Map</a></div>", unsafe_allow_html=True)
        st.markdown("<div class='link-item'><a href='https://www.tradingview.com/yield-curves/' target='_blank' style='text-decoration: none;'>🔗 TradingView Yield Curves</a></div>", unsafe_allow_html=True)
        st.markdown("<div class='link-item'><a href='https://www.tradingview.com/options/chain' target='_blank' style='text-decoration: none;'>🔗 TradingView Options Chain</a></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="compact-header">🎭 Sentiment</div>', unsafe_allow_html=True)
        st.markdown("<div class='link-item'><a href='https://www.cnn.com/markets/fear-and-greed' target='_blank' style='text-decoration: none;'>🔗 CNN Fear & Greed</a></div>", unsafe_allow_html=True)
        st.markdown("<div class='link-item'><a href='https://www.aaii.com/sentiment-survey' target='_blank' style='text-decoration: none;'>🔗 AAII Survey</a></div>", unsafe_allow_html=True)
        st.markdown("<div class='link-item'><a href='https://truflation.com/indexes' target='_blank' style='text-decoration: none;'>🔗 Truflation</a></div>", unsafe_allow_html=True)
        st.markdown("<div class='link-item'><a href='https://www.currentmarketvaluation.com/' target='_blank' style='text-decoration: none;'>🔗 Current Market Valuation</a></div>", unsafe_allow_html=True)

with col3:
    with st.container(border=True):
        st.markdown('<div class="compact-header">📰 News</div>', unsafe_allow_html=True)
        st.markdown("<div class='link-item'><a href='https://ground.news/' target='_blank' style='text-decoration: none;'>🔗 Ground News</a></div>", unsafe_allow_html=True)
        st.markdown("<div class='link-item'><a href='https://www.nbcnews.com/' target='_blank' style='text-decoration: none;'>🔗 NBC News</a></div>", unsafe_allow_html=True)
        st.markdown("<div class='link-item'><a href='https://www.cnbc.com/' target='_blank' style='text-decoration: none;'>🔗 CNBC</a></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="compact-header">🎥 YouTube</div>', unsafe_allow_html=True)
        st.markdown("<div class='link-item'><a href='https://www.youtube.com/@TheDavidLinReport' target='_blank' style='text-decoration: none;'>🔗 David Lin Report</a></div>", unsafe_allow_html=True)
        st.markdown("<div class='link-item'><a href='https://www.youtube.com/@Click-Capital' target='_blank' style='text-decoration: none;'>🔗 Click Capital</a></div>", unsafe_allow_html=True)
        st.markdown("<div class='link-item'><a href='https://www.youtube.com/@DividendTalks' target='_blank' style='text-decoration: none;'>🔗 Dividend Talks</a></div>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="compact-header">💰 Earnings</div>', unsafe_allow_html=True)
        st.markdown("<div class='link-item'><a href='https://earningshub.com/earnings-calendar/this-week' target='_blank' style='text-decoration: none;'>🔗 Earnings Hub</a></div>", unsafe_allow_html=True)
