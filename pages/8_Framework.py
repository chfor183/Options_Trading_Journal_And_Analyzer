import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Investment Framework", page_icon="🧠", layout="wide")
st.title("🧠 Investment Framework")

tabs = st.tabs(["📋 Analysis Checklists", "💰 Allocation & Notes", "⚖️ Rules & Mindset", "🧠 Psychology & Takeaways"])

with tabs[0]:
    st.subheader("🔍 Interactive Investment Checklists")
    st.write("Use these interactive, state-preserving checklists to audit trade setups before committing capital.")
    
    # Callback functions to reset session state keys for each checkbox group
    def uncheck_etf():
        for key in ["etf_ta1", "etf_ta2", "etf_ta3", "etf_rsi", "etf_bb", "etf_wma", "etf_sma", "etf_st", "etf_sent", "etf_breadth", "etf_vix", "etf_seas", "etf_fomc", "etf_cpi", "etf_unemp", "etf_friday", "etf_geo"]:
            st.session_state[key] = False

    def uncheck_company():
        for key in ["comp_f1", "comp_f2", "comp_f3", "comp_f4", "comp_ta1", "comp_ta2", "comp_ta3", "comp_rsi", "comp_bb", "comp_wma", "comp_sma", "comp_st", "comp_news", "comp_macro", "comp_revisions"]:
            st.session_state[key] = False

    def set_section_state(keys, value):
        for key in keys:
            st.session_state[key] = value

    # Define checklist keys for scoring and state tracking
    etf_keys = ["etf_ta1", "etf_ta2", "etf_ta3", "etf_rsi", "etf_bb", "etf_wma", "etf_sma", "etf_st", "etf_sent", "etf_breadth", "etf_vix", "etf_seas", "etf_fomc", "etf_cpi", "etf_unemp", "etf_friday", "etf_geo"]
    comp_keys = ["comp_f1", "comp_f2", "comp_f3", "comp_f4", "comp_ta1", "comp_ta2", "comp_ta3", "comp_rsi", "comp_bb", "comp_wma", "comp_sma", "comp_st", "comp_news", "comp_macro", "comp_revisions"]

    etf_score = sum([st.session_state.get(k, False) for k in etf_keys])
    etf_total = len(etf_keys)
    etf_progress = etf_score / etf_total

    comp_score = sum([st.session_state.get(k, False) for k in comp_keys])
    comp_total = len(comp_keys)
    comp_progress = comp_score / comp_total

    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            col_title, col_btn = st.columns([2, 1])
            col_title.markdown("### 🗺️ ETF Analysis")
            col_btn.button("Uncheck all", key="uncheck_etf_btn", on_click=uncheck_etf, use_container_width=True)
            
            # Progress and Score metrics displayed prominently at the top
            st.progress(etf_progress)
            st.metric("ETF Checklist Score", f"{etf_score} / {etf_total}", delta=f"{int(etf_progress*100)}% Complete")
            st.write("---")
            
            # Use collapsed expanders to keep the checklists vertically compact!
            with st.expander("📈 1. Technical Analysis", expanded=False):
                sec_keys_etf_ta = ["etf_ta1", "etf_ta2", "etf_ta3"]
                btn_c1, btn_c2 = st.columns(2)
                btn_c1.button("Check section", key="chk_sec_etf_ta", on_click=set_section_state, args=(sec_keys_etf_ta, True), use_container_width=True)
                btn_c2.button("Uncheck section", key="unchk_sec_etf_ta", on_click=set_section_state, args=(sec_keys_etf_ta, False), use_container_width=True)
                
                etf_ta1 = st.checkbox("Weekly Heikin Ashi Trend & Daily Candles Price Action", key="etf_ta1")
                etf_ta2 = st.checkbox("Volume accumulation and distribution", key="etf_ta2")
                etf_ta3 = st.checkbox("Horizontal Support & Resistance Swing Zones Mapped", key="etf_ta3")
            
            with st.expander("🔬 2. Core Technical Indicators Status", expanded=False):
                sec_keys_etf_ind = ["etf_rsi", "etf_bb", "etf_wma", "etf_sma", "etf_st"]
                btn_c1, btn_c2 = st.columns(2)
                btn_c1.button("Check section", key="chk_sec_etf_ind", on_click=set_section_state, args=(sec_keys_etf_ind, True), use_container_width=True)
                btn_c2.button("Uncheck section", key="unchk_sec_etf_ind", on_click=set_section_state, args=(sec_keys_etf_ind, False), use_container_width=True)

                etf_rsi = st.checkbox("RSI (14) audited (Overbought >70 / Oversold <30)", key="etf_rsi")
                etf_bb = st.checkbox("Bollinger Bands (20, 2SD) extremes or squeeze checked", key="etf_bb")
                etf_wma = st.checkbox("WMA 50 checked for mid-term trend support/resistance", key="etf_wma")
                etf_sma = st.checkbox("SMA 200 checked for long-term institutional trend direction", key="etf_sma")
                etf_st = st.checkbox("Supertrend (10, 1, 1) execution signal confirmed", key="etf_st")
                
            with st.expander("📊 3. Macro Sentiment & Breadth", expanded=False):
                sec_keys_etf_macro = ["etf_sent", "etf_breadth", "etf_vix", "etf_seas"]
                btn_c1, btn_c2 = st.columns(2)
                btn_c1.button("Check section", key="chk_sec_etf_macro", on_click=set_section_state, args=(sec_keys_etf_macro, True), use_container_width=True)
                btn_c2.button("Uncheck section", key="unchk_sec_etf_macro", on_click=set_section_state, args=(sec_keys_etf_macro, False), use_container_width=True)

                etf_sent = st.checkbox("Sentiment indexes & Put-Call ratios", key="etf_sent")
                etf_breadth = st.checkbox("Market Breadth (% of stocks above 50/200 SMA) checked", key="etf_breadth")
                etf_vix = st.checkbox("VIX Volatility Index checked", key="etf_vix")
                etf_seas = st.checkbox("Historical monthly/quarterly Seasonality checked", key="etf_seas")
            
            with st.expander("📅 4. Key Macro Catalyst Schedule", expanded=False):
                sec_keys_etf_cat = ["etf_fomc", "etf_cpi", "etf_unemp", "etf_friday", "etf_geo"]
                btn_c1, btn_c2 = st.columns(2)
                btn_c1.button("Check section", key="chk_sec_etf_cat", on_click=set_section_state, args=(sec_keys_etf_cat, True), use_container_width=True)
                btn_c2.button("Uncheck section", key="unchk_sec_etf_cat", on_click=set_section_state, args=(sec_keys_etf_cat, False), use_container_width=True)

                etf_fomc = st.checkbox("FOMC Meetings & Interest Rate decisions checked", key="etf_fomc")
                etf_cpi = st.checkbox("Inflation (CPI/PCI US) & economic calendar schedule checked", key="etf_cpi")
                etf_unemp = st.checkbox("Unemployment rates & Jobs report timeline checked", key="etf_unemp")
                etf_friday = st.checkbox("Options Friday (3rd Friday of the month) expiration risks checked", key="etf_friday")
                etf_geo = st.checkbox("Global political climate & war developments audited", key="etf_geo")
            
    with col2:
        with st.container(border=True):
            col_title2, col_btn2 = st.columns([2, 1])
            col_title2.markdown("### 🏢 Company Analysis")
            col_btn2.button("Uncheck all", key="uncheck_comp_btn", on_click=uncheck_company, use_container_width=True)
            
            # Progress and Score metrics displayed prominently at the top
            st.progress(comp_progress)
            st.metric("Company Checklist Score", f"{comp_score} / {comp_total}", delta=f"{int(comp_progress*100)}% Complete")
            st.write("---")
            
            # Use collapsed expanders to keep the checklists vertically compact!
            with st.expander("📊 1. Fundamental Analysis", expanded=False):
                sec_keys_comp_fund = ["comp_f1", "comp_f2", "comp_f3", "comp_f4"]
                btn_c1, btn_c2 = st.columns(2)
                btn_c1.button("Check section", key="chk_sec_comp_fund", on_click=set_section_state, args=(sec_keys_comp_fund, True), use_container_width=True)
                btn_c2.button("Uncheck section", key="unchk_sec_comp_fund", on_click=set_section_state, args=(sec_keys_comp_fund, False), use_container_width=True)

                comp_f1 = st.checkbox("Earnings History (EPS & Revenue growth / Surprises audited)", key="comp_f1")
                comp_f2 = st.checkbox("Forward Guidance (Capex outlook, revisions, sector guidance)", key="comp_f2")
                comp_f3 = st.checkbox("Balance Sheet Health (Debt-to-Equity & Current ratios)", key="comp_f3")
                comp_f4 = st.checkbox("Operating Metrics (Gross/Operating/Net margins & FCF Yield)", key="comp_f4")
            
            with st.expander("📈 2. Technical Analysis", expanded=False):
                sec_keys_comp_ta = ["comp_ta1", "comp_ta2", "comp_ta3"]
                btn_c1, btn_c2 = st.columns(2)
                btn_c1.button("Check section", key="chk_sec_comp_ta", on_click=set_section_state, args=(sec_keys_comp_ta, True), use_container_width=True)
                btn_c2.button("Uncheck section", key="unchk_sec_comp_ta", on_click=set_section_state, args=(sec_keys_comp_ta, False), use_container_width=True)

                comp_ta1 = st.checkbox("Weekly Heikin Ashi Trend & Daily Candles Price Action", key="comp_ta1")
                comp_ta2 = st.checkbox("Volume accumulation and distribution", key="comp_ta2")
                comp_ta3 = st.checkbox("Horizontal Support & Resistance Swing Zones Mapped", key="comp_ta3")
            
            with st.expander("🔬 3. Core Technical Indicators Status", expanded=False):
                sec_keys_comp_ind = ["comp_rsi", "comp_bb", "comp_wma", "comp_sma", "comp_st"]
                btn_c1, btn_c2 = st.columns(2)
                btn_c1.button("Check section", key="chk_sec_comp_ind", on_click=set_section_state, args=(sec_keys_comp_ind, True), use_container_width=True)
                btn_c2.button("Uncheck section", key="unchk_sec_comp_ind", on_click=set_section_state, args=(sec_keys_comp_ind, False), use_container_width=True)

                comp_rsi = st.checkbox("RSI (14) audited (Overbought >70 / Oversold <30)", key="comp_rsi")
                comp_bb = st.checkbox("Bollinger Bands (20, 2SD) extremes or squeeze checked", key="comp_bb")
                comp_wma = st.checkbox("WMA 50 checked for mid-term trend support/resistance", key="comp_wma")
                comp_sma = st.checkbox("SMA 200 checked for long-term institutional trend direction", key="comp_sma")
                comp_st = st.checkbox("Supertrend (10, 1, 1) execution signal confirmed", key="comp_st")
                
            with st.expander("📅 4. Catalyst Checks", expanded=False):
                sec_keys_comp_cat = ["comp_news", "comp_macro", "comp_revisions"]
                btn_c1, btn_c2 = st.columns(2)
                btn_c1.button("Check section", key="chk_sec_comp_cat", on_click=set_section_state, args=(sec_keys_comp_cat, True), use_container_width=True)
                btn_c2.button("Uncheck section", key="unchk_sec_comp_cat", on_click=set_section_state, args=(sec_keys_comp_cat, False), use_container_width=True)

                comp_news = st.checkbox("Recent corporate developments, leadership shifts, legal actions, and PR reports", key="comp_news")
                comp_macro = st.checkbox("Sector Rotations, industry-specific developments, and cycle stage audited", key="comp_macro")
                comp_revisions = st.checkbox("Financial target revisions, earnings guidance adjustments, or analyst consensus updates", key="comp_revisions")

