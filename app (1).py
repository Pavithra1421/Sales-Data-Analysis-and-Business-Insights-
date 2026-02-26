import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ────────────────────────────────────────────────
# Page Configuration
# ────────────────────────────────────────────────
st.set_page_config(
    page_title="Retail Sales Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("Retail Sales Analysis & Business Insights Dashboard")

st.markdown("""
This dashboard analyzes historical retail sales data to uncover key trends, top-performing products, regional performance, seasonal patterns, and customer insights.
""")

# ────────────────────────────────────────────────
# 1. Data Loading with Caching
# ────────────────────────────────────────────────
@st.cache_data
def load_data():
    return pd.read_csv("train.csv")

df = load_data()

st.success(f"Dataset loaded successfully — {df.shape[0]:,} rows × {df.shape[1]} columns")

# ────────────────────────────────────────────────
# 2. Data Cleaning & Preprocessing
# ────────────────────────────────────────────────
with st.expander("Data Cleaning & Preprocessing", expanded=True):
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Dataset Overview")
        st.write(f"**Rows:** {df.shape[0]:,}")
        st.write(f"**Columns:** {df.shape[1]}")
        st.write("**Column Names:**", df.columns.tolist())

    with col2:
        st.subheader("Missing Values")
        missing = df.isnull().sum()
        if missing.sum() > 0:
            st.write(missing[missing > 0])
            df = df.dropna(subset=['Order Date', 'Sales'])
        else:
            st.success("No missing values detected.")

    # Remove duplicates
    duplicates = df.duplicated().sum()
    st.write(f"**Duplicate rows found:** {duplicates}")
    if duplicates > 0:
        df = df.drop_duplicates()
        st.success(f"Duplicates removed. New shape: {df.shape}")

    # Convert date column
    df['Order Date'] = pd.to_datetime(df['Order Date'], format='%d/%m/%Y', errors='coerce')
    invalid_dates = df['Order Date'].isnull().sum()
    if invalid_dates > 0:
        st.warning(f"Dropped {invalid_dates} rows with invalid dates.")
        df = df.dropna(subset=['Order Date'])

    st.write("**Cleaned Dataset Shape:**", df.shape)
    st.dataframe(df.head(5), use_container_width=True)

# ────────────────────────────────────────────────
# Important Note: Missing Profit / Cost Columns
# ────────────────────────────────────────────────
if 'Profit' not in df.columns:
    st.warning("""
    **Note:** This dataset does not contain 'Profit', 'Cost Price' or 'Quantity' columns.  
    Therefore, profit margin analysis and loss-making products cannot be calculated.  
    All insights are based on **Sales** value only.
    """)

# ────────────────────────────────────────────────
# Sidebar Filters
# ────────────────────────────────────────────────
st.sidebar.header("Filters")
selected_regions = st.sidebar.multiselect(
    "Region",
    options=sorted(df['Region'].unique()),
    default=df['Region'].unique()
)

selected_categories = st.sidebar.multiselect(
    "Category",
    options=sorted(df['Category'].unique()),
    default=df['Category'].unique()
)

# Apply filters
filtered_df = df[
    (df['Region'].isin(selected_regions)) &
    (df['Category'].isin(selected_categories))
]

# ────────────────────────────────────────────────
# Key Performance Indicators (KPIs)
# ────────────────────────────────────────────────
st.header("Key Business Metrics")
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Revenue", f"${filtered_df['Sales'].sum():,.2f}")
col2.metric("Total Orders", filtered_df['Order ID'].nunique())
col3.metric("Unique Products", filtered_df['Product Name'].nunique())
col4.metric("Unique Customers", filtered_df['Customer Name'].nunique())

# ────────────────────────────────────────────────
# Main Insights Tabs
# ────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Top Products",
    "Region Performance",
    "Category Analysis",
    "Seasonal Trends",
    "Customer Insights"
])

