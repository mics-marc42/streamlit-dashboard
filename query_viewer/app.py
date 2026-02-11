import streamlit as st
import pandas as pd
from bigquery_utils import query_bigquery

st.set_page_config(page_title="Query Viewer", layout="wide")

st.title("BigQuery Query Viewer")

query = """
DECLARE pivot_cols STRING;
SET pivot_cols = (
  SELECT STRING_AGG(
    FORMAT("'%s' AS %s",
      content_type,
      REGEXP_REPLACE(content_type, r'[^a-zA-Z0-9]', '_')
    ),
    ", "
  )
  FROM (select * FROM (
    SELECT DISTINCT content_type
    FROM `opa_hybrid.submission` s
    LEFT JOIN opa_hybrid.deliverable d
    ON s.deliverable_id = d.id
    WHERE review_stage !='PENDING'
    AND DATE(JSON_VALUE(review_props, '$.created_at')) = CURRENT_DATE() -1
  )
  UNION ALL (
    select "POP" as content_type
  )
  )
);

EXECUTE IMMEDIATE FORMAT(
'''
WITH subs as (
  SELECT s.id as subm_id, 
    collaboration_id, 
    deliverable_id, 
    s.created_at as subm_date,  
    content_type,
    review_stage,
    review_props, 
    reviewed_by_agent_id
  FROM opa_hybrid.submission s
  LEFT JOIN opa_hybrid.deliverable d
  ON s.deliverable_id = d.id
  WHERE review_stage !='PENDING'
  AND DATE(JSON_VALUE(review_props, '$.created_at')) = CURRENT_DATE() -1
),
pop as (
  SELECT c.id as collaboration_id,
    pop_props, 
    pop_review_props, 
    pop_review_stage, 
    CAST(JSON_VALUE(pop_review_props, '$.agent_id') as INT64) as agent_id
  FROM opa_hybrid.collaboration c
  LEFT JOIN opa_hybrid.campaign cam
  ON c.campaign_id = cam.id
  WHERE platform IN ('product_trials', 'instagram_and_product_trials')
  AND pop_review_stage IN ('APPROVED', 'REJECTED')
  AND DATE(JSON_VALUE(pop_review_props, '$.created_at')) = CURRENT_DATE() -1
), 
agent as (
  SELECT id as agent_id,  
    CONCAT(given_name, ' ', family_name) as name
  FROM opa_hybrid.agent
), 
final_data as(
  SELECT agent_name, 
    content_type, 
    breakup
  FROM (
    SELECT  name as agent_name, 
      content_type,
      CONCAT('Total : ', submissions_rated , '\\n','APPROVED : ', ROUND(approved/submissions_rated*100, 0),'%%',  '\\n', 'REJECTED : ', ROUND(rejected/submissions_rated*100, 0), '%%') as breakup 
    FROM (
    select reviewed_by_agent_id as agent_id, 
      name, 
      content_type, 
      COUNT(distinct subm_id) as submissions_rated, 
      COUNT(DISTINCT IF(review_stage = 'APPROVED', subm_id, NULL)) as approved, 
      COUNT(DISTINCT IF(review_stage = 'REJECTED', subm_id, NULL)) as rejected
    from subs s
    LEFT JOIN agent a
    ON s.reviewed_by_agent_id = a.agent_id
    GROUP BY  1, 2, 3
    )
    union all(
      SELECT agent_name,
        content_type, 
        CONCAT('Total : ', pop_rated, '\\n', 'APPROVED : ', ROUND(approved/pop_rated*100, 0),'%%','\\n' 'REJECTED', ' : ', ROUND(rejected/pop_rated*100, 0), '%%') as breakup
      FROM (
        SELECT name as agent_name, 
          'POP' as content_type,
          COUNT(DISTINCT collaboration_id) as pop_rated,
          COUNT(DISTINCT IF(pop_review_stage = 'APPROVED', collaboration_id, NULL)) as approved,
          COUNT(DISTINCT IF(pop_review_stage = 'REJECTED', collaboration_id, NULL)) as rejected
        FROM pop p
        LEFT join agent a 
        ON p.agent_id = a.agent_id
        GROUP BY 1,2
      )
    )
  )
) 
SELECT *
  FROM final_data
  PIVOT (
    ANY_VALUE(breakup)
    FOR content_type IN (%s)
  )
  ORDER BY agent_name
''', pivot_cols
)
"""

try:
    with st.spinner("Executing query..."):
        df = query_bigquery(query)
        st.success(f"Query executed successfully! Found {len(df)} rows.")
        st.dataframe(df, use_container_width=True)
except Exception as e:
    st.error(f"Error executing query: {str(e)}")
