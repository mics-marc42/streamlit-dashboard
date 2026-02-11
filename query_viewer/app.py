import streamlit as st
import pandas as pd
from bigquery_utils import query_bigquery

st.set_page_config(page_title="Query Viewer", layout="wide")

st.title("BigQuery Query Viewer")

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
    st.dataframe(filtered_df, use_container_width=True)