with tabs[1]:
    st.subheader("💵 Portfolio & Capital Allocation")
    
    st.markdown("""
    | Capital Tier | Primary Option Strategy | Tactical Note |
    | :--- | :--- | :--- |
    | **\\$3,000 - \\$10,000** | Spreads + Short Iron Condor | **Credit > Debit**: Selling premium harnesses high-odds win rates through extrinsic value farming. |
    | **\\$10,000 - \\$30,000** | Add Buying LEAPS | Utilize naked or spreads depending on available margin to gain leveraged directional exposure. |
    | **\\$30,000 - \\$50,000** | Add Sell Cash-Secured Puts | Sell CSPs on high-quality companies; acquire the underlying stock if it closes In-The-Money (ITM) and you want ownership. |
    | **\\$50,000 - \\$100,000** | Add Sell Covered Calls | Complete the loop (Wheel Strategy) by selling covered calls on stock positions if it moves ITM and you wish to exit. |
    | **\\$100,000+** | Diversify + Dividends + DCA + Buy the Dip | Consolidate wealth. Add dollar-cost averaging, blue-chip dividends, and dynamic risk management. |
    """)
    
    st.write("")
    st.markdown("### 📌 Key Strategic Notes")
    st.markdown("""
    - **Note 1 :** Together, selling cash-secured puts and selling covered calls forms **The Wheel Strategy** (efficient yield generation on stocks you are happy to own long-term).
    - **Note 2 :** Always keep a fraction of capital reserved for: **medium-to-high risk plays** and/or **liquidity** to strike on outstanding market opportunities.
    - **Note 3 :** You can always experiment with speculative option strategies or new plays, but keep allocation restricted to <span style="font-size: 1.3em;">**less than 10% of total capital for the total of those strategies.**</span>
    - **Note 4 : ⚠️ POSITION SIZING is the ultimate key to survival in the markets!** Never risk too much on any single trade or ticker. Keep allocation to <span style="font-size: 1.3em;">**less than 5% of total capital per trade.**</span> The probability of profit and good research will do the rest.
    """, unsafe_allow_html=True)

