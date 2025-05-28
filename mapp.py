
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Rig Comparison Dashboard", layout="wide")
st.title("🚀 Rig Comparison Dashboard")

# ---------- LOAD DATA ----------
default_path = "Updated_Merged_Data_with_API_and_Location.csv"
data = pd.read_csv(default_path)

if "Efficiency Score" in data.columns and data["Efficiency Score"].isnull().all():
    data.drop(columns=["Efficiency Score"], inplace=True)

# ---------- GLOBAL SEARCH & FILTER BAR ----------
with st.container():
    col_search, col1, col2, col3, col4 = st.columns([2.5, 1.2, 1.2, 1.2, 1.2])
    with col_search:
        st.markdown("🔍 **Global Search**")
        search_term = st.text_input("Search any column...")
        reset_filters = st.button("🔄 Reset All Filters", key="master_reset_button")
        if reset_filters:
            st.experimental_rerun()
        if search_term:
            search_term = search_term.lower()
            data = data[data.apply(lambda row: row.astype(str).str.lower().str.contains(search_term).any(), axis=1)]
            st.success(f"🔎 Found {len(data)} matching rows.")
    with col1:
        selected_operator = st.selectbox("Operator", ["All"] + sorted(data["Operator"].dropna().unique().tolist()))
    with col2:
        filtered_by_op = data if selected_operator == "All" else data[data["Operator"] == selected_operator]
        selected_contractor = st.selectbox("Contractor", ["All"] + sorted(filtered_by_op["Contractor"].dropna().unique().tolist()))
    with col3:
        filtered_by_contractor = filtered_by_op if selected_contractor == "All" else filtered_by_op[filtered_by_op["Contractor"] == selected_contractor]
        selected_shaker = st.selectbox("Shaker", ["All"] + sorted(filtered_by_contractor["flowline_Shakers"].dropna().unique().tolist()))
    with col4:
        filtered_by_shaker = filtered_by_contractor if selected_shaker == "All" else filtered_by_contractor[filtered_by_contractor["flowline_Shakers"] == selected_shaker]
        selected_hole = st.selectbox("Hole Size", ["All"] + sorted(filtered_by_shaker["Hole_Size"].dropna().unique().tolist()))

    filtered = filtered_by_shaker if selected_hole == "All" else filtered_by_shaker[filtered_by_shaker["Hole_Size"] == selected_hole]

# ---------- METRICS ----------
st.markdown("### 📊 Key Metrics")
m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Avg Total Dilution", f"{filtered['Total_Dil'].mean():,.2f} BBLs")
with m2:
    st.metric("Avg SCE", f"{filtered['Total_SCE'].mean():,.2f}")
with m3:
    st.metric("Avg DSRE", f"{filtered['DSRE'].mean()*100:.1f}%")

# ---------- MAIN TABS ----------
tabs = st.tabs([
    "🧾 Well Overview", 
    "📋 Summary & Charts", 
    "📊 Statistical Insights", 
    "📈 Advanced Analytics", 
    "🧮 Multi-Well Comparison", 
    "⚙️ Advanced Tab"
])

# ---------- TAB 1 ----------
with tabs[0]:
    st.subheader("📄 Well Overview")
    selected_metric = st.selectbox("Choose metric to visualize", ["Total_Dil", "Total_SCE", "DSRE"])
    metric_data = filtered[["Well_Name", selected_metric]].dropna()
    metric_data = metric_data.groupby("Well_Name")[selected_metric].mean().reset_index()
    metric_data.rename(columns={selected_metric: "Value"}, inplace=True)
    fig = px.bar(metric_data, x="Well_Name", y="Value", title=f"Well Name vs {selected_metric}")
    st.plotly_chart(fig, use_container_width=True)

# ---------- TAB 2 ----------
with tabs[1]:
    st.markdown("### 📌 Summary & Charts")
    subset = filtered.dropna(subset=["Well_Name"])
    chart1, chart2 = st.columns(2)
    with chart1:
        if all(col in subset.columns for col in ["Depth", "DOW"]):
            fig1 = px.bar(subset, x="Well_Name", y=["Depth", "DOW"], barmode='group', height=400)
            st.plotly_chart(fig1, use_container_width=True)
    with chart2:
        y_cols = [col for col in ["Base_Oil", "Water", "Weight_Material", "Chemicals"] if col in subset.columns]
        if y_cols:
            fig2 = px.bar(subset, x="Well_Name", y=y_cols, barmode="stack", height=400)
            st.plotly_chart(fig2, use_container_width=True)

# ---------- TAB 3 ----------
with tabs[2]:
    st.markdown("### 📊 Statistical Insights")
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("📈 Mean DSRE", f"{filtered['DSRE'].mean()*100:.2f}%")
    with k2: st.metric("🚛 Max Haul Off", f"{filtered['Haul_OFF'].max():,.0f}")
    with k3: st.metric("🧪 Avg SCE", f"{filtered['Total_SCE'].mean():,.2f}")
    with k4: st.metric("💧 Avg Dilution", f"{filtered['Total_Dil'].mean():,.2f}")

