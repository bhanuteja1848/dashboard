import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import io

# Load dataset
@st.cache_data
def load_data():
    # Load both datasets
    wanderdoll_df = pd.read_csv("wanderdoll_cleaned.csv")
    oddmuse_df = pd.read_csv("odd_muse_cleaned.csv")  # Add your Odd Muse file
    
    # Add brand column to each dataset
    wanderdoll_df["brand"] = "Wanderdoll"
    oddmuse_df["brand"] = "Odd Muse"
    
    # Combine datasets
    df = pd.concat([wanderdoll_df, oddmuse_df], ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    
    # Check for duplicates and remove them
    original_count = len(df)
    df = df.drop_duplicates(subset=["brand", "customer name", "review", "rating", "date"], keep='first')
    duplicate_count = original_count - len(df)
    return df

df = load_data()

# Define categories
categories = {
    "product_issue": ["too small", "too big", "wrong size", "poor fit", "too tight", "loose", "didn't fit", "short", "sizing",
                      "Sizing" , "fit" , "didn't fit" , "too loose","height", "weight" , "poor sizing", "wrong size", "poor sizing information", 
                      "lack of sizing information", "wrong sizing information","ordered wrong size", "don't know my size", "didn't know which size",
                    "which size" , "what's the length" , "what's the size" , "how tall" , "what size" , "is this suitable for" , "idk which size" , 
                      "what size is the model wearing ?", "How tall is the model?","Would this fit ?"],
    "service_issue": ["no reply", "didn't respond", "ignored", "bad service", "no response", "unhelpful", "rude", "messages from team", "no answer"],
    "expectation": ["refund", "return", "exchange", "compensation"],
    "delivery_issue": ["not delivered", "didn't receive", "lost order", "missing item", "delivery delay", "waiting"],
    "positive_experience": ["fantastic", "great", "smooth", "helpful", "excellent", "thank you", "amazing", "outstanding", "resolved", "fast", "quick"]
}

# Function to filter reviews by categories
def filter_by_categories(df, selected_categories):
    if not selected_categories:
        return df
    
    all_keywords = []
    for category in selected_categories:
        all_keywords.extend(categories[category])
    
    # Check if matched_keywords column exists, if not use review
    if "matched_keywords" in df.columns:
        return df[df["matched_keywords"].str.contains("|".join(all_keywords), case=False, na=False)]
    else:
        return df[df["review"].str.contains("|".join(all_keywords), case=False, na=False)]

# Dynamic title based on brand selection
# Sidebar filters
st.sidebar.header("🔍 Filters")

# Brand filter
brand_options = st.sidebar.selectbox(
    "🏷️ Select Brand",
    options=["All Brands"] + sorted(df["brand"].unique().tolist()),
    index=0
)

# Dynamic title based on brand selection
if brand_options == "All Brands":
    st.title("Multi-Brand Review Analytics Dashboard")
    brand_text = "All Brands"
else:
    st.title(f"{brand_options} Review Analytics Dashboard")
    brand_text = brand_options

# Show total dataset info
total_reviews = len(df) if brand_options == "All Brands" else len(df[df["brand"] == brand_options])
st.info(f"📊 **{brand_text}**: {total_reviews} reviews from {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")

# Create tabs
tab1, tab2 = st.tabs(["📊 Dashboard", "📋 Data"])

# Date range filter
min_date = df["date"].min()
max_date = df["date"].max()

# Date range selector
date_option = st.sidebar.selectbox(
    "📅 Date Range",
    ["All Time", "Last 6 months", "Last 12 months", "Custom"]
)

if date_option == "All Time":
    start_date = min_date
    end_date = max_date
    st.sidebar.info(f"📅 {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
elif date_option == "Last 6 months":
    start_date = max_date - timedelta(days=180)
    end_date = max_date
    st.sidebar.info(f"📅 {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
elif date_option == "Last 12 months":
    start_date = max_date - timedelta(days=365)
    end_date = max_date
    st.sidebar.info(f"📅 {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
else:  # Custom
    start_date, end_date = st.sidebar.date_input(
        "📅 Select Custom Date Range",
        [max_date - timedelta(days=365), max_date],
        min_value=min_date,
        max_value=max_date
    )

# Rating filter - Fixed to use integers instead of floats
rating_options = st.sidebar.multiselect(
    "⭐ Select Ratings",
    options=[1, 2, 3, 4, 5],  # Changed from floats to integers
    default=[1, 2, 3, 4, 5],
    format_func=lambda x: f"{x} Star{'s' if x != 1 else ''}"
)

# Category filter
st.sidebar.subheader("🏷️ Filter by Categories")
selected_categories = []

for category, keywords in categories.items():
    category_name = category.replace("_", " ").title()
    if st.sidebar.checkbox(f"{category_name}", key=category):
        selected_categories.append(category)
        with st.sidebar.expander(f"Keywords in {category_name}"):
            st.write(", ".join(keywords))

# Show all reviews option
show_all = st.sidebar.checkbox("📋 Show All Reviews (ignore category filters)", value=not bool(selected_categories))

# Apply filters
filtered_df = df.copy()

# Apply brand filter
if brand_options != "All Brands":
    filtered_df = filtered_df[filtered_df["brand"] == brand_options]

# Apply date filter
filtered_df = filtered_df[
    (filtered_df["date"] >= pd.to_datetime(start_date)) &
    (filtered_df["date"] <= pd.to_datetime(end_date))
]

# Apply rating filter - Fixed to handle data type mismatch
if rating_options:  # Only apply if ratings are selected
    # Convert both to the same type for comparison
    filtered_df = filtered_df[filtered_df["rating"].astype(int).isin(rating_options)]

# Apply category filter
if not show_all and selected_categories:
    filtered_df = filter_by_categories(filtered_df, selected_categories)

# Dashboard Tab
with tab1:
    st.header("📈 Analytics Overview")
    
    # Show filtering info
    if not show_all and selected_categories:
        category_names = [cat.replace("_", " ").title() for cat in selected_categories]
        st.info(f"🔍 Filtered by categories: {', '.join(category_names)}")
    elif show_all:
        st.info("📋 Showing all reviews (no category filter applied)")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    if not filtered_df.empty:
        with col1:
            st.metric("Total Reviews", len(filtered_df), delta=f"of {len(df)} total")
        
        with col2:
            avg_rating = filtered_df["rating"].mean()
            overall_avg = df["rating"].mean()
            delta = avg_rating - overall_avg
            st.metric("Average Rating", f"{avg_rating:.1f}", delta=f"{delta:+.1f}")
        
        with col3:
            positive_count = len(filtered_df[filtered_df["rating"] >= 4])
            positive_pct = (positive_count / len(filtered_df)) * 100
            st.metric("Positive Reviews", f"{positive_pct:.1f}%", delta=f"{positive_count} reviews")
        
        with col4:
            negative_count = len(filtered_df[filtered_df["rating"] <= 2])
            negative_pct = (negative_count / len(filtered_df)) * 100
            st.metric("Negative Reviews", f"{negative_pct:.1f}%", delta=f"{negative_count} reviews")
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            # Bar chart for ratings distribution
            st.subheader("⭐ Rating Distribution")
            rating_counts = filtered_df["rating"].value_counts().sort_index()
            fig_bar = px.bar(
                x=rating_counts.index,
                y=rating_counts.values,
                title="Reviews by Star Rating",
                labels={"x": "Star Rating", "y": "Number of Reviews"},
                color=rating_counts.values,
                color_continuous_scale="RdYlBu_r",
                text=rating_counts.values
            )
            fig_bar.update_layout(showlegend=False)
            fig_bar.update_xaxes(tickmode='array', tickvals=[1, 2, 3, 4, 5])
            fig_bar.update_traces(texttemplate='%{text}', textposition='outside')
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            # Pie chart for positive/negative reviews
            st.subheader("😊 Sentiment Distribution")
            sentiment_counts = filtered_df["rating"].apply(
                lambda x: "Positive (4-5★)" if x >= 4 else "Negative (1-2★)" if x <= 2 else "Neutral (3★)"
            ).value_counts()
            fig_pie = px.pie(
                names=sentiment_counts.index,
                values=sentiment_counts.values,
                title="Overall Sentiment",
                color_discrete_map={
                    "Positive (4-5★)": "#22c55e", 
                    "Negative (1-2★)": "#ef4444", 
                    "Neutral (3★)": "#fbbf24"
                }
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Category analysis if categories are selected
        if not show_all and selected_categories:
            st.subheader("🏷️ Category Analysis")
            
            # Show breakdown by selected categories
            category_data = []
            for category in selected_categories:
                cat_df = filter_by_categories(df, [category])
                # Apply same filters as main dashboard
                if brand_options != "All Brands":
                    cat_df = cat_df[cat_df["brand"] == brand_options]
                cat_df = cat_df[
                    (cat_df["date"] >= pd.to_datetime(start_date)) &
                    (cat_df["date"] <= pd.to_datetime(end_date)) &
                    (cat_df["rating"].astype(int).isin(rating_options))
                ]
                
                category_data.append({
                    "Category": category.replace("_", " ").title(),
                    "Count": len(cat_df),
                    "Avg Rating": cat_df["rating"].mean() if len(cat_df) > 0 else 0,
                    "Positive %": (len(cat_df[cat_df["rating"] >= 4]) / len(cat_df) * 100) if len(cat_df) > 0 else 0
                })
            
            category_df = pd.DataFrame(category_data)
            st.dataframe(category_df, use_container_width=True)
        
        # Positive vs Negative Reviews Timeline
        st.subheader("📈 Positive vs Negative Reviews Over Time")

        # Create sentiment categories
        filtered_df_timeline = filtered_df.copy()
        filtered_df_timeline['sentiment'] = filtered_df_timeline['rating'].apply(
            lambda x: 'Positive (4-5★)' if x >= 4 else 'Negative (1-2★)' if x <= 2 else 'Neutral (3★)'
        )

        # Group by date and sentiment
        timeline_df = filtered_df_timeline.groupby([filtered_df_timeline['date'].dt.date, 'sentiment']).size().reset_index()
        timeline_df.columns = ['Date', 'Sentiment', 'Count']

        if len(timeline_df) > 0:
            fig_timeline = px.line(
                timeline_df,
                x='Date',
                y='Count',
                color='Sentiment',
                title='Sentiment Trends Over Time',
                markers=True,
                color_discrete_map={
                    'Positive (4-5★)': '#22c55e',
                    'Negative (1-2★)': '#ef4444', 
                    'Neutral (3★)': '#fbbf24'
                }
            )
            fig_timeline.update_layout(
                hovermode='x unified',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_timeline, use_container_width=True)
        else:
            st.info("📊 Not enough data points for timeline visualization.")
    else:
        st.warning("⚠️ No reviews match the selected filters. Please adjust your criteria.")

# Data Tab
with tab2:
    st.header("📋 Review Data")
    
    # Additional filters specific to data view
    col1, col2 = st.columns(2)
    
    with col1:
        show_columns = st.multiselect(
            "📋 Select Columns to Display",
            options=["brand", "customer name", "rating", "review", "date", "matched_keywords"],
            default=["brand", "customer name", "rating", "date", "matched_keywords"]
        )
    
    with col2:
        sort_by = st.selectbox(
            "🔄 Sort by",
            options=["date", "rating", "customer name", "brand"],
            index=0
        )
        sort_order = st.radio("Sort Order", ["Descending", "Ascending"], horizontal=True)
    
    # Display filtered data
    if not filtered_df.empty and show_columns:
        # Sort data
        ascending = sort_order == "Ascending"
        display_df = filtered_df[show_columns].sort_values(sort_by, ascending=ascending)
        
        # Show filter summary
        filter_info = []
        if brand_options != "All Brands":
            filter_info.append(f"Brand: {brand_options}")
        if not show_all and selected_categories:
            category_names = [cat.replace("_", " ").title() for cat in selected_categories]
            filter_info.append(f"Categories: {', '.join(category_names)}")
        if len(rating_options) < 5:
            filter_info.append(f"Ratings: {', '.join([str(int(r)) for r in sorted(rating_options)])}")
        filter_info.append(f"Date: {start_date} to {end_date}")
        
        st.info(f"🔍 **Active Filters:** {' | '.join(filter_info)}")
        
        st.subheader(f"Filtered Reviews ({len(display_df)} of {len(df)} total)")
        st.dataframe(display_df, use_container_width=True, height=400)
        
        # Download section
        st.subheader("💾 Download Data")
        col1, col2 = st.columns(2)
        
        with col1:
            # CSV download
            csv_buffer = io.StringIO()
            display_df.to_csv(csv_buffer, index=False)
            filename_suffix = "_".join(selected_categories) if selected_categories else "all"
            brand_suffix = brand_options.lower().replace(" ", "_") if brand_options != "All Brands" else "all_brands"
            st.download_button(
                label="📥 Download as CSV",
                data=csv_buffer.getvalue(),
                file_name=f"{brand_suffix}_reviews_{filename_suffix}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        with col2:
            # Excel download
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                display_df.to_excel(writer, index=False, sheet_name='Reviews')
            st.download_button(
                label="📊 Download as Excel",
                data=excel_buffer.getvalue(),
                file_name=f"{brand_suffix}_reviews_{filename_suffix}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        # Data summary
        with st.expander("📈 Data Summary"):
            st.write(f"**Total Reviews:** {len(display_df)} (of {len(df)} in dataset)")
            st.write(f"**Date Range:** {display_df['date'].min().strftime('%Y-%m-%d')} to {display_df['date'].max().strftime('%Y-%m-%d')}")
            st.write(f"**Average Rating:** {display_df['rating'].mean():.1f}")
            if brand_options != "All Brands":
                st.write(f"**Brand:** {brand_options}")
            st.write("**Rating Distribution:**")
            rating_summary = display_df['rating'].value_counts().sort_index()
            for rating, count in rating_summary.items():
                percentage = (count / len(display_df)) * 100
                st.write(f"  - {int(rating)} Star: {count} reviews ({percentage:.1f}%)")
    
    else:
        st.warning("⚠️ No data to display. Please adjust your filters or select columns to show.")

# Sidebar info
st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ About")
st.sidebar.info(
    "This dashboard analyzes multi-brand reviews with categorical filtering. "
    "Select brands and categories to focus on specific types of feedback, or view all data for a complete overview."
)