with tabs[2]:
    st.subheader("⚖️ Rules & Mindset")
    
    col_r1, col_r2 = st.columns(2)
    
    with col_r1:
        with st.container(border=True):
            st.markdown("### 📜 Core Trading Rules")
            st.markdown("""
            - **Rule #1: Know what you are doing and why you are doing it.**
              - Never copy a play blindly. Make sure you understand the trade mechanics, entry setup, contract terms, and structural thesis.
            - **Rule #2: Be ready for every market move and know what to do in advance.**
              - Map out your adjustment strategies (hedges, rolls, take-profit triggers, stop-losses) *before* committing capital. No panic decisions.
            - **Rule #3: Set yourself clear goals and boundaries.**
              - Identify standard profit targets (e.g., 50% max profit on credit spreads) and maximum tolerable drawdown boundaries.
            """)
            
            with st.container(border=True):
                st.markdown("### 💬 Words to Live By")
                st.markdown("""
                * **When in doubt, test.** Put the strategy in a paper account or run backtests first.
                * **Look at what most people know to search for consensus.** Contrast general consensus with institutional flow.
                * **Simple is always better (first principles).** Avoid overly complex multi-tier adjustments; focus on liquidity, trend, and position sizing.
                * **Always be objective about the market and companies.** Block out emotional bias; charts and books do not care about your beliefs.
                * **Don't lose money (proper risk management).** Preserve capital first; performance yields will compound naturally.
                * **Follow trends, price action, mean reversal, and gap fills.** Trade the actual market setup in front of you, not the hypothetical scenario you want.
                * **⚠️ THE MOST DANGEROUS WORDS IN FINANCE:** *"This time it's different."*
                """)
                
    with col_r2:
        with st.container(border=True):
            st.markdown("### 🧠 The Trader Mindset")
            st.markdown("""
            * **Market Non-Action:** If nothing notable is developing on the tape, follow the main trend or don't deploy capital at all. Preserving liquidity is a position.
            * **Why the stock market always goes up in the long run:**
              - Perpetual fiat inflation eroding purchasing power.
              - Multi-tier central interest rate management.
              - Constant flow of passive pressure from index funds and ETFs.
              - Continuous productivity and real value generated by efficient corporations.
            * **What causes markets/stocks to drop:**
              - Adverse regulatory news
              - Poor corporate performance
              - Downward price revision
              - Black swan disruptions
              - Panic speculation
              - Momentum trends
              - Institutional dark pool liquidation
              - Emotional FOMO unwinding
            """)

