"""
Streamlit app for BigQuery data querying and predictions.
"""
# Workaround for numpy.fft import issue with numpy 2.0+
try:
    import numpy
    # Fix for numpy 2.0 compatibility issue
    if not hasattr(numpy.fft, '__all__'):
        numpy.fft.__all__ = [
            'fft', 'ifft', 'fft2', 'ifft2', 'fftn', 'ifftn',
            'rfft', 'irfft', 'rfft2', 'irfft2', 'rfftn', 'irfftn',
            'hfft', 'ihfft', 'fftfreq', 'rfftfreq', 'fftshift', 'ifftshift'
        ]
except (ImportError, AttributeError):
    pass

import streamlit as st
import pandas as pd
import os
from bigquery_utils import query_bigquery, active_users_query
from predictor import PRODUCT_UTILITY_SCORE, BRAND_SCORE
from feasibility import calculate_feasibility
from multiplier_calc import calculate_collaborations, DEFAULT_SAFETY_NUMBER


# Page configuration - must be called before any other Streamlit commands
# This will only execute when Streamlit runs the script
try:
    st.set_page_config(
        page_title="Collaboration Predictor",
        page_icon="📊",
        layout="wide"
    )
except Exception:
    # Ignore if running outside Streamlit context (e.g., during import)
    pass


def apply_filters(df, product_utility, brand_score, price_comfort_min, price_comfort_max, 
                  quantity_min, quantity_max, num_products_min, num_products_max, asin_repeat):
    """Apply filters to the dataframe"""
    filtered_df = df.copy()
    
    # Note: These filters assume the dataframe has columns matching these filter names
    # You may need to adjust based on your actual BigQuery schema
    
    # Apply filters based on available columns
    # This is a template - adjust column names based on your actual data structure
    
    return filtered_df