# ───── Tab 1 ─────
with tab1:
    st.subheader("Top Performing Products by Revenue")
    top_products = (
        filtered_df.groupby(['Product Name', 'Category'])['Sales']
        .sum()
        .reset_index()
        .sort_values('Sales', ascending=False)
        .head(15)
    )

    fig1 = px.bar(
        top_products,
        x='Sales',
        y='Product Name',
        orientation='h',
        color='Category',
        title="Top 15 Products by Total Sales",
        labels={'Sales': 'Total Sales (USD)'},
        height=550
    )
    st.plotly_chart(fig1, use_container_width=True)

    st.dataframe(
        top_products.style.format({'Sales': '${:,.2f}'}),
        use_container_width=True
    )

# ───── Tab 2 ─────
with tab2:
    st.subheader("Revenue by Region")
    region_sales = (
        filtered_df.groupby('Region')['Sales']
        .sum()
        .reset_index()
        .sort_values('Sales', ascending=False)
    )

    fig2 = px.pie(
        region_sales,
        names='Region',
        values='Sales',
        title="Revenue Distribution by Region"
    )
    st.plotly_chart(fig2)

    fig2b = px.bar(
        region_sales,
        x='Region',
        y='Sales',
        title="Total Revenue per Region",
        text_auto=True
    )
    st.plotly_chart(fig2b, use_container_width=True)

    if not region_sales.empty:
        top_region = region_sales.iloc[0]
        st.success(f"**Top Performing Region:** {top_region['Region']} — ${top_region['Sales']:,.2f}")

# ───── Tab 3 ─────
with tab3:
    st.subheader("Performance by Category & Sub-Category")

    cat_sales = filtered_df.groupby('Category')['Sales'].sum().reset_index()
    fig3 = px.pie(cat_sales, names='Category', values='Sales', title="Sales Share by Category")
    st.plotly_chart(fig3)

    subcat_sales = (
        filtered_df.groupby(['Category', 'Sub-Category'])['Sales']
        .sum()
        .reset_index()
        .sort_values('Sales', ascending=False)
        .head(20)
    )

    fig3b = px.bar(
        subcat_sales,
        x='Sales',
        y='Sub-Category',
        color='Category',
        orientation='h',
        title="Top 20 Sub-Categories by Revenue",
        height=650
    )
    st.plotly_chart(fig3b, use_container_width=True)

# ───── Tab 4 ─────
with tab4:
    st.subheader("Seasonal & Yearly Sales Trends")

    df_season = filtered_df.copy()
    df_season['Month'] = df_season['Order Date'].dt.strftime('%B')
    df_season['Year'] = df_season['Order Date'].dt.year

    monthly = (
        df_season.groupby(['Year', 'Month'])['Sales']
        .sum()
        .reset_index()
    )

    month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']

    monthly['Month'] = pd.Categorical(monthly['Month'], categories=month_order, ordered=True)
    monthly = monthly.sort_values(['Year', 'Month'])

    fig4 = px.line(
        monthly,
        x='Month',
        y='Sales',
        color='Year',
        markers=True,
        title="Monthly Sales Trend Across Years"
    )
    st.plotly_chart(fig4, use_container_width=True)

    yearly = df_season.groupby('Year')['Sales'].sum().reset_index()
    fig4b = px.bar(yearly, x='Year', y='Sales', title="Annual Revenue Trend")
    st.plotly_chart(fig4b)

# ───── Tab 5 ─────
with tab5:
    st.subheader("Top Customers by Revenue")

    top_customers = (
        filtered_df.groupby(['Customer Name', 'Segment'])['Sales']
        .sum()
        .reset_index()
        .sort_values('Sales', ascending=False)
        .head(15)
    )

    fig5 = px.bar(
        top_customers,
        x='Sales',
        y='Customer Name',
        color='Segment',
        orientation='h',
        title="Top 15 Customers by Total Revenue",
        height=550
    )
    st.plotly_chart(fig5, use_container_width=True)

# ────────────────────────────────────────────────
# Download Section
# ────────────────────────────────────────────────
st.header("Export Data")
csv = filtered_df.to_csv(index=False).encode('utf-8')

st.download_button(
    label="Download Filtered Dataset (CSV)",
    data=csv,
    file_name="filtered_sales_data.csv",
    mime="text/csv"
)

st.caption("Retail Sales Analytics Dashboard • Built for professional reporting & insights")