with tabs[3]:
    st.subheader("🧠 Psychology & Key Takeaways")
    
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        with st.container(border=True):
            st.markdown("### 🎭 Cognitive Biases to Guard Against")
            st.markdown("""
            1. **Confirmation Bias:**
               - Seeking only news and data that confirm your existing trade thesis while ignoring glaring negative signals.
            2. **Loss Aversion (Prospect Theory):**
               - The pain of losing \\$100 is felt twice as intensely as the joy of making $100. This leads traders to hold losing trades too long (hoping to break even) and cutting winners too early.
            3. **Recency Bias:**
               - Overweighting the importance of recent market actions (e.g., a 3-day drop) and losing track of the larger long-term structural trends.
            4. **Anchoring Bias:**
               - Getting stuck on a company's past peak stock price or your specific purchase price as the absolute 'fair value' rather than looking at current performance.
            5. **Overconfidence & Illusion of Control:**
               - Attributing lucky wins in a bull market to absolute personal trading skill, leading to excessive risk-taking and oversized positioning.
            """)
            
        with st.container(border=True):
            st.markdown("### 📖 The Intelligent Investor - Key Takeaways")
            st.markdown("""
            - **Mr. Market (The Emotional Business Partner):**
              - Treat the market as an emotional business partner who offers to buy or sell stakes every day at wild price swings. Capitalize on his erratic moods rather than falling under his influence.
            - **Investment vs. Speculation:**
              - An investment operation is one which, upon thorough analysis, promises safety of principal and an adequate return. Operations not meeting these requirements are speculative.
            - **Margin of Safety:**
              - The secret of sound investment is the buffer/safety margin. Always pay significantly less than a business's intrinsic worth to absorb unforeseen operational downturns.
            - **Defensive vs. Enterprising (Aggressive) Investor:**
              - Match your active market participation time to your personal temperament. If you cannot spend hours weekly doing research, stick to a highly passive, robust index structure.
            """)
            
    with col_p2:
        with st.container(border=True):
            st.markdown("### 🏦 The Psychology of Money - Key Takeaways")
            st.markdown("""
            - **Being Rich vs. Being Wealthy:**
              - *Rich* is current income. It's visible (nice cars, luxury items). *Wealth* is the money not spent—assets, options, and investments that offer future flexibility and freedom.
            - **No One's Crazy:**
              - Your personal experiences with money dictate how you interact with the stock market. Every investor has different experiences and risk thresholds; behave according to your own long-term objectives.
            - **Getting Rich vs. Staying Rich**:
              - Getting rich requires taking calculated risks and being optimistic.
              - Staying rich requires the exact opposite: humility, frugality, and the paranoia that what you made can be taken away just as fast.
            - **The Power of Compounding:**
              - Outstanding investing results aren't about finding the highest returns. They are about earning consistently good returns over the longest possible uninterrupted time period.
            - **Freedom is the Ultimate Dividend:**
              - The highest value of money is its ability to give you complete control over your time. Being able to do what you want, when you want, with whom you want, is the ultimate financial goal.
            """)
