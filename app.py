import streamlit as st
import pandas as pd
import plotly.express as px
from db import get_ai_impact_data,get_daily_portfolio_data

# st.set_page_config(page_title="AI Ads Impact Dashboard", layout="wide")


st.set_page_config(layout="wide")


st.title("🤖 AI Ads Optimization Impact Dashboard")


# load data
raw_df = get_ai_impact_data().dropna()
portfolio_df = get_daily_portfolio_data()


# convert date safely
raw_df["action_date"] = pd.to_datetime(raw_df["action_date"], errors="coerce")
raw_df = raw_df.dropna(subset=["action_date"])

cycle_dates = sorted(raw_df["action_date"].unique())


# create week column
# create 7-day action window label
raw_df["week_range"] = (
    raw_df["action_date"].dt.strftime("%b %d")
    + " - " +
    (raw_df["action_date"] + pd.Timedelta(days=6)).dt.strftime("%b %d")
)

raw_df["week"] = raw_df["action_date"].dt.strftime("%Y - Week %U")

portfolio_df = portfolio_df.sort_values("report_date")

anchor_date = pd.to_datetime("2026-02-05")

portfolio_df["week_number"] = (
    (portfolio_df["report_date"] - anchor_date).dt.days // 7
)

anchor_date = pd.to_datetime("2026-02-05")

raw_df["week_number"] = (
    (pd.to_datetime(raw_df["action_date"]) - anchor_date).dt.days // 7
)

weekly = (
    portfolio_df
    .groupby("week_number")
    .agg({
        "report_date": ["min", "max"],
        "total_sales": "sum",
        "total_spend": "sum"
    })
    .reset_index()
)

weekly.columns = ["week_number", "start_date", "end_date", "total_sales", "total_spend"]

weekly["avg_roas"] = weekly["total_sales"] / weekly["total_spend"]

weekly["week_range"] = (
    weekly["start_date"].dt.strftime("%d %b")
    + " – " +
    weekly["end_date"].dt.strftime("%d %b")
)
weekly = weekly[weekly["start_date"] >= pd.to_datetime("2026-01-29")]


# fig = px.line(
#     weekly,
#     x="week_range",
#     y="avg_roas",
#     markers=True,
#     title="Weekly Portfolio ROAS Trend"
# )

# st.plotly_chart(fig, use_container_width=True)

weekly_roas = (
    portfolio_df
    .groupby("week_number")
    .agg({
        "total_sales": "sum",
        "total_spend": "sum"
    })
    .reset_index()
)

weekly_roas["portfolio_roas"] = (
    weekly_roas["total_sales"] /
    weekly_roas["total_spend"]
)

weekly_ai = (
    raw_df
    .groupby("week_number")["roas_change"]
    .mean()
    .reset_index()
)

merged = weekly_roas.merge(
    weekly[["week_number", "week_range"]],
    on="week_number",
    how="left"
)

st.markdown("### Filters")

col1, col2 = st.columns(2)

# Campaign dropdown
with col1:
    campaigns = sorted(raw_df["campaign_id"].unique())
    selected_campaign = st.selectbox("Campaign ID", campaigns)

# Week dropdown
with col2:
    week_list = weekly.sort_values("week_number")["week_range"].tolist()
    selected_week = st.selectbox("Week", week_list)


# df = raw_df[
#     (raw_df["campaign_id"] == selected_campaign) &
#     (raw_df["week_range"] == selected_week)
# ].copy()

selected_week_row = weekly[weekly["week_range"] == selected_week]
selected_week_number = selected_week_row["week_number"].iloc[0]

df = raw_df[
    (raw_df["campaign_id"] == selected_campaign) &
    (raw_df["week_number"] == selected_week_number)
].copy()



def classify(row):
    if row["action"] == "PAUSE" and row["spend_after"] == 0:
        return "Saved Budget 💰"
    elif row["roas_change"] > 0:
        return "Success ✅"
    else:
        return "Failed ❌"

df["result"] = df.apply(classify, axis=1)

