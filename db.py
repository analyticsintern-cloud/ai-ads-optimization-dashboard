import pandas as pd
from sqlalchemy import create_engine
import os
# from dotenv import load_dotenv

# load_dotenv()

# def get_engine():
#     return create_engine(
#         f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
#         f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
#     )


def get_engine():
    return create_engine(
        f"postgresql+psycopg2://{st.secrets['DB_USER']}:{st.secrets['DB_PASSWORD']}@"
        f"{st.secrets['DB_HOST']}:{st.secrets['DB_PORT']}/{st.secrets['DB_NAME']}"
    )


def get_ai_impact_data():
    engine = get_engine()

    query = """
    WITH actions AS (
        SELECT 
            campaign_id,
            targeting,
            action,
            explanation,
            created_at::date AS action_date
        FROM voylla.llm_keyword_actions
    ),

    performance AS (
        SELECT
            TO_TIMESTAMP("Date",'YYYY-MM-DD HH24:MI:SS')::date AS report_date,
            "Campaign ID" AS campaign_id,
            "Targeting Value" AS targeting,
            SUM("Estimated Budget Consumed") AS spend,
            SUM("Direct Sales" + "Indirect Sales") AS sales,
            SUM("Impressions") AS impressions
        FROM voylla."Blinkit_Ads_Report"
        GROUP BY 1,2,3
    ),

    before_after AS (
        SELECT
            a.campaign_id,
            a.targeting,
            a.action,
            a.action_date,
            a.explanation,

            SUM(CASE WHEN p.report_date BETWEEN a.action_date - INTERVAL '7 days'
                                           AND a.action_date - INTERVAL '1 day'
                     THEN p.spend END) AS spend_before,

            SUM(CASE WHEN p.report_date BETWEEN a.action_date - INTERVAL '7 days'
                                           AND a.action_date - INTERVAL '1 day'
                     THEN p.sales END) AS sales_before,

            SUM(CASE WHEN p.report_date BETWEEN a.action_date
                                           AND a.action_date + INTERVAL '6 days'
                     THEN p.spend END) AS spend_after,

            SUM(CASE WHEN p.report_date BETWEEN a.action_date
                                           AND a.action_date + INTERVAL '6 days'
                     THEN p.sales END) AS sales_after,
            
            SUM(CASE WHEN p.report_date BETWEEN a.action_date - INTERVAL '7 days'
                                           AND a.action_date - INTERVAL '1 days' 
                     THEN p.impressions END) AS imp_before,
            SUM(CASE WHEN p.report_date BETWEEN a.action_date
                                           AND a.action_date + INTERVAL '6 days'
                     THEN p.impressions END) AS imp_after
        FROM actions a
        LEFT JOIN performance p
        ON a.campaign_id = p.campaign_id
        AND a.targeting = p.targeting
        GROUP BY 1,2,3,4,5
    )

    SELECT *,
        CASE 
            WHEN spend_before > 0 THEN sales_before / spend_before
            ELSE 0 
        END AS roas_before,

        CASE 
            WHEN spend_after > 0 THEN sales_after / spend_after
            ELSE 0 
        END AS roas_after,

        CASE 
            WHEN spend_before > 0 AND spend_after > 0
            THEN (sales_after / spend_after) - (sales_before / spend_before)
            ELSE 0
        END AS roas_change,
        spend_after - spend_before AS spend_change,
        imp_before AS impressions_before,
        imp_after  AS impressions_after
    FROM before_after;
    """

    return pd.read_sql(query, engine)

def get_daily_portfolio_data():
    engine = get_engine()

    query = """
    SELECT
        TO_TIMESTAMP("Date",'YYYY-MM-DD HH24:MI:SS')::date AS report_date,
        SUM("Estimated Budget Consumed") AS total_spend,
        SUM("Direct Sales" + "Indirect Sales") AS total_sales
    FROM voylla."Blinkit_Ads_Report"
    WHERE TO_TIMESTAMP("Date",'YYYY-MM-DD HH24:MI:SS')::date >= DATE '2026-01-29' AND "Campaign ID" = '296468'
    GROUP BY 1
    ORDER BY 1;
    """

    df = pd.read_sql(query, engine)
    df["report_date"] = pd.to_datetime(df["report_date"])
    df["roas_daily"] = df["total_sales"] / df["total_spend"]
    return df

