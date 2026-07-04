import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime, timedelta
import math
from fpdf import FPDF, XPos, YPos
from src.db import SessionLocal
from src.models import Trade

st.set_page_config(page_title="Export", page_icon="📄", layout="wide")
st.title("Export")

# Inject custom CSS styles for PDF and CSV download buttons
components.html("""
<script>
const observer = new MutationObserver(() => {
    const parentDoc = window.parent.document;
    
    if (!parentDoc.getElementById('custom-export-styles')) {
        const styleEl = parentDoc.createElement('style');
        styleEl.id = 'custom-export-styles';
        styleEl.textContent = `
            .btn-pdf-report {
                background-color: #1a73e8 !important;
                color: #ffffff !important;
                border: 1px solid #1a73e8 !important;
                transition: background-color 0.2s, transform 0.1s !important;
            }
            .btn-pdf-report:hover {
                background-color: #1557b0 !important;
                border-color: #1557b0 !important;
                cursor: pointer !important;
            }
            .btn-pdf-report p {
                color: #ffffff !important;
            }
            .btn-csv-report {
                background-color: #2e7d32 !important;
                color: #ffffff !important;
                border: 1px solid #2e7d32 !important;
                transition: background-color 0.2s, transform 0.1s !important;
            }
            .btn-csv-report:hover {
                background-color: #1b5e20 !important;
                border-color: #1b5e20 !important;
                cursor: pointer !important;
            }
            .btn-csv-report p {
                color: #ffffff !important;
            }
        `;
        parentDoc.head.appendChild(styleEl);
    }
    
    const buttons = parentDoc.querySelectorAll('.stButton button, .stDownloadButton button');
    buttons.forEach(b => {
        const text = b.innerText.trim();
        if (text === 'Generate PDF Report') {
            b.classList.add('btn-pdf-report');
        } else if (text === 'Export CSV Report') {
            b.classList.add('btn-csv-report');
        }
    });
});
observer.observe(window.parent.document.body, {childList: true, subtree: true});
</script>
""", height=0, width=0)

def analyze_trade(trade):
    pnl = 0.0
    premium_collected = 0.0
    premium_paid = 0.0
    total_commission = 0.0
    close_date = None
    
    for tx in trade.transactions:
        total_commission += tx.commission
        if tx.action == "Open":
            pnl -= tx.price
            if tx.price > 0:
                premium_paid += tx.price
            else:
                premium_collected += abs(tx.price)
        else:
            pnl += tx.price
            if tx.price > 0:
                premium_collected += tx.price
            else:
                premium_paid += abs(tx.price)
            
            if close_date is None or tx.date > close_date:
                close_date = tx.date
                
    pnl -= total_commission
            
    return {
        "pnl": pnl,
        "premium_collected": premium_collected,
        "premium_paid": premium_paid,
        "total_commission": total_commission,
        "close_date": close_date.date() if close_date else None,
        "is_winner": pnl > 0,
        "is_loser": pnl < 0
    }

class PDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 16)
        self.cell(0, 8, 'Trade Report', 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')

    def chapter_title(self, title):
        self.set_font('helvetica', 'B', 14)
        # Give chapter titles a subtle dark blue color to stand out from text
        self.set_text_color(20, 50, 90)
        self.cell(0, 10, title, 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='L')
        self.set_text_color(0, 0, 0)
        self.ln(1)

def generate_pdf(filtered_trades, filter_info):
    pdf = PDF(orientation='L') # Landscape for wide tables
    pdf.add_page()
    
    # Subtitle for Filters
    pdf.set_font('helvetica', 'I', 10)
    pdf.set_text_color(100, 100, 100)
    filters_text = f"Filters Applied -> Ticker: {filter_info['Ticker']} | Date: {filter_info['Date']} | Status: {filter_info['Status']} | Strategy: {filter_info['Strategy']} | Debit/Credit: {filter_info.get('Debit/Credit', 'All')}"
    pdf.cell(0, 6, filters_text, 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    pdf.set_font('helvetica', '', 10)
    
    # 1. Key Metrics
    total_trades = len(filtered_trades)
    wins = 0
    losses = 0
    winning_pnls = []
    losing_pnls = []
    total_comm = 0.0
    total_prem_col = 0.0
    total_prem_paid = 0.0
    total_pnl = 0.0
    
    analyzed_data = []
    
    for t in filtered_trades:
        stats = analyze_trade(t)
        if stats["is_winner"]:
            wins += 1
            winning_pnls.append(stats["pnl"])
        if stats["is_loser"]:
            losses += 1
            losing_pnls.append(stats["pnl"])
            
        total_comm += stats["total_commission"]
        total_prem_col += stats["premium_collected"]
        total_prem_paid += stats["premium_paid"]
        total_pnl += stats["pnl"]
        
        open_tx = next((tx for tx in t.transactions if tx.action == "Open"), None)
        contracts = max((leg.quantity for leg in t.legs if leg.quantity), default=1) if t.legs else (open_tx.quantity if open_tx else 1)
        cost = -open_tx.price if open_tx else 0.0
        
        close_dates = [tx.date for tx in t.transactions if tx.action != "Open"]
        close_date_str = max(close_dates).strftime('%Y-%m-%d') if close_dates else "-"
        
        close_txs = [tx for tx in t.transactions if tx.action != "Open"]
        close_price = sum(tx.price for tx in close_txs) if close_txs else 0.0
        
        analyzed_data.append({
            "Month": t.date_opened.strftime("%b %Y"),
            "Is Winner": stats["is_winner"],
            "Is Loser": stats["is_loser"],
            "PnL": stats["pnl"],
            # Trade table data
            "Trade No": str(t.trade_number) if t.trade_number is not None else "-",
            "Ticker": t.ticker,
            "Name": t.underlying_name or "-",
            "Date Opened": t.date_opened.strftime("%Y-%m-%d"),
            "Date Closed": close_date_str,
            "Strategy": t.strategy_type or "-",
            "Exp. Direction": t.expected_direction or "-",
            "Contracts": str(contracts),
            "Cost": f"${cost:.2f}",
            "Close Price": f"${close_price:.2f}" if close_txs else "-",
            "PnL_str": f"${stats['pnl']:.2f}",
            "Comm": f"${stats['total_commission']:.2f}",
            "Status": t.status,
            "Cost_raw": cost,
            "Close_raw": close_price,
            "Comm_raw": stats["total_commission"]
        })

    batting_avg = (wins / total_trades * 100) if total_trades > 0 else 0.0
    avg_win = sum(winning_pnls) / len(winning_pnls) if winning_pnls else 0.0
    avg_loss = sum(losing_pnls) / len(losing_pnls) if losing_pnls else 0.0

    pdf.chapter_title("Key Metrics")
    metrics_text = (
        f"Total Trades: {total_trades}   |   Batting Avg: {batting_avg:.1f}%   |   Wins/Losses: {wins}/{losses}\n"
        f"Average Win: ${avg_win:.2f}   |   Average Loss: ${avg_loss:.2f}\n"
        f"Total Commission: ${total_comm:.2f}   |   Premium Collected: ${total_prem_col:.2f}   |   Premium Paid: ${total_prem_paid:.2f}\n"
        f"Net PnL: ${total_pnl:.2f}"
    )
    pdf.set_font('helvetica', '', 11)
    # Adding a light gray fill for the metrics block
    pdf.set_fill_color(245, 245, 245)
    pdf.multi_cell(0, 8, metrics_text, fill=True)
    pdf.ln(5)
    
    # 2. Detailed Breakdown by Month
    pdf.chapter_title("Detailed Breakdown - By Month")
    
    if analyzed_data:
        df = pd.DataFrame(analyzed_data)
        grouped = df.groupby("Month").agg(
            Trades=("Ticker", "count"),
            Wins=("Is Winner", "sum"),
            Losses=("Is Loser", "sum"),
            Total_PnL=("PnL", "sum"),
            Avg_Win=("PnL", lambda x: x[x > 0].mean() if len(x[x > 0]) > 0 else 0),
            Avg_Loss=("PnL", lambda x: x[x < 0].mean() if len(x[x < 0]) > 0 else 0)
        ).reset_index()
        
        grouped.fillna({
            "Trades": 0, "Wins": 0, "Losses": 0, 
            "Total_PnL": 0.0, "Avg_Win": 0.0, "Avg_Loss": 0.0
        }, inplace=True)
        
        # Table Header
        cols = ["Month", "Trades", "Batting Avg", "Wins", "Losses", "Avg Win", "Avg Loss", "Total PnL"]
        widths = [30, 20, 25, 20, 20, 30, 30, 30]
        
        pdf.set_font('helvetica', 'B', 10)
        for col, w in zip(cols, widths):
            pdf.cell(w, 8, col, 1, align='C')
        pdf.ln()
        
        pdf.set_font('helvetica', '', 10)
        for _, row in grouped.iterrows():
            b_avg = (row['Wins'] / row['Trades'] * 100) if row['Trades'] > 0 else 0.0
            
            pdf.cell(widths[0], 8, str(row['Month']), 1, align='C')
            pdf.cell(widths[1], 8, str(row['Trades']), 1, align='C')
            pdf.cell(widths[2], 8, f"{b_avg:.1f}%", 1, align='C')
            pdf.cell(widths[3], 8, str(row['Wins']), 1, align='C')
            pdf.cell(widths[4], 8, str(row['Losses']), 1, align='C')
            pdf.cell(widths[5], 8, f"${row['Avg_Win']:.2f}", 1, align='C')
            pdf.cell(widths[6], 8, f"${row['Avg_Loss']:.2f}", 1, align='C')
            pdf.cell(widths[7], 8, f"${row['Total_PnL']:.2f}", 1, align='C')
            pdf.ln()
    else:
        pdf.cell(0, 10, "No trades to display.", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.ln(5)
    
    # 3. Trades Table
    pdf.chapter_title("Trades List")
    if analyzed_data:
        cols = ["#", "Ticker", "Name", "Opened", "Closed", "Strategy", "Exp. Dir.", "Contr.", "Cost", "Close", "PnL", "Comm.", "Status"]
        # Total width roughly 277 for Landscape A4 (margins are 10mm each side)
        widths = [12, 14, 32, 19, 19, 44, 21, 11, 19, 22, 22, 13, 29]
        
        def print_trades_header():
            pdf.set_font('helvetica', 'B', 8)
            for col, w in zip(cols, widths):
                pdf.cell(w, 8, col, 1, align='C')
            pdf.ln()
            pdf.set_font('helvetica', '', 8)

        print_trades_header()
        
        def sanitize(text):
            if text is None: return "-"
            # Replace common unicode symbols manually, then ignore the rest to avoid FPDF errors
            return str(text).replace('↗', '^').replace('↘', 'v').replace('±', '+/-').replace('—', '-').replace('–', '-').encode('latin-1', 'ignore').decode('latin-1')
        
        for data in analyzed_data:
            # Check if we are near the bottom of the page (Landscape A4 height is 210mm)
            if pdf.get_y() > 180:
                pdf.add_page()
                print_trades_header()
                
            pdf.cell(widths[0], 8, sanitize(data['Trade No']), 1, align='C')
            pdf.cell(widths[1], 8, sanitize(data['Ticker'])[:8], 1, align='C')
            pdf.cell(widths[2], 8, sanitize(data['Name'])[:20], 1, align='C')
            pdf.cell(widths[3], 8, sanitize(data['Date Opened']), 1, align='C')
            pdf.cell(widths[4], 8, sanitize(data['Date Closed']), 1, align='C')
            pdf.cell(widths[5], 8, sanitize(data['Strategy'])[:26], 1, align='C')
            pdf.cell(widths[6], 8, sanitize(data['Exp. Direction'])[:15], 1, align='C')
            pdf.cell(widths[7], 8, sanitize(data['Contracts']), 1, align='C')
            pdf.cell(widths[8], 8, sanitize(data['Cost']), 1, align='C')
            pdf.cell(widths[9], 8, sanitize(data['Close Price']), 1, align='C')
            pdf.cell(widths[10], 8, sanitize(data['PnL_str']), 1, align='C')
            pdf.cell(widths[11], 8, sanitize(data['Comm']), 1, align='C')
            pdf.cell(widths[12], 8, sanitize(data['Status'])[:20], 1, align='C')
            pdf.ln()

        # Print totals row
        sum_cost = sum(d['Cost_raw'] for d in analyzed_data)
        sum_close = sum(d['Close_raw'] for d in analyzed_data)
        sum_pnl = sum(d['PnL'] for d in analyzed_data)
        sum_comm = sum(d['Comm_raw'] for d in analyzed_data)
        
        # Check if we have enough space for the totals row (Landscape A4 height is 210mm)
        if pdf.get_y() > 185:
            pdf.add_page()
            print_trades_header()
            
        pdf.set_font('helvetica', 'B', 8)
        left_width = sum(widths[:8])
        pdf.cell(left_width, 8, "Total", 1, align='R')
        pdf.cell(widths[8], 8, f"${sum_cost:.2f}", 1, align='C')
        pdf.cell(widths[9], 8, f"${sum_close:.2f}", 1, align='C')
        pdf.cell(widths[10], 8, f"${sum_pnl:.2f}", 1, align='C')
        pdf.cell(widths[11], 8, f"${sum_comm:.2f}", 1, align='C')
        pdf.cell(widths[12], 8, "", 1, align='C')
        pdf.ln()
    else:
        pdf.cell(0, 10, "No trades to display.", 0, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    return pdf.output()


def generate_csv_data(filtered_trades):
    rows = []
    for t in filtered_trades:
        stats = analyze_trade(t)
        
        # Calculate closed date
        close_dates = [tx.date for tx in t.transactions if tx.action != "Open"]
        close_date_str = max(close_dates).strftime('%Y-%m-%d') if close_dates else ""
        
        # Determine contracts
        open_tx = next((tx for tx in t.transactions if tx.action == "Open"), None)
        contracts = max((leg.quantity for leg in t.legs if leg.quantity), default=1) if t.legs else (open_tx.quantity if open_tx else 1)
        
        # Format legs
        legs_list = []
        for leg in t.legs:
            strike_str = f"{leg.strike:.2f}" if leg.strike is not None else ""
            price_str = f"{leg.price:.3f}" if leg.price is not None else ""
            delta_str = f"{leg.delta:.4f}" if leg.delta is not None else ""
            iv_str = f"{leg.iv:.2f}%" if leg.iv is not None else ""
            expiry_str = leg.expiry.strftime('%Y-%m-%d') if leg.expiry else ""
            legs_list.append(
                f"{leg.position} {leg.quantity if leg.quantity else 1} {leg.option_type} "
                f"(Strike: {strike_str}, Price: {price_str}, Delta: {delta_str}, IV: {iv_str}, Expiry: {expiry_str})"
            )
        legs_str = "; ".join(legs_list)
        
        # Format transactions
        tx_list = []
        for tx in t.transactions:
            tx_date_str = tx.date.strftime('%Y-%m-%d %H:%M:%S') if tx.date else ""
            tx_list.append(
                f"[{tx_date_str}] {tx.action} {tx.quantity} @ {tx.price:.2f} (Comm: {tx.commission:.2f})"
            )
        tx_str = "; ".join(tx_list)
        
        # Outcome
        if t.status == "Open":
            outcome = "Open"
        elif stats["is_winner"]:
            outcome = "Win"
        elif stats["is_loser"]:
            outcome = "Loss"
        else:
            outcome = "Scratch"
            
        rows.append({
            "Trade Number": t.trade_number if t.trade_number is not None else "",
            "Ticker": t.ticker,
            "Underlying Name": t.underlying_name or "",
            "Category": t.category or "",
            "Strategy Type": t.strategy_type or "",
            "Expected Direction": t.expected_direction or "",
            "Idea URL": t.idea_url or "",
            "Date Opened": t.date_opened.strftime('%Y-%m-%d %H:%M:%S') if t.date_opened else "",
            "Date Closed": close_date_str,
            "Status": t.status,
            "Collateral": t.collateral if t.collateral is not None else 0.0,
            "Max Profit": t.max_profit if t.max_profit is not None else 0.0,
            "Max Loss": t.max_loss if t.max_loss is not None else 0.0,
            "Probability of Profit": t.probability_of_profit if t.probability_of_profit is not None else 0.0,
            "Probability of Loss": t.probability_of_loss if t.probability_of_loss is not None else 0.0,
            "Probability Max Profit": t.probability_max_profit if t.probability_max_profit is not None else 0.0,
            "Probability Max Loss": t.probability_max_loss if t.probability_max_loss is not None else 0.0,
            "Expected Value": t.expected_value if t.expected_value is not None else 0.0,
            "Underlying Price at Open": t.underlying_price_at_open if t.underlying_price_at_open is not None else 0.0,
            "Premium Collected": stats["premium_collected"],
            "Premium Paid": stats["premium_paid"],
            "Total Commission": stats["total_commission"],
            "Net PnL": stats["pnl"],
            "Contracts": contracts,
            "Outcome": outcome,
            "Legs": legs_str,
            "Transactions": tx_str
        })
        
    df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode('utf-8')


db = SessionLocal()

active_portfolio_id = st.session_state.get("active_portfolio_id")
if active_portfolio_id:
    trades = db.query(Trade).filter(Trade.portfolio_id == active_portfolio_id).all()
else:
    trades = []
    st.warning("No portfolio selected. Please select one from the sidebar.")

if trades:
    # Filtering logic matching Journal
    # Initialize keys in session state for resetting filters
    if "export_filter_ticker" not in st.session_state:
        st.session_state.export_filter_ticker = ""
    if "export_filter_date" not in st.session_state:
        st.session_state.export_filter_date = "All"
    if "export_filter_status" not in st.session_state:
        st.session_state.export_filter_status = "All"
    if "export_filter_strategy" not in st.session_state:
        st.session_state.export_filter_strategy = "All"
    if "export_filter_type" not in st.session_state:
        st.session_state.export_filter_type = "All"

    def reset_export_filters():
        st.session_state.export_filter_ticker = ""
        st.session_state.export_filter_date = "All"
        st.session_state.export_filter_status = "All"
        st.session_state.export_filter_strategy = "All"
        st.session_state.export_filter_type = "All"

    filter_col1, filter_col2, filter_col3, filter_col4, filter_col5, filter_col6 = st.columns([1, 1, 1.4, 1.2, 1, 0.9])
    filter_ticker = filter_col1.text_input("Filter by Ticker", key="export_filter_ticker")
    
    date_options = ["Last 7 days", "Last month", "Last 3 Months", "Last Year", "YTD", "All"]
    date_filter = filter_col2.selectbox("Filter by Date", date_options, key="export_filter_date")
    
    today = datetime.today().date()
    if date_filter == "Last 7 days":
        start_date = today - timedelta(days=7)
    elif date_filter == "Last month":
        start_date = today - timedelta(days=30)
    elif date_filter == "Last 3 Months":
        start_date = today - timedelta(days=90)
    elif date_filter == "Last Year":
        start_date = today - timedelta(days=365)
    elif date_filter == "YTD":
        start_date = datetime(today.year, 1, 1).date()
    else:
        start_date = datetime.min.date()
        
    filter_status = filter_col3.radio("Filter by Status", ["All", "Open Trades", "Closed Trades"], key="export_filter_status", horizontal=True)
    
    strategy_options = ["All"] + list(set([t.strategy_type for t in trades]))
    filter_strategy = filter_col4.selectbox("Filter by Strategy", strategy_options, key="export_filter_strategy")
    
    filter_type = filter_col5.selectbox("Filter by Debit/Credit", ["All", "Debit", "Credit"], key="export_filter_type")

    filter_col6.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    if filter_col6.button("Reset filters", key="export_reset_btn", type="primary", use_container_width=True, on_click=reset_export_filters):
        pass

    # Apply filters
    filtered_trades = trades
    if filter_ticker:
        filtered_trades = [t for t in filtered_trades if filter_ticker.upper() in t.ticker.upper()]
    if date_filter != "All":
        def get_reference_date(t):
            if t.status == "Open":
                return t.date_opened.date()
            else:
                close_dates = [tx.date for tx in t.transactions if tx.action != "Open"]
                if close_dates:
                    return max(close_dates).date()
                return t.date_opened.date()
                
        filtered_trades = [t for t in filtered_trades if get_reference_date(t) >= start_date]
        
    if filter_status != "All":
        if filter_status == "Open Trades":
            filtered_trades = [t for t in filtered_trades if t.status == "Open"]
        elif filter_status == "Closed Trades":
            filtered_trades = [t for t in filtered_trades if t.status != "Open"]
            
    if filter_strategy != "All":
        filtered_trades = [t for t in filtered_trades if t.strategy_type == filter_strategy]
        
    if filter_type != "All":
        if filter_type == "Debit":
            filtered_trades = [t for t in filtered_trades if t.strategy_type and "debit" in t.strategy_type.lower()]
        elif filter_type == "Credit":
            filtered_trades = [t for t in filtered_trades if t.strategy_type and "credit" in t.strategy_type.lower()]
        
    # Sort
    filtered_trades.sort(key=lambda x: x.date_opened, reverse=True)
    
    st.write(f"**{len(filtered_trades)} trades match the current filters.**")
    
    filter_info = {
        "Ticker": filter_ticker if filter_ticker else "All",
        "Date": date_filter,
        "Status": filter_status,
        "Strategy": filter_strategy,
        "Debit/Credit": filter_type
    }
    
    pdf_bytes = bytes(generate_pdf(filtered_trades, filter_info))
    
    col_pdf, col_csv = st.columns(2)
    with col_pdf:
        st.download_button(
            label="Generate PDF Report",
            data=pdf_bytes,
            file_name=f"Trade_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
    with col_csv:
        csv_bytes = generate_csv_data(filtered_trades)
        st.download_button(
            label="Export CSV Report",
            data=csv_bytes,
            file_name=f"Trades_Export_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            type="secondary",
            use_container_width=True
        )

db.close()