def main():
    # Initialize session state
    if 'active_users_data' not in st.session_state:
        st.session_state.active_users_data = None
    if 'filtered_count' not in st.session_state:
        st.session_state.filtered_count = 0
    if 'collaboration_result' not in st.session_state:
        st.session_state.collaboration_result = None
    if 'filtered_df' not in st.session_state:
        st.session_state.filtered_df = None
    
    st.title("📊 Collaboration Predictor Dashboard")
    st.markdown("Analyze collaboration data and active users")
    
    # Main content area with tabs
    tab1, tab2 = st.tabs(["📈 Summary Dashboard", "👥 Active Users"])
    
    # Tab 1: Summary Dashboard
    with tab1:
        st.header("📈 Summary Dashboard")
        
        # Top-level filters
        st.subheader("🔍 Top-Level Filters")
        top_col1, top_col2 = st.columns(2)
        
        with top_col1:
            campaign_type = st.selectbox(
                "Type of Campaign",
                ["Barter", "Cashback", "Payout", "Barter with Payout", "Other"],
                index=0
            )
            
        with top_col2:
            platform = st.selectbox(
                "Platform",
                [
                    "youtube",
                    "instagram",
                    "content_creation",
                    "ecommerce_website",
                    "amazon",
                    "flipkart",
                    "myntra",
                    "nykaa",
                    "purplle",
                    "healthkart",
                    "sublime",
                    "1mg",
                    "snapdeal",
                    "bigbasket",
                    "swiggy",
                    "tira",
                    "swiggy_instamart",
                    "blinkit",
                    "zepto",
                    "meesho",
                    "jiomart",
                    "firstcry"
                ],
                index=0
            )
        
        st.divider()
        
        # Conditional sub-filters based on platform
        st.subheader("📋 Sub-Filters")
        
        # Initialize filter variables
        gender = None
        avg_price_or_incentive = None
        location_specific = None
        locations = None
        utility_score = None
        product_desirability = None
        
        if platform in ["instagram", "youtube"]:
            # Filters for IG/YT platforms
            st.write("**Platform: Instagram/YouTube Filters**")
            
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                gender = st.selectbox("Gender", ["Male", "Female", "Mixed"], index=2)
                utility_score = st.selectbox(
                    "Utility of the Product (out of 10)",
                    options=list(range(1, 11)),
                    index=4,  # Default to 5
                    key="utility_score_igyt"
                )
                product_desirability = st.selectbox(
                    "Product Desirability (out of 10)",
                    options=list(range(1, 11)),
                    index=4,  # Default to 5
                    key="product_desirability_igyt"
                )
            
            with filter_col2:
                avg_price_or_incentive = st.number_input(
                    "Total incentive amount (Please add the total price of the product or the amount incentive involved)",
                    value=0,
                    step=1,
                    min_value=0,
                    key="total_incentive_igyt"
                )
                
                location_specific = st.selectbox("Location Specific", ["Yes", "No"], index=1)
                
                if location_specific == "Yes":
                    # Indian states list
                    indian_states = [
                        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
                        "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
                        "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
                        "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
                        "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
                        "Uttar Pradesh", "Uttarakhand", "West Bengal",
                        "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli",
                        "Daman and Diu", "Delhi", "Jammu and Kashmir", "Ladakh",
                        "Lakshadweep", "Puducherry"
                    ]
                    locations = st.multiselect("Select Locations (States)", indian_states)
        
        else:
            # Filters for other platforms (Amazon, Nykaa, Flipkart, Blinkit)
            st.write(f"**Platform: {platform} Filters**")
            
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                gender = st.selectbox("Gender", ["Male", "Female", "Mixed"], index=2, key="gender_other")
                utility_score = st.selectbox(
                    "Utility of the Product (out of 10)",
                    options=list(range(1, 11)),
                    index=4,  # Default to 5
                    key="utility_score"
                )
                avg_price_or_incentive = st.number_input(
                    "Total incentive amount (Please add the total price of the product or the amount incentive involved)",
                    value=0,
                    step=1,
                    min_value=0,
                    key="total_incentive_other"
                )
            
            with filter_col2:
                location_specific = st.selectbox("Location Specific", ["Yes", "No"], index=1, key="loc_specific_other")
                
                if location_specific == "Yes":
                    indian_states = [
                        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
                        "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand",
                        "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur",
                        "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Punjab",
                        "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana", "Tripura",
                        "Uttar Pradesh", "Uttarakhand", "West Bengal",
                        "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli",
                        "Daman and Diu", "Delhi", "Jammu and Kashmir", "Ladakh",
                        "Lakshadweep", "Puducherry"
                    ]
                    locations = st.multiselect("Select Locations (States)", indian_states, key="locations_other")
                
                product_desirability = st.selectbox(
                    "Product Desirability (out of 10)",
                    options=list(range(1, 11)),
                    index=4,  # Default to 5
                    key="product_desirability"
                )
        
        # Apply Filters Button - Always visible after all filters
        st.divider()
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            apply_button = st.button("🔍 Apply Filters", type="primary", use_container_width=True)
        
        if apply_button:
            try:
                with st.spinner("Fetching data from BigQuery and applying filters..."):
                    # Step 1: Run active_users_query
                    all_users_df = query_bigquery(active_users_query)
                    
                    if all_users_df.empty:
                        st.warning("⚠️ No data returned from BigQuery.")
                        st.session_state.collaboration_result = None
                        st.session_state.filtered_df = None
                    else:
                        # Print total rows before filtering
                        total_rows_before_filters = len(all_users_df)
                        print(f"📊 Total rows from BigQuery (before filters): {total_rows_before_filters:,}")
                        
                        # Step 2: Filter by platform and campaign type (execution_type)
                        filtered_df = all_users_df.copy()
                        # print(filtered_df.head())
                        
                        # Map campaign type from UI to database values
                        campaign_type_map = {
                            "Barter": ["regular_barter", "barter_brand_shipment"],
                            "Cashback": ["order_and_payout"],
                            "Payout": ["regular_payout"],
                            "Barter with Payout": ["barter_with_payout"],
                            "Other": ["other"]
                        }
                        
                        # Filter by platform (check if platform string is present in platform column)
                        if platform:
                            rows_before_platform = len(filtered_df)
                            # Use contains to check if platform string is present in the column
                            filtered_df = filtered_df[filtered_df['platform'].str.contains(platform, case=False, na=False)]
                            rows_after_platform = len(filtered_df)
                            print(f"🔍 After platform filter (contains '{platform}'): {rows_before_platform:,} → {rows_after_platform:,} rows")
                        
                        # Filter by execution_type (campaign type) - handle multiple values
                        if campaign_type and campaign_type in campaign_type_map:
                            db_execution_types = campaign_type_map[campaign_type]
                            rows_before_execution = len(filtered_df)
                            # If it's a list, use isin() to match any value in the list
                            if isinstance(db_execution_types, list):
                                # Filter for users matching ANY of the execution types in the list
                                filtered_df = filtered_df[filtered_df['execution_type'].isin(db_execution_types)]
                                print(f"🔍 Filtering execution_type for: {', '.join(db_execution_types)}")
                            else:
                                filtered_df = filtered_df[filtered_df['execution_type'] == db_execution_types]
                                print(f"🔍 Filtering execution_type for: {db_execution_types}")
                            rows_after_execution = len(filtered_df)
                            print(f"🔍 After execution_type filter ({campaign_type}): {rows_before_execution:,} → {rows_after_execution:,} rows")
                        
                        # Step 3: Filter where accepted_180 > 0 AND completed_180 > 0
                        rows_before_active = len(filtered_df)
                        if 'accepted_180' in filtered_df.columns and 'completed_180' in filtered_df.columns:
                            filtered_df = filtered_df   [
                                (filtered_df['accepted_180'] > 0) & 
                                (filtered_df['completed_180'] > 0)
                            ]
                            rows_after_active = len(filtered_df)
                            print(f"🔍 After active users filter (accepted_180 > 0 AND completed_180 > 0): {rows_before_active:,} → {rows_after_active:,} rows")
                        else:
                            st.warning("⚠️ Required columns (accepted_180, completed_180) not found in data.")
                            filtered_df = pd.DataFrame()  # Empty dataframe
                            print(f"⚠️ Missing columns - filtered_df set to empty")
                        
                        # Step 4: Filter by gender if gender is selected
                        if gender and gender != "Mixed":
                            rows_before_gender = len(filtered_df)
                            if 'gender' in filtered_df.columns:
                                # Map UI gender values to database values (case-insensitive)
                                gender_map = {
                                    "Male": ["male", "m", "M"],
                                    "Female": ["female", "f", "F"]
                                }
                                if gender in gender_map:
                                    # Filter for users matching the selected gender (case-insensitive)
                                    gender_values = gender_map[gender]
                                    filtered_df = filtered_df[filtered_df['gender'].notna()]
                                    filtered_df['gender_lower'] = filtered_df['gender'].str.lower()
                                    filtered_df = filtered_df[filtered_df['gender_lower'].isin([g.lower() for g in gender_values])]
                                    filtered_df = filtered_df.drop(columns=['gender_lower'])
                                    rows_after_gender = len(filtered_df)
                                    print(f"🔍 After gender filter ({gender}): {rows_before_gender:,} → {rows_after_gender:,} rows")
                                else:
                                    print(f"⚠️ Unknown gender value: {gender}")
                            else:
                                st.warning("⚠️ Gender column not found in data. Gender filtering skipped.")
                                print(f"⚠️ Gender column missing - gender filtering skipped")
                                print(f"   Available columns: {', '.join(filtered_df.columns.tolist())}")
                        
                        # Step 5: Filter by location (state) if location_specific is "Yes" and locations are selected
                        if location_specific == "Yes" and locations and len(locations) > 0:
                            rows_before_location = len(filtered_df)
                            if 'state' in filtered_df.columns:
                                # Filter for users in the selected states (case-insensitive matching)
                                # Handle null values properly - only filter non-null states
                                filtered_df = filtered_df[filtered_df['state'].notna()]
                                # Convert to lowercase for case-insensitive comparison
                                filtered_df['state_lower'] = filtered_df['state'].str.lower()
                                locations_lower = [loc.lower() for loc in locations]
                                filtered_df = filtered_df[filtered_df['state_lower'].isin(locations_lower)]
                                # Drop the temporary column
                                filtered_df = filtered_df.drop(columns=['state_lower'])
                                rows_after_location = len(filtered_df)
                                print(f"🔍 After location filter (states: {', '.join(locations)}): {rows_before_location:,} → {rows_after_location:,} rows")
                            else:
                                st.warning("⚠️ State column not found in data. Location filtering skipped.")
                                print(f"⚠️ State column missing - location filtering skipped")
                                print(f"   Available columns: {', '.join(filtered_df.columns.tolist())}")
                        
                        # Step 6: Count remaining users
                        filtered_count = len(filtered_df)
                        print(f"✅ Final filtered count: {filtered_count:,} users")
                        
                        # Step 7: Calculate collaborations using multiplier
                        if filtered_count > 0:
                            # Get values for multiplier calculation from user inputs
                            # Use the filter input values directly (pass through even if 0, as 0 is a valid input)
                            avg_price_from_data = avg_price_or_incentive if avg_price_or_incentive and avg_price_or_incentive > 0 else None
                            # For utility and desirability, pass the value if it's set (including 0)
                            utility_from_data = utility_score if utility_score is not None else None
                            desirability_from_data = product_desirability if product_desirability is not None else None
                            
                            # Print values being used for multiplier calculation
                            print(f"📊 Multiplier calculation inputs:")
                            print(f"   - Filtered Count: {filtered_count:,}")
                            print(f"   - Product Desirability: {desirability_from_data}")
                            print(f"   - Utility Score: {utility_from_data}")
                            print(f"   - Average Price: {avg_price_from_data}")
                            print(f"   - Default Safety: {DEFAULT_SAFETY_NUMBER}")
                            
                            # Calculate collaborations
                            collaboration_result = calculate_collaborations(
                                filtered_count=filtered_count,
                                product_desirability=desirability_from_data,
                                average_price=avg_price_from_data,
                                utility_score=utility_from_data,
                                default_safety=DEFAULT_SAFETY_NUMBER
                            )
                            
                            print(f"📊 Multiplier result: {collaboration_result['multiplier']:.4f}")
                            print(f"📊 Total collaborations: {collaboration_result['total_collaborations']:,}")
                            
                            st.session_state.collaboration_result = collaboration_result
                            st.session_state.filtered_df = filtered_df
                            st.success(f"✅ Filters applied successfully! Found {filtered_count:,} active users.")
                        else:
                            st.warning("⚠️ No active users found with the selected filters (accepted_90 > 0 AND completed_90 > 0).")
                            st.session_state.collaboration_result = None
                            st.session_state.filtered_df = None
            
            except Exception as e:
                st.error(f"❌ Error applying filters: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
                st.info("💡 Tip: Make sure your BigQuery connection is working and the query returns expected columns.")
            
            except Exception as e:
                st.error(f"❌ Error applying filters: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
                st.info("💡 Tip: Make sure your BigQuery schema matches the expected column names. You may need to adjust column names in the code.")
        
        # Display Results (always show if available)
        st.divider()
        st.subheader("📊 Collaboration Results")
        
        if 'collaboration_result' in st.session_state and st.session_state.collaboration_result:
            result = st.session_state.collaboration_result
            
            # Main metrics - Side by side
            col1, col2 = st.columns(2)
            with col1:
                st.metric(
                    label="📊 Max Collaborations That Can Be Executed",
                    value=f"{result['filtered_count']:,}"
                )
            
            with col2:
                st.metric(
                    label="🎯 Collaborations That Can Be Executed (safe)",
                    value=f"{result['total_collaborations']:,}",
                    delta=f"Multiplier: {result['multiplier']:.3f}"
                )
            
            # Additional details in expander
            with st.expander("📋 Detailed Calculation Information"):
                st.write(f"**Filtered Results from BigQuery:** {result['filtered_count']:,}")
                st.write(f"**Multiplier Applied:** {result['multiplier']:.3f}")
                st.write(f"**Total Collaborations:** {result['total_collaborations']:,}")
                
                st.divider()
                st.write("**Multiplier Factors:**")
                if result['product_desirability'] is not None:
                    st.write(f"- Product Desirability: {result['product_desirability']:.1f}/10")
                if result['utility_score'] is not None:
                    st.write(f"- Utility Score: {result['utility_score']:.1f}/10")
                if result['average_price'] is not None:
                    st.write(f"- Average Price: ₹{result['average_price']:.2f}")
                st.write(f"- Default Safety Number: {result['default_safety']:.2f}")
                
                st.divider()
                st.write("**Calculation:**")
                st.write(f"Total Collaborations = Filtered Count × Multiplier")
                st.write(f"Total Collaborations = {result['filtered_count']:,} × {result['multiplier']:.3f}")
                st.write(f"Total Collaborations = {result['total_collaborations']:,}")
                
                st.info("💡 Edit `multiplier_calc.py` to adjust the multiplier calculation logic.")
            
            # Show sample of filtered data
            if 'filtered_df' in st.session_state and st.session_state.filtered_df is not None:
                with st.expander("👀 View Filtered Data Sample"):
                    st.dataframe(st.session_state.filtered_df.head(10), use_container_width=True)
                    st.caption(f"Showing 10 of {len(st.session_state.filtered_df)} filtered records")
        
        else:
            st.info("👆 Apply filters to see collaboration results")
    
    # Tab 2: Active Users Table
    with tab2:
        st.header("👥 Active Users Data")
        
        # Load data button for Active Users tab
        if st.button("📥 Load Active Users Data", type="primary"):
            try:
                with st.spinner("Loading active users data..."):
                    st.session_state.active_users_data = query_bigquery(active_users_query)
                    st.success("✅ Data loaded successfully!")
            except Exception as e:
                st.error(f"❌ Error loading data: {str(e)}")
        
        # Check if data is available
        if 'active_users_data' in st.session_state and st.session_state.active_users_data is not None:
            active_users_df = st.session_state.active_users_data
        else:
            active_users_df = None
        
        if active_users_df is None or active_users_df.empty:
            st.info("👆 Click 'Load Active Users Data' button to fetch data from BigQuery.")
        else:
            # Filters section
            st.subheader("🔍 Filters")
            
            filter_col1, filter_col2 = st.columns(2)
            
            with filter_col1:
                # Platform filter
                if 'platform' in active_users_df.columns:
                    unique_platforms = ['All'] + sorted(active_users_df['platform'].dropna().unique().tolist())
                    selected_platform = st.selectbox("Platform", unique_platforms, index=0)
                else:
                    selected_platform = "All"
                
                # Execution type filter
                if 'execution_type' in active_users_df.columns:
                    unique_execution_types = ['All'] + sorted(active_users_df['execution_type'].dropna().unique().tolist())
                    selected_execution_type = st.selectbox("Execution Type", unique_execution_types, index=0)
                else:
                    selected_execution_type = "All"
            
            with filter_col2:
                # Acceptance filters
                st.write("**Acceptance Filters (Greater Than)**")
                accepted_min = st.number_input("Accepted (min)", value=0, min_value=0, step=1, key="au_accepted")
                accepted_90_min = st.number_input("Accepted 90 (min)", value=0, min_value=0, step=1, key="au_accepted_90")
                accepted_180_min = st.number_input("Accepted 180 (min)", value=0, min_value=0, step=1, key="au_accepted_180")
            
            filter_col3, filter_col4 = st.columns(2)
            
            with filter_col3:
                # Completion filters
                st.write("**Completion Filters (Greater Than)**")
                completed_min = st.number_input("Completed (min)", value=0, min_value=0, step=1, key="au_completed")
                completed_90_min = st.number_input("Completed 90 (min)", value=0, min_value=0, step=1, key="au_completed_90")
                completed_180_min = st.number_input("Completed 180 (min)", value=0, min_value=0, step=1, key="au_completed_180")
            
            with filter_col4:
                # Additional filters
                st.write("**Additional Filters**")
                if 'accepted_30' in active_users_df.columns:
                    accepted_30_min = st.number_input("Accepted 30 (min)", value=0, min_value=0, step=1, key="au_accepted_30")
                else:
                    accepted_30_min = 0
                
                if 'completed_60' in active_users_df.columns:
                    completed_60_min = st.number_input("Completed 60 (min)", value=0, min_value=0, step=1, key="au_completed_60")
                else:
                    completed_60_min = 0
                
                if 'invited' in active_users_df.columns:
                    invited_min = st.number_input("Invited (min)", value=0, min_value=0, step=1, key="au_invited")
                else:
                    invited_min = 0
            
            # Apply filters to dataframe
            filtered_active_users_df = active_users_df.copy()
            
            # Platform filter
            if selected_platform != "All" and 'platform' in filtered_active_users_df.columns:
                filtered_active_users_df = filtered_active_users_df[filtered_active_users_df['platform'] == selected_platform]
            
            # Execution type filter
            if selected_execution_type != "All" and 'execution_type' in filtered_active_users_df.columns:
                filtered_active_users_df = filtered_active_users_df[filtered_active_users_df['execution_type'] == selected_execution_type]
            
            # Acceptance filters
            if 'accepted' in filtered_active_users_df.columns:
                filtered_active_users_df = filtered_active_users_df[filtered_active_users_df['accepted'] >= accepted_min]
            if 'accepted_90' in filtered_active_users_df.columns:
                filtered_active_users_df = filtered_active_users_df[filtered_active_users_df['accepted_90'] >= accepted_90_min]
            if 'accepted_180' in filtered_active_users_df.columns:
                filtered_active_users_df = filtered_active_users_df[filtered_active_users_df['accepted_180'] >= accepted_180_min]
            if 'accepted_30' in filtered_active_users_df.columns:
                filtered_active_users_df = filtered_active_users_df[filtered_active_users_df['accepted_30'] >= accepted_30_min]
            
            # Completion filters
            if 'completed' in filtered_active_users_df.columns:
                filtered_active_users_df = filtered_active_users_df[filtered_active_users_df['completed'] >= completed_min]
            if 'completed_90' in filtered_active_users_df.columns:
                filtered_active_users_df = filtered_active_users_df[filtered_active_users_df['completed_90'] >= completed_90_min]
            if 'completed_180' in filtered_active_users_df.columns:
                filtered_active_users_df = filtered_active_users_df[filtered_active_users_df['completed_180'] >= completed_180_min]
            if 'completed_60' in filtered_active_users_df.columns:
                filtered_active_users_df = filtered_active_users_df[filtered_active_users_df['completed_60'] >= completed_60_min]
            
            # Invited filter
            if 'invited' in filtered_active_users_df.columns:
                filtered_active_users_df = filtered_active_users_df[filtered_active_users_df['invited'] >= invited_min]
            
            # Show filter results summary
            st.info(f"📊 Showing {len(filtered_active_users_df):,} of {len(active_users_df):,} users after filters")
            
            st.divider()
            
            # Pagination settings
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                items_per_page = st.selectbox(
                    "Items per page",
                    [10, 25, 50, 100],
                    index=1
                )
            
            # Calculate pagination based on filtered data
            total_rows = len(filtered_active_users_df)
            total_pages = (total_rows - 1) // items_per_page + 1 if total_rows > 0 else 1
            
            # Page selector
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                page_number = st.number_input(
                    "Page",
                    min_value=1,
                    max_value=total_pages,
                    value=1,
                    step=1
                )
            
            # Calculate slice
            start_idx = (page_number - 1) * items_per_page
            end_idx = start_idx + items_per_page
            
            # Display paginated data (from filtered dataframe)
            paginated_df = filtered_active_users_df.iloc[start_idx:end_idx]
            
            st.dataframe(
                paginated_df,
                use_container_width=True,
                height=400
            )
            
            # Pagination info
            st.caption(
                f"Showing {start_idx + 1} to {min(end_idx, total_rows)} of {total_rows} users "
                f"(Page {page_number} of {total_pages})"
            )
            
            # Download buttons
            col1, col2 = st.columns(2)
            with col1:
                csv_filtered = filtered_active_users_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Filtered Data (CSV)",
                    data=csv_filtered,
                    file_name="active_users_filtered.csv",
                    mime="text/csv"
                )
            with col2:
                csv_all = active_users_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Full Dataset (CSV)",
                    data=csv_all,
                    file_name="active_users_all.csv",
                    mime="text/csv"
                )


if __name__ == "__main__":
    main()
