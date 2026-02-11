import streamlit as st
import pandas as pd
import re
from bigquery_utils import query_bigquery

st.set_page_config(page_title="Query Viewer", layout="wide")

st.title("BigQuery Query Viewer")

tab1, tab2 = st.tabs(["Tab 1", "Tab 2"])

query = """
With campaign as (
  SELECT id cam_id, 
    platform,
    project_name,
    stage,participation_count as cam_participation,
  FROM opa_hybrid.campaign
  WHERE platform = 'product_trials'
),
product as (
  SELECT campaign_id, 
    pb.id as bundle_id,
    p.id as product_id, 
    pb.participation_count, 
    JSON_VALUE(pb.procurement_props, '$.orders_per_day') daily_limit, 
    JSON_VALUE(pb.procurement_props, '$.ecommerce_platform') product_platform,
    JSON_VALUE(pb.procurement_props, '$.new_user_blocked_seats') new_user_seats,
    pb.procurement_props,
    quantity,
  FROM opa_hybrid.product_bundle pb
  LEFT JOIN `opa_hybrid.product_bundle_item` pbi
  ON pb.id = pbi.product_bundle_id
  LEFT JOIN opa_hybrid.product p 
  ON pbi.product_id = p.id
), 
collab as ( 
  SELECT product_bundle_id, COUNTIF(invite_stage = 'ACCEPTED') as acceptance, 
  FROM opa_hybrid.collaboration
  WHERE invite_stage = 'ACCEPTED'
  AND is_revoked = 'false'
  AND DATE(JSON_VALUE(participation_props, '$.acceptance.created_at')) = CURRENT_DATE() -1
  GROUP BY 1
),
final_data as (
  SELECT cam_id, 
    cam_participation, project_name,
    bundle_id, product_id, participation_count, 
    CAST(daily_limit as INT64) as daily_limit, 
    product_platform, 
    quantity, acceptance,
    CAST(new_user_seats as INT64) new_user_seats
  FROM campaign cam
  LEFT JOIN product as p
  ON cam.cam_id = p.campaign_id
  LEFT JOIN collab as c
  ON p.bundle_id = c.product_bundle_id AND cam.cam_id = p.campaign_id
  WHERE stage = 'LIVE'AND participation_count < quantity
)
SELECT product_id, 
  product_platform,
  SUM(daily_limit) as daily_limit,
  SUM(acceptance) as accepted_yesterday,
  SUM(new_user_seats) as new_user_seats,
  SUM(participation_count) as total_acceptances,
  SUM(quantity) as total_quantity,
  STRING_AGG(Concat(cam_id,' - ', bundle_id), '\\n') as campaigns,
  STRING_AGG(project_name, '\\n') as project_name
FROM final_data
GROUP BY 1, 2
HAVING daily_limit - accepted_yesterday > 0
"""

