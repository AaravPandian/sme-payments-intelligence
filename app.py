"""LedgerLens: beginner-friendly, synthetic UK SME payments dashboard.

Run after `python -m scripts.build_project` with `streamlit run app.py`.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.analytics import merchant_summary, method_summary, monthly_summary, overall_kpis, safe_percent
from src.config import AS_OF_DATE, DB_PATH, ROOT
from src.database import build_database, load_payments

st.set_page_config(page_title="LedgerLens | SME Payments Intelligence", page_icon="💳", layout="wide")
st.markdown("""
<style>
.block-container {padding-top: 1.6rem; padding-bottom: 2.5rem; max-width: 1400px;}
.hero {padding: 1.35rem 1.6rem; border: 1px solid #23405B; border-radius: 16px;
  background: linear-gradient(115deg,#132C43,#101D32 65%,#153C3B); margin-bottom: 1rem;}
.hero h1 {font-size: 2.2rem; margin: 0 0 .3rem; letter-spacing: -.8px;}
.hero p {margin: 0; color: #BDD2E1;}
.tag {font-size:.74rem; color:#6EE8C4; letter-spacing:1.5px; font-weight:700;}
div[data-testid="stMetric"] {background:#11243A; border:1px solid #233D54; border-radius:12px; padding:15px;}
div[data-testid="stMetricValue"] {font-size: 1.6rem;}
.small-note {color:#91A9BC; font-size:.82rem;}
</style>
""", unsafe_allow_html=True)


def pounds(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"£{value / 1_000_000:,.2f}m"
    if abs(value) >= 1000:
        return f"£{value / 1000:,.1f}k"
    return f"£{value:,.2f}"


def finish_chart(fig, height=370):
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color="#D8E9F6"), margin=dict(l=12, r=12, t=50, b=20),
                      height=height, legend_title_text="", hovermode="closest")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#273C52", zerolinecolor="#273C52")
    return fig


@st.cache_data(show_spinner=False)
def cached_payments(db_stamp: float):
    # db_stamp makes Streamlit invalidate the cache after the SQLite DB is rebuilt.
    return load_payments()


st.markdown("""
<div class="hero">
 <div class="tag">PORTFOLIO PROJECT · DIGITAL BANKING ANALYTICS</div>
 <h1>LedgerLens <span style="color:#61E0BD">/ SME Payments</span></h1>
 <p>Explore payment approvals, merchant performance, refunds and payouts across a fictional UK SME portfolio.</p>
</div>
""", unsafe_allow_html=True)

if not DB_PATH.exists():
    # GitHub intentionally excludes generated SQLite. Rebuild from committed CSVs
    # so hosted Streamlit Community Cloud can launch without a manual shell step.
    try:
        build_database()
    except (OSError, sqlite3.DatabaseError, ValueError) as err:
        st.error(f"Cannot create the demo database from the sample CSVs: {err}. Try `python -m scripts.build_project` locally.")
        st.stop()

try:
    payments = cached_payments(DB_PATH.stat().st_mtime_ns)
except (sqlite3.DatabaseError, OSError, ValueError) as err:
    st.error(f"Database could not be loaded: {err}")
    st.stop()

st.sidebar.title("Filters")
st.sidebar.caption("Applies to dashboard charts and exported payments. SQL Lab queries use the full database.")
first_day = payments["payment_date"].min().date()
last_day = payments["payment_date"].max().date()
window = st.sidebar.date_input("Original payment date", value=(first_day, last_day), min_value=first_day, max_value=last_day)
industries = sorted(payments["industry"].unique().tolist())
selected_industries = st.sidebar.multiselect("Industry", industries, default=industries)
methods = sorted(payments["payment_method"].unique().tolist())
selected_methods = st.sidebar.multiselect("Payment method", methods, default=methods)
merchant_names = sorted(payments["merchant_name"].unique().tolist())
selected_merchant = st.sidebar.selectbox("Merchant", ["All merchants", *merchant_names])

if not isinstance(window, (tuple, list)) or len(window) != 2:
    st.info("Select a start date and an end date in the sidebar.")
    st.stop()
start_day, end_day = window
if start_day > end_day:
    st.warning("Start date must be before end date.")
    st.stop()
mask = (payments["payment_date"].dt.date >= start_day) & (payments["payment_date"].dt.date <= end_day)
mask &= payments["industry"].isin(selected_industries) & payments["payment_method"].isin(selected_methods)
if selected_merchant != "All merchants":
    mask &= payments["merchant_name"].eq(selected_merchant)
filtered = payments.loc[mask].copy()
st.sidebar.markdown("---")
st.sidebar.caption(f"**Demo cutoff:** {AS_OF_DATE} · GBP only · synthetic data")
st.sidebar.caption(f"Showing **{len(filtered):,}** of **{len(payments):,}** payment attempts")

if filtered.empty:
    st.warning("No payments match these filters. Try broadening the date range or selections.")
    st.stop()

kpis = overall_kpis(filtered)
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Gross processed", pounds(kpis["gross_gbp"]), help="Successful payments only")
col2.metric("Payment success", f"{kpis['success_rate_pct']:.1f}%", help="Successful attempts divided by all attempts")
col3.metric("Net processed", pounds(kpis["net_gbp"]), help="Gross less processing fees and attributed refunds")
col4.metric("Refund rate (value)", f"{kpis['refund_rate_pct']:.2f}%", help="Refund value / gross processed, not proportion of transactions")
col5.metric("Pending payouts", pounds(kpis["pending_payout_gbp"]), help="Future-scheduled gross less fee payouts at the demo cutoff")

st.caption("Synthetic scenario · Refunds are attributed to the original payment date · Payout status is fixed as of 30 Sep 2026 · Figures are illustrative, not real financial data.")
tabs = st.tabs(["Overview", "Payment performance", "SME merchants", "Refunds & payouts", "SQL Lab", "Data explorer"])

with tabs[0]:
    a, b = st.columns([1.7, 1])
    with a:
        monthly = monthly_summary(filtered)
        long_data = monthly.melt(id_vars="month", value_vars=["gross_gbp", "net_gbp"], var_name="Metric", value_name="GBP")
        long_data["Metric"] = long_data["Metric"].map({"gross_gbp": "Gross", "net_gbp": "Net after fees & refunds"})
        fig = px.line(long_data, x="month", y="GBP", color="Metric", markers=True,
                      color_discrete_map={"Gross": "#64DFC0", "Net after fees & refunds": "#7EA9FF"},
                      title="Monthly payment value", labels={"month": "Month", "GBP": "Value (£)"})
        st.plotly_chart(finish_chart(fig), use_container_width=True)
    with b:
        status_counts = filtered["payment_status"].value_counts().rename_axis("Outcome").reset_index(name="Attempts")
        fig = px.pie(status_counts, names="Outcome", values="Attempts", hole=0.7, title="Payment outcomes",
                     color="Outcome", color_discrete_map={"succeeded": "#64DFC0", "failed": "#FF8B8B"})
        fig.update_traces(textinfo="percent+label")
        st.plotly_chart(finish_chart(fig), use_container_width=True)
    left, right = st.columns(2)
    with left:
        method = method_summary(filtered)
        fig = px.bar(method, x="payment_method", y="gross_gbp", title="Gross value by payment method",
                     color="payment_method", color_discrete_sequence=px.colors.qualitative.Pastel,
                     labels={"gross_gbp": "Value (£)", "payment_method": "Payment method"})
        st.plotly_chart(finish_chart(fig), use_container_width=True)
    with right:
        industries_agg = filtered.groupby("industry", as_index=False)["net_gbp"].sum().sort_values("net_gbp")
        fig = px.bar(industries_agg, x="net_gbp", y="industry", orientation="h", title="Net payment value by industry",
                     labels={"net_gbp": "Net value (£)", "industry": "Industry"}, color_discrete_sequence=["#66CDAA"])
        st.plotly_chart(finish_chart(fig), use_container_width=True)

with tabs[1]:
    st.subheader("Where do payment attempts fail?")
    l, r = st.columns(2)
    with l:
        method = method_summary(filtered).sort_values("success_rate_pct")
        fig = px.bar(method, x="success_rate_pct", y="payment_method", orientation="h", text="success_rate_pct",
                     title="Success rate by method", labels={"success_rate_pct": "Approval rate (%)", "payment_method": "Method"},
                     color_discrete_sequence=["#7EA9FF"])
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_xaxes(range=[0, 110])
        st.plotly_chart(finish_chart(fig), use_container_width=True)
    with r:
        time_data = filtered.assign(weekday=filtered["payment_date"].dt.day_name())
        day = time_data.groupby("weekday", as_index=False).agg(attempts=("payment_id", "count"), successful=("successful", "sum"))
        order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day["failure_rate_pct"] = 100 * (1 - day["successful"] / day["attempts"])
        fig = px.bar(day, x="weekday", y="failure_rate_pct", title="Failure rate by weekday",
                     category_orders={"weekday": order}, labels={"weekday": "Day", "failure_rate_pct": "Failure rate (%)"},
                     color_discrete_sequence=["#F3B976"])
        st.plotly_chart(finish_chart(fig), use_container_width=True)
    st.dataframe(method_summary(filtered).rename(columns={"payment_method":"Payment method", "attempts":"Attempts", "successful":"Successful", "gross_gbp":"Gross (£)", "fees_gbp":"Fees (£)", "success_rate_pct":"Success rate (%)"}),
                 use_container_width=True, hide_index=True)
    st.info("Failure patterns here are fictional and not evidence of fraud or real payment-provider performance.")

with tabs[2]:
    merchants = merchant_summary(filtered)
    st.subheader("Merchant benchmarking")
    l, r = st.columns([1.1, 1])
    with l:
        top = merchants.head(12).sort_values("net_gbp")
        fig = px.bar(top, x="net_gbp", y="merchant_name", orientation="h", title="Top 12 SMEs by net volume",
                     labels={"merchant_name": "SME", "net_gbp": "Net value (£)"}, color_discrete_sequence=["#64DFC0"])
        st.plotly_chart(finish_chart(fig, height=475), use_container_width=True)
    with r:
        bubbles = merchants[merchants["gross_gbp"] > 0].copy()
        fig = px.scatter(bubbles, x="success_rate_pct", y="refund_rate_pct", size="gross_gbp", color="industry",
                         hover_name="merchant_name", size_max=28, title="SME success vs. refund rate",
                         labels={"success_rate_pct": "Success rate (%)", "refund_rate_pct": "Refunded value (%)"})
        st.plotly_chart(finish_chart(fig, height=475), use_container_width=True)
    st.dataframe(merchants.head(30), use_container_width=True, hide_index=True)
    st.caption("Merchant metrics require enough attempts for meaningful comparison; this chart is descriptive, not a risk model.")

with tabs[3]:
    l, r = st.columns(2)
    with l:
        sector = filtered.groupby("industry", as_index=False).agg(refunds_gbp=("refund_amount_gbp", "sum"), gross_gbp=("gross_gbp", "sum"))
        sector["refund_rate_pct"] = sector.apply(lambda r: safe_percent(r["refunds_gbp"], r["gross_gbp"]), axis=1)
        fig = px.bar(sector.sort_values("refund_rate_pct"), y="industry", x="refund_rate_pct", orientation="h",
                     title="Refund value as % of gross by industry", labels={"industry": "Industry", "refund_rate_pct": "Refund rate (%)"},
                     color_discrete_sequence=["#F2AC85"])
        st.plotly_chart(finish_chart(fig), use_container_width=True)
    with r:
        payout = filtered[filtered["successful"]].groupby("settlement_status", as_index=False)["payout_amount_gbp"].sum()
        fig = px.pie(payout, names="settlement_status", values="payout_amount_gbp", hole=0.67,
                     title="Scheduled payout value by status", color="settlement_status",
                     color_discrete_map={"paid": "#64DFC0", "pending": "#FFBF69"})
        st.plotly_chart(finish_chart(fig), use_container_width=True)
    a, b, c = st.columns(3)
    a.metric("Total refunds", pounds(kpis["refunds_gbp"]))
    b.metric("Paid payouts", pounds(kpis["paid_payout_gbp"]))
    c.metric("Scheduled pending", pounds(kpis["pending_payout_gbp"]))
    st.subheader("Pending payouts")
    pending = filtered.loc[filtered["settlement_status"] == "pending",
                           ["payment_id", "merchant_name", "scheduled_payout_date", "payout_amount_gbp"]]
    st.dataframe(pending.sort_values("scheduled_payout_date").head(150), use_container_width=True, hide_index=True)
    st.caption("Payout amounts exclude processing fees; subsequent refunds are reported separately and do not rewrite historical payout records.")

with tabs[4]:
    st.subheader("Learn SQL by answering six business questions")
    queries = {
        "1 · Monthly gross vs. net volume": "01_monthly_volume.sql",
        "2 · Approval rates by payment method": "02_payment_method_success.sql",
        "3 · Highest-volume SMEs": "03_top_merchants.sql",
        "4 · Refund rates by industry": "04_refunds_by_industry.sql",
        "5 · Outstanding settlements": "05_pending_settlements.sql",
        "6 · Merchant failure hotspots": "06_failure_hotspots.sql",
    }
    selected_query = st.selectbox("Business question", list(queries))
    query_text = (ROOT / "sql" / "queries" / queries[selected_query]).read_text(encoding="utf-8")
    st.code(query_text, language="sql")
    with sqlite3.connect(DB_PATH) as conn:
        sql_result = pd.read_sql_query(query_text, conn)
    st.dataframe(sql_result, use_container_width=True, hide_index=True)
    st.download_button("Export query result as CSV", sql_result.to_csv(index=False).encode("utf-8"),
                       file_name="sql_query_result.csv", mime="text/csv")
    st.caption("SQL queries always run against the complete sample database. Dashboard filters do not change SQL results.")

with tabs[5]:
    st.subheader("Inspect original payment attempts")
    st.write(f"{kpis['attempts']:,} attempts · {kpis['successful_payments']:,} successful · "+
             f"{(filtered['refund_amount_gbp'] > 0).sum():,} refunded")
    display_cols = ["payment_id", "payment_date", "merchant_name", "industry", "payment_method",
                    "amount_gbp", "payment_status", "processing_fee_gbp", "refund_amount_gbp", "settlement_status"]
    st.dataframe(filtered[display_cols].sort_values("payment_date", ascending=False).head(1000), use_container_width=True, hide_index=True)
    st.download_button("Download all filtered records (CSV)", filtered[display_cols].to_csv(index=False).encode("utf-8"),
                       file_name="filtered_payments.csv", mime="text/csv")
    st.caption("The table shows the first 1,000 rows; the download contains all filtered payment attempts.")

st.markdown("---")
st.markdown("<span class='small-note'>Built with Python · SQLite SQL · Pandas · Streamlit · Plotly | Synthetic educational dataset | Not for financial decisions</span>", unsafe_allow_html=True)
