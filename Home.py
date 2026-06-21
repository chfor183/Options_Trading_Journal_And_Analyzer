import streamlit as st
from src.db import init_db, SessionLocal
from src.models import Portfolio

# We need a small hack to only run Home content when we're actually on the Home page,
# because when using st.navigation, this file becomes the router and runs for every page.
if "page" not in st.session_state:
    st.session_state.page = "Home"

try:
    init_db()
except Exception as e:
    pass

with st.sidebar:
    st.header("Portfolio Selection")
    db = SessionLocal()
    portfolios = db.query(Portfolio).all()
    if portfolios:
        portfolio_options = {p.id: p.name for p in portfolios}
        
        # Determine index of current selection, default to 0
        current_idx = 0
        if "active_portfolio_id" in st.session_state:
            for i, p in enumerate(portfolios):
                if p.id == st.session_state.active_portfolio_id:
                    current_idx = i
                    break
                    
        selected_p_id = st.selectbox(
            "Select Portfolio",
            options=list(portfolio_options.keys()),
            format_func=lambda x: portfolio_options[x],
            index=current_idx
        )
        st.session_state.active_portfolio_id = selected_p_id
    else:
        st.warning("No portfolios found.")

    st.divider()
    with st.expander("Manage Portfolios"):
        st.subheader("Create")
        new_p_name = st.text_input("New Portfolio Name")
        new_p_desc = st.text_input("Description")
        if st.button("Create Portfolio") and new_p_name:
            new_port = Portfolio(name=new_p_name, description=new_p_desc)
            db.add(new_port)
            db.commit()
            st.success(f"Created {new_p_name}!")
            st.rerun()
            
        st.divider()
        st.subheader("Delete")
        if portfolios:
            del_p_id = st.selectbox(
                "Portfolio to Delete",
                options=list(portfolio_options.keys()),
                format_func=lambda x: portfolio_options[x],
                key="del_port_select"
            )
            if st.button("Delete Portfolio", type="primary", use_container_width=True):
                port_to_delete = db.query(Portfolio).filter(Portfolio.id == del_p_id).first()
                if port_to_delete:
                    db.delete(port_to_delete)
                    db.commit()
                    if st.session_state.get("active_portfolio_id") == del_p_id:
                        del st.session_state.active_portfolio_id
                    st.success(f"Deleted portfolio {port_to_delete.name}")
                    st.rerun()
    db.close()

pages = {
    "Navigation": [
        st.Page("pages/0_Home_Content.py", title="Home", icon="🏠", default=True),
        st.Page("pages/1_Trade.py", title="Trade", icon="📝"),
        st.Page("pages/2_Journal.py", title="Journal", icon="📓"),
        st.Page("pages/3_Dashboard.py", title="Dashboard", icon="📊"),
    ],
    "Hidden": [
        st.Page("pages/4_Close Trade.py", title="Close Trade", icon="✖")
    ]
}

pg = st.navigation(pages)
pg.run()

