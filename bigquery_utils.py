"""
BigQuery utility functions for querying data.
"""
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
import os
from typing import Optional, Dict, Any
import streamlit as st

# Lazy initialization of BigQuery client
_client = None

def get_bigquery_client():
    """Get or create BigQuery client (lazy initialization)"""
    global _client
    if _client is None:
        try:
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"]
            )

            _client = bigquery.Client(
                credentials=credentials,
                project=credentials.project_id,
            )

        except Exception as e:
            raise Exception(
                f"Failed to initialize BigQuery client: {str(e)}"
            )

    return _client


def query_bigquery(query):
    """Execute a BigQuery query and return results as DataFrame"""
    client = get_bigquery_client()
    df = client.query(query).to_dataframe()
    return df

active_users_query="""
    WITH users as (
  SELECT user_id,
    COALESCE(plat, platform) as platform,
    execution_type,
    COUNT(c.id) as invited, 
    COUNTIF(invite_stage = 'ACCEPTED' AND is_revoked = 'false') as accepted,
    COUNTIF(invite_stage = 'ACCEPTED' AND is_revoked = 'false' AND DATE_DIFF(CURRENT_DATE(), DATE(JSON_VALUE(participation_props, '$.acceptance.created_at')), DAY) < 180) as accepted_180,
    -- COUNTIF(invite_stage = 'ACCEPTED' AND is_revoked = 'false' AND DATE_DIFF(CURRENT_DATE(), DATE(JSON_VALUE(participation_props, '$.acceptance.created_at')), DAY) < 90) as accepted_90,    
    -- COUNTIF(invite_stage = 'ACCEPTED' AND is_revoked = 'false' AND DATE_DIFF(CURRENT_DATE(), DATE(JSON_VALUE(participation_props, '$.acceptance.created_at')), DAY) < 30) as accepted_30, 
    -- COUNTIF(invite_stage = 'ACCEPTED' AND is_revoked = 'false' AND is_completed = 'true') as completed, 
    COUNTIF(invite_stage = 'ACCEPTED' AND is_revoked = 'false' AND is_completed = 'true' AND DATE_DIFF(CURRENT_DATE(), DATE(completed_at), DAY) < 180) as completed_180,
    -- COUNTIF(invite_stage = 'ACCEPTED' AND is_revoked = 'false' AND is_completed = 'true' AND DATE_DIFF(CURRENT_DATE(), DATE(completed_at), DAY) < 90) as completed_90,
    -- COUNTIF(invite_stage = 'ACCEPTED' AND is_revoked = 'false' AND is_completed = 'true' AND DATE_DIFF(CURRENT_DATE(), DATE(completed_at), DAY) < 60) as completed_60
  FROM opa_hybrid.collaboration c
  LEFT JOIN opa_hybrid.campaign cam
  ON c.campaign_id = cam.id
  LEFT JOIN (
    SELECT campaign_id, MAX(d.platform) as plat from opa_hybrid.deliverable d
    LEFT JOIN opa_hybrid.campaign cam
    ON d.campaign_id = cam.id
    WHERE cam.platform not IN('instagram', 'youtube', 'instagram_and_product_trials')
    GROUP BY 1 
  ) d
  ON c.campaign_id = d.campaign_id

  -- WHERE platform = 'product_trials'
  GROUP BY 1, 2, 3
  HAVING accepted >0
  order by 1
), 

location as (
  SELECT id, gender, state from opa_hybrid.user u
  LEFT JOIN(
    SELECT pincode, state, ROW_NUMBER() OVER(partition by pincode) as rn
    FROM `facts.dim_pincode`
    Qualify rn = 1
  ) dim
  ON CAST(JSON_VALUE(profile, '$.postcode') as INT64) = pincode
)
SELECT * EXCEPT(id) FROM users u
lEFT JOIN location l
ON u.user_id = l.id
"""



