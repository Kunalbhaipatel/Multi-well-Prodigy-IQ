# full_fixed_dashboard.py
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Rig Comparison Dashboard", layout="wide")
st.title("🚀 Rig Comparison Dashboard")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("Updated_Merged_Data_with_API_and_Location.csv")
    if "Efficiency Score" in df.columns and df["Efficiency Score"].isnull().all():
        df.drop(columns=["Efficiency Score"], inplace=True)
    return df

data = load_data()
filtered = data.copy()

# Filters and global search
with st.container():
    col_search, col1, col2, col3, col4 = st.columns([2.5, 1.2, 1.2, 1.2, 1.2])
    with col_search:
        st.markdown("🔍 **Global Search**")
        search_term = st.text_input("Search any column...")
        if search_term:
            search_term = search_term.lower()
            filtered = filtered[filtered.apply(lambda row: row.astype(str).str.lower().str.contains(search_term).any(), axis=1)]
            st.success(f"🔎 Found {len(filtered)} matching rows.")
    with col1:
        selected_operator = st.selectbox("Operator", ["All"] + sorted(data["Operator"].dropna().unique().tolist()))
        if selected_operator != "All":
            filtered = filtered[filtered["Operator"] == selected_operator]
    with col2:
        selected_contractor = st.selectbox("Contractor", ["All"] + sorted(data["Contractor"].dropna().unique().tolist()))
        if selected_contractor != "All":
            filtered = filtered[filtered["Contractor"] == selected_contractor]
    with col3:
        selected_shaker = st.selectbox("Shaker", ["All"] + sorted(data["flowline_Shakers"].dropna().unique().tolist()))
        if selected_shaker != "All":
            filtered = filtered[filtered["flowline_Shakers"] == selected_shaker]
    with col4:
        try:
            hole_sizes = sorted(data["Hole_Size"].dropna().unique().tolist())
            selected_hole = st.selectbox("Hole Size", ["All"] + hole_sizes)
            if selected_hole != "All":
                filtered = filtered[filtered["Hole_Size"] == selected_hole]
        except Exception as e:
            st.warning(f"⚠️ Unable to load Hole Size options: {e}")

# Key Metrics
st.markdown("### 📊 Key Metrics")
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Avg Total Dilution", f"{filtered['Total_Dil'].mean():,.2f} BBLs")
with m2:
    st.metric("Avg SCE", f"{filtered['Total_SCE'].mean():,.2f}")
with m3:
    st.metric("Avg DSRE", f"{filtered['DSRE'].mean()*100:.1f}%")

# Tabs
tabs = st.tabs(["Well Overview", "Summary & Charts", "Statistical Insights", "Advanced Analytics", "Derrick Comparison", "Advanced Filters"])

# Well Overview
with tabs[0]:
    st.subheader("📄 Well Overview")
    st.markdown("Analyze well-level performance metrics as grouped column bar charts.")
    selected_metric = st.selectbox("Choose a metric to visualize", ["Total_Dil", "Total_SCE", "DSRE"])

    if "Well_Name" in filtered.columns and selected_metric in filtered.columns:
        metric_data = filtered[["Well_Name", selected_metric]].dropna()
        metric_data = metric_data.groupby("Well_Name")[selected_metric].mean().reset_index()
        metric_data.rename(columns={selected_metric: "Value"}, inplace=True)
        fig = px.bar(metric_data, x="Well_Name", y="Value", title=f"Well Name vs {selected_metric}")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("⚠️ Required columns not found.")

# Summary & Charts
with tabs[1]:
    st.markdown("### 📌 Summary & Charts")
    chart1, chart2 = st.columns(2)
    with chart1:
        st.markdown("#### 📌 Depth vs DOW")
        if all(col in filtered.columns for col in ["Well_Name", "Depth", "DOW"]):
            subset = filtered[["Well_Name", "Depth", "DOW"]].dropna()
            subset["Depth"] = pd.to_numeric(subset["Depth"], errors="coerce")
            subset["DOW"] = pd.to_numeric(subset["DOW"], errors="coerce")
            subset.dropna(inplace=True)
            if not subset.empty:
                fig1 = px.bar(subset, x="Well_Name", y=["Depth", "DOW"], barmode="group",
                              labels={"value": "Barrels", "variable": "Metric"},
                              color_discrete_sequence=px.colors.qualitative.Prism)
                st.plotly_chart(fig1, use_container_width=True)
            else:
                st.warning("⚠️ No data to plot after cleaning.")
        else:
            st.warning("⚠️ Required columns missing.")

    with chart2:
        st.markdown("#### 🌈 Dilution Breakdown")
        y_cols = [col for col in ["Base_Oil", "Water", "Weight_Material", "Chemicals"] if col in filtered.columns]
        if y_cols and "Well_Name" in filtered.columns:
            subset = filtered[["Well_Name"] + y_cols].dropna()
            if not subset.empty:
                fig2 = px.bar(subset, x="Well_Name", y=y_cols, barmode="stack",
                              color_discrete_sequence=px.colors.qualitative.Set2)
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.warning("⚠️ No data to plot after cleaning.")
        else:
            st.warning("⚠️ Required columns missing for dilution chart.")

# Statistical Insights
with tabs[2]:
    st.markdown("### 📊 Statistical Summary & Insights")
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("📈 Mean DSRE", f"{filtered['DSRE'].mean()*100:.2f}%")
    with k2:
        st.metric("🚛 Max Haul Off", f"{filtered['Haul_OFF'].max():,.0f}")
    with k3:
        st.metric("🧪 Avg SCE", f"{filtered['Total_SCE'].mean():,.2f}")
    with k4:
        st.metric("💧 Avg Dilution", f"{filtered['Total_Dil'].mean():,.2f}")

# Advanced Analytics
with tabs[3]:
    st.markdown("### 🔬 Advanced Analytics (to be added)")

# Derrick Comparison
with tabs[4]:
    st.markdown("### 🟩 Derrick vs Non-Derrick (to be added)")

# Advanced Filters
with tabs[5]:
    st.markdown("### ⚙️ Advanced Filters (to be added)")