# ---------- TAB 4 ----------
with tabs[3]:
    st.markdown("### 🤖 Advanced Analytics")
    if "ROP" in filtered.columns and "Temp" in filtered.columns:
        fig_rt = px.scatter(filtered, x="ROP", y="Temp", color="Well_Name", title="ROP vs Temp")
        st.plotly_chart(fig_rt, use_container_width=True)
    if "Base_Oil" in filtered.columns and "Water" in filtered.columns:
        fig_bw = px.scatter(filtered, x="Base_Oil", y="Water", size="Total_Dil", color="Well_Name", title="Base Oil vs Water")
        st.plotly_chart(fig_bw, use_container_width=True)
    try:
        corr_cols = ["DSRE", "Total_SCE", "Total_Dil", "Discard Ratio", "Dilution_Ratio", "ROP", "AMW", "Haul_OFF"]
        fig_corr = px.imshow(filtered[corr_cols].dropna().corr(), text_auto=True, aspect="auto")
        st.plotly_chart(fig_corr, use_container_width=True)
    except Exception as e:
        st.warning("⚠️ Correlation heatmap could not be generated.")

# ---------- TAB 5 ----------
with tabs[4]:
    st.markdown("### 🧮 Derrick vs Non-Derrick")
    if "flowline_Shakers" in filtered.columns:
        filtered["Shaker_Type"] = filtered["flowline_Shakers"].apply(lambda x: "Derrick" if isinstance(x, str) and "derrick" in x.lower() else "Non-Derrick")
        cols = ["DSRE", "Total_Dil", "Dilution_Ratio"]
        derrick_avg = filtered[filtered["Shaker_Type"] == "Derrick"][cols].mean().reset_index()
        non_derrick_avg = filtered[filtered["Shaker_Type"] == "Non-Derrick"][cols].mean().reset_index()
        derrick_avg.columns = ["Metric", "Derrick"]
        non_derrick_avg.columns = ["Metric", "Non-Derrick"]
        merged = pd.merge(derrick_avg, non_derrick_avg, on="Metric")
        melted = pd.melt(merged, id_vars="Metric", value_vars=["Derrick", "Non-Derrick"], var_name="Shaker_Type", value_name="Average")
        fig = px.bar(melted, x="Metric", y="Average", color="Shaker_Type", barmode="group")
        st.plotly_chart(fig, use_container_width=True)

# ---------- TAB 6 ----------
with tabs[5]:
    st.markdown("### ⚙️ Advanced Filters")
    col1, col2 = st.columns(2)
    with col1:
        if "IntLength" in data.columns:
            min_val, max_val = int(data["IntLength"].min()), int(data["IntLength"].max())
            int_range = st.slider("Interval Length", min_val, max_val, (min_val, max_val))
            filtered = filtered[(filtered["IntLength"] >= int_range[0]) & (filtered["IntLength"] <= int_range[1])]
        if "AMW" in data.columns:
            min_amw, max_amw = float(data["AMW"].min()), float(data["AMW"].max())
            amw_range = st.slider("AMW", min_amw, max_amw, (min_amw, max_amw))
            filtered = filtered[(filtered["AMW"] >= amw_range[0]) & (filtered["AMW"] <= amw_range[1])]
    with col2:
        if "Average_LGS%" in data.columns:
            lgs_min, lgs_max = float(data["Average_LGS%"].min()), float(data["Average_LGS%"].max())
            lgs_range = st.slider("Average LGS%", lgs_min, lgs_max, (lgs_min, lgs_max))
            filtered = filtered[(filtered["Average_LGS%"] >= lgs_range[0]) & (filtered["Average_LGS%"] <= lgs_range[1])]
        if "TD_Date" in data.columns and not data["TD_Date"].isnull().all():
            try:
                data["TD_Date"] = pd.to_datetime(data["TD_Date"], errors='coerce')
                data["TD_Year"] = data["TD_Date"].dt.year
                data["TD_Month"] = data["TD_Date"].dt.strftime('%B')
                year_opts = sorted(data["TD_Year"].dropna().unique())
                selected_year = st.selectbox("TD Year", ["All"] + [int(y) for y in year_opts])
                selected_month = st.selectbox("TD Month", ["All"] + list(pd.date_range("2024-01-01", "2024-12-31", freq="MS").strftime("%B").unique()))
                if selected_year != "All":
                    filtered = filtered[filtered["TD_Year"] == selected_year]
                if selected_month != "All":
                    filtered = filtered[filtered["TD_Month"] == selected_month]
            except Exception as e:
                st.warning(f"⚠️ TD date error: {e}")
    st.markdown("### 🔍 Filtered Result Preview")
    st.dataframe(filtered)

# ---------- FOOTER ----------
st.markdown("""
<div style='position: fixed; left: 0; bottom: 0; width: 100%; background-color: #1c1c1c; color: white; text-align: center; padding: 8px 0; font-size: 0.9rem; z-index: 999;'>
    &copy; 2025 Derrick Corp | Designed for drilling performance insights
</div>
""", unsafe_allow_html=True)