# Get portfolio weekly data for selected week
weekly_selected = weekly[weekly["week_range"] == selected_week]

# st.write("Selected Week:", selected_week)
# st.write("Weekly Selected Row:")
# st.write(weekly_selected)


if not weekly_selected.empty:
    week_roas = weekly_selected["avg_roas"].iloc[0]
    week_spend = weekly_selected["total_spend"].iloc[0]
else:
    week_roas = 0
    week_spend = 0


st.markdown("### 📊 Weekly Performance Summary")

col1, col2, col3 = st.columns(3)

# 1️⃣ AI Success Rate
if len(df) > 0:
    success_rate = (df["result"] == "Success ✅").mean() * 100
else:
    success_rate = 0

# 2️⃣ Portfolio ROAS (Weekly)
# already computed above

# 3️⃣ Portfolio Spend (Weekly)

col1.metric("AI Success Rate", f"{success_rate:.1f}%")
col2.metric("Weekly ROAS", f"{week_roas:.2f}")
col3.metric("Weekly Spend", f"₹{week_spend:,.0f}")

# st.markdown("### 📊 AI Performance Summary")

# col1, col2, col3, col4 = st.columns(4)

# success_rate = (df["result"] == "Success ✅").mean() * 100
# avg_roas_lift = df["roas_change"].mean()
# spend_saved = df[df["spend_change"] < 0]["spend_change"].sum()
# impressions = df["impressions_after"].sum()

# col1.metric("Success Rate", f"{success_rate:.1f}%")
# col2.metric("Avg ROAS Change", f"{avg_roas_lift:.2f}")
# col3.metric("Spend Saved", f"₹{abs(spend_saved):,.0f}")
# col4.metric("Impressions After", f"{impressions:,.0f}")


# st.markdown("### 📈 Impact Visualisation")
# col1, col2 = st.columns(2)

# with col1:
#     fig = px.bar(
#         raw_df,
#         x="targeting",
#         y=["roas_before", "roas_after"],
#         barmode="group",
#         title="ROAS Before vs After"
#     )
#     st.plotly_chart(fig, use_container_width=True)

# with col2:
#     pie = px.pie(raw_df, names="result", title="Decision Outcomes")
#     st.plotly_chart(pie, use_container_width=True)


# st.header("AI Decision Success Distribution")

# pie = px.pie(raw_df, names="result", title="Decision Outcomes")
# st.plotly_chart(pie, use_container_width=True)




fig = px.line(
    weekly,
    x="week_range",
    y="avg_roas",
    markers=True,
    title="Weekly Portfolio ROAS Trend"
)

st.plotly_chart(fig, use_container_width=True)


df = df.reset_index(drop=True)


st.header("Keyword Decision Scorecard")


st.data_editor(
    df[[
        "targeting",
        "action",
        "roas_before",
        "roas_after",
        "roas_change",
        "spend_before",
        "spend_after",
        "spend_change",
        "impressions_before",
        "impressions_after",
        "result",
        "explanation"
    ]],
    use_container_width=True,
    height=500,
    disabled=True
)

st.header("ROAS Before vs After")

fig = px.bar(
    df,
    x="targeting",
    y=["roas_before", "roas_after"],
    barmode="group",
    title="Keyword ROAS Comparison"
)
st.plotly_chart(fig, use_container_width=True)

# st.markdown("### 🧠 Keyword Decision Scoreboard")

# df = df.sort_values("roas_change", ascending=False)

# for _, row in df.iterrows():
#     with st.container():
#         col1, col2, col3, col4 = st.columns([2,1,1,1])
        
#         col1.markdown(f"**{row['targeting']}**")
#         col2.markdown(f"Action: **{row['action']}**")
#         col3.markdown(f"ROAS: **{row['roas_before']:.2f} → {row['roas_after']:.2f}**")
#         col4.markdown(f"Result: **{row['result']}**")

#         # expandable explanation
#         with st.expander("Why did AI suggest this?"):
#             st.write(row["explanation"])

#         st.markdown("---")