with tab1:
    if 'df' not in st.session_state:
        try:
            with st.spinner("Executing query..."):
                st.session_state.df = query_bigquery(query)
                st.success(f"Query executed successfully! Found {len(st.session_state.df)} rows.")
        except Exception as e:
            st.error(f"Error executing query: {str(e)}")
            st.session_state.df = pd.DataFrame()

    if not st.session_state.df.empty:
        st.subheader("Filters")
        col1, col2 = st.columns(2)
        
        with col1:
            unique_platforms = sorted(st.session_state.df['product_platform'].dropna().unique().tolist())
            platform_options = ["All"] + unique_platforms
            product_platform_filter = st.selectbox("Filter by Product Platform:", platform_options)
        
        with col2:
            project_name_filter = st.text_input("Filter by Project Name (substring):", value="")
        
        filtered_df = st.session_state.df.copy()
        
        if product_platform_filter and product_platform_filter != "All":
            filtered_df = filtered_df[
                filtered_df['product_platform'] == product_platform_filter
            ]
        
        if project_name_filter:
            filtered_df = filtered_df[
                filtered_df['project_name'].astype(str).str.contains(
                    project_name_filter, case=False, na=False
                )
            ]
        
        filtered_df = filtered_df.reset_index(drop=True)
        
        st.write(f"Showing {len(filtered_df)} of {len(st.session_state.df)} rows")
        
        st.markdown("""
        <style>
        div[data-testid="stDataFrame"] table td,
        div[data-testid="stDataFrame"] table th {
            white-space: normal !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
        }
        div[data-testid="stDataFrame"] table {
            table-layout: auto !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.dataframe(filtered_df, use_container_width=True)

with tab2:
    # 1) Simple query to get distinct content types (plus POP)
    content_type_query = """
    SELECT DISTINCT content_type
    FROM `opa_hybrid.submission` s
    LEFT JOIN opa_hybrid.deliverable d
      ON s.deliverable_id = d.id
    WHERE review_stage != 'PENDING'
      AND DATE(JSON_VALUE(review_props, '$.created_at')) = CURRENT_DATE() - 1

    UNION ALL

    SELECT 'POP' AS content_type
    """

    # 2) Base query template where {pivot_cols} will be filled from Python
    base_query = """
    WITH subs AS (
      SELECT
        s.id AS subm_id,
        collaboration_id,
        deliverable_id,
        s.created_at AS subm_date,
        content_type,
        review_stage,
        review_props,
        reviewed_by_agent_id
      FROM opa_hybrid.submission s
      LEFT JOIN opa_hybrid.deliverable d
        ON s.deliverable_id = d.id
      WHERE review_stage != 'PENDING'
        AND DATE(JSON_VALUE(review_props, '$.created_at')) = CURRENT_DATE() - 1
    ),
    pop AS (
      SELECT
        c.id AS collaboration_id,
        pop_props,
        pop_review_props,
        pop_review_stage,
        CAST(JSON_VALUE(pop_review_props, '$.agent_id') AS INT64) AS agent_id
      FROM opa_hybrid.collaboration c
      LEFT JOIN opa_hybrid.campaign cam
        ON c.campaign_id = cam.id
      WHERE platform IN ('product_trials', 'instagram_and_product_trials')
        AND pop_review_stage IN ('APPROVED', 'REJECTED')
        AND DATE(JSON_VALUE(pop_review_props, '$.created_at')) = CURRENT_DATE() - 1
    ),
    agent AS (
      SELECT
        id AS agent_id,
        CONCAT(given_name, ' ', family_name) AS name
      FROM opa_hybrid.agent
    ),
    final_data AS (
      SELECT
        agent_name,
        content_type,
        breakup
      FROM (
        SELECT
          name AS agent_name,
          content_type,
          CONCAT(
            'Total : ',
            submissions_rated,
            ' \n',
            'APPROVED : ',
            ROUND(approved / submissions_rated * 100, 0),
            '%',
            ' \n',
            'REJECTED : ',
            ROUND(rejected / submissions_rated * 100, 0),
            '%'
          ) AS breakup
        FROM (
          SELECT
            reviewed_by_agent_id AS agent_id,
            name,
            content_type,
            COUNT(DISTINCT subm_id) AS submissions_rated,
            COUNT(DISTINCT IF(review_stage = 'APPROVED', subm_id, NULL)) AS approved,
            COUNT(DISTINCT IF(review_stage = 'REJECTED', subm_id, NULL)) AS rejected
          FROM subs s
          LEFT JOIN agent a
            ON s.reviewed_by_agent_id = a.agent_id
          GROUP BY 1, 2, 3
        )
        UNION ALL
        SELECT
          agent_name,
          content_type,
          CONCAT(
            'Total : ',
            pop_rated,
            ' \n',
            'APPROVED : ',
            ROUND(approved / pop_rated * 100, 0),
            '%',
            ' \n',
            'REJECTED : ',
            ROUND(rejected / pop_rated * 100, 0),
            '%'
          ) AS breakup
        FROM (
          SELECT
            name AS agent_name,
            'POP' AS content_type,
            COUNT(DISTINCT collaboration_id) AS pop_rated,
            COUNT(DISTINCT IF(pop_review_stage = 'APPROVED', collaboration_id, NULL)) AS approved,
            COUNT(DISTINCT IF(pop_review_stage = 'REJECTED', collaboration_id, NULL)) AS rejected
          FROM pop p
          LEFT JOIN agent a
            ON p.agent_id = a.agent_id
          GROUP BY 1, 2
        )
      )
    )
    SELECT *
    FROM final_data
    PIVOT (
      ANY_VALUE(breakup)
      FOR content_type IN ({pivot_cols})
    )
    ORDER BY agent_name
    """

    if 'df2' not in st.session_state:
        try:
            with st.spinner("Executing query..."):
                # First query: get dynamic list of content types
                ct_df = query_bigquery(content_type_query)

                if ct_df.empty or 'content_type' not in ct_df.columns:
                    st.warning("No content types found for the given date.")
                    st.session_state.df2 = pd.DataFrame()
                else:
                    # Build the pivot column list like: 'image' AS image, 'POP' AS POP, ...
                    pivot_parts = []
                    for ct in ct_df['content_type'].dropna().unique():
                        ct_str = str(ct)
                        alias = re.sub(r'[^a-zA-Z0-9]', '_', ct_str)
                        pivot_parts.append(f"'{ct_str}' AS {alias}")
                    pivot_cols_sql = ", ".join(pivot_parts)

                    final_query = base_query.format(pivot_cols=pivot_cols_sql)
                    st.session_state.df2 = query_bigquery(final_query)

                st.success(f"Query executed successfully! Found {len(st.session_state.df2)} rows.")
        except Exception as e:
            st.error(f"Error executing query: {str(e)}")
            st.session_state.df2 = pd.DataFrame()
    
    if not st.session_state.df2.empty:
        filtered_df2 = st.session_state.df2.reset_index(drop=True)
        
        st.write(f"Showing {len(filtered_df2)} rows")
        
        st.markdown("""
        <style>
        div[data-testid="stDataFrame"] table td,
        div[data-testid="stDataFrame"] table th {
            white-space: normal !important;
            word-wrap: break-word !important;
            overflow-wrap: break-word !important;
        }
        div[data-testid="stDataFrame"] table {
            table-layout: auto !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.dataframe(filtered_df2, use_container_width=True)
