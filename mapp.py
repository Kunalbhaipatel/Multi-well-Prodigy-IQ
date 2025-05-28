import pandas as pd
import streamlit as st
import plotly.express as px
from st_aggrid import AgGrid

st.set_page_config(page_title="Rig Comparison Dashboard", layout="wide")
st.title("🚀 Rig Comparison Dashboard")

# ---------- CACHED DATA LOADING ----------
@st.cache_data
def load_data():
    df = pd.read_csv("Updated_Merged_Data_with_API_and_Location.csv")
    df["TD_Date"] = pd.to_datetime(df["TD_Date"], errors='coerce')
    if "Efficiency Score" in df.columns and df["Efficiency Score"].isnull().all():
        df.drop(columns=["Efficiency Score"], inplace=True)
    return df

data = load_data()

# ---------- GLOBAL SEARCH & FILTER ----------
with st.container():
    col_search, col1, col2, col3, col4 = st.columns([2.5, 1.2, 1.2, 1.2, 1.2])
    with col_search:
        st.markdown("🔍 **Global Search**")
        search_term = st.text_input("Search any column...")

    with col1:
        selected_operator = st.selectbox("Operator", ["All"] + sorted(data["Operator"].dropna().unique().tolist()))
    with col2:
        temp = data if selected_operator == "All" else data[data["Operator"] == selected_operator]
        selected_contractor = st.selectbox("Contractor", ["All"] + sorted(temp["Contractor"].dropna().unique().tolist()))
    with col3:
        temp = temp if selected_contractor == "All" else temp[temp["Contractor"] == selected_contractor]
        selected_shaker = st.selectbox("Shaker", ["All"] + sorted(temp["flowline_Shakers"].dropna().unique().tolist()))
    with col4:
        temp = temp if selected_shaker == "All" else temp[temp["flowline_Shakers"] == selected_shaker]
        selected_hole = st.selectbox("Hole Size", ["All"] + sorted(temp["Hole_Size"].dropna().unique().tolist()))

filtered = temp if selected_hole == "All" else temp[temp["Hole_Size"] == selected_hole]

# Apply global search
if search_term:
    search_term = search_term.lower()
    filtered = filtered[filtered.apply(lambda row: row.astype(str).str.lower().str.contains(search_term).any(), axis=1)]
    st.success(f"🔎 Found {len(filtered)} matching rows.")

# ---------- METRICS ----------
st.markdown("### 📊 Key Metrics")
m1, m2, m3 = st.columns(3)
with m1: st.metric("Avg Total Dilution", f"{filtered['Total_Dil'].mean():,.2f} BBLs")
with m2: st.metric("Avg SCE", f"{filtered['Total_SCE'].mean():,.2f}")
with m3: st.metric("Avg DSRE", f"{filtered['DSRE'].mean()*100:.1f}%")

# ---------- TABS ----------
tabs = st.tabs(["Well Overview", "Summary & Charts", "Statistical Insights", "Advanced Analytics", "Derrick Comparison", "Advanced Filters"])

with tabs[0]:
    st.subheader("📄 Well Overview")
    metric = st.selectbox("Choose metric", ["Total_Dil", "Total_SCE", "DSRE"])
    grouped = filtered.groupby("Well_Name")[metric].mean().reset_index()
    fig = px.bar(grouped, x="Well_Name", y=metric, title=f"{metric} by Well")
    st.plotly_chart(fig, use_container_width=True)

with tabs[1]:
    st.subheader("📊 Summary & Charts")
    subset = filtered.dropna(subset=["Well_Name"])
    fig1 = px.bar(subset, x="Well_Name", y=["Depth", "DOW"], barmode='group')
    fig2 = px.bar(subset, x="Well_Name", y=["Base_Oil", "Water", "Weight_Material", "Chemicals"], barmode="stack")
    st.plotly_chart(fig1, use_container_width=True)
    st.plotly_chart(fig2, use_container_width=True)

with tabs[2]:
    st.subheader("📈 Statistical Insights")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Max Depth", f"{filtered['Depth'].max():,.0f}")
    with c2: st.metric("Avg LGS%", f"{filtered['Average_LGS%'].mean():.2f}")
    with c3: st.metric("Dilution Ratio", f"{filtered['Dilution_Ratio'].mean():.2f}")
    with c4: st.metric("Discard Ratio", f"{filtered['Discard Ratio'].mean():.2f}")

with tabs[3]:
    st.subheader("📉 Advanced Analytics")
    if "ROP" in filtered.columns and "Temp" in filtered.columns:
        fig3 = px.scatter(filtered, x="ROP", y="Temp", color="Well_Name")
        st.plotly_chart(fig3, use_container_width=True)

    if "Base_Oil" in filtered.columns and "Water" in filtered.columns:
        fig4 = px.scatter(filtered, x="Base_Oil", y="Water", size="Total_Dil", color="Well_Name")
        st.plotly_chart(fig4, use_container_width=True)

    try:
        corr_cols = ["DSRE", "Total_SCE", "Total_Dil", "Discard Ratio", "Dilution_Ratio", "ROP", "AMW", "Haul_OFF"]
        fig_corr = px.imshow(filtered[corr_cols].dropna().corr(), text_auto=True)
        st.plotly_chart(fig_corr, use_container_width=True)
    except:
        st.warning("Heatmap unavailable due to missing data.")

with tabs[4]:
    st.subheader("📊 Derrick vs Non-Derrick")
    if "flowline_Shakers" in filtered.columns:
        filtered["Shaker_Type"] = filtered["flowline_Shakers"].apply(lambda x: "Derrick" if "derrick" in str(x).lower() else "Non-Derrick")
        derrick = filtered[filtered["Shaker_Type"] == "Derrick"]
        non_derrick = filtered[filtered["Shaker_Type"] == "Non-Derrick"]
        metric_cols = ["DSRE", "Total_Dil", "Total_SCE"]
        derrick_avg = derrick[metric_cols].mean().reset_index(name="Derrick")
        non_derrick_avg = non_derrick[metric_cols].mean().reset_index(name="Non-Derrick")
        comparison = pd.merge(derrick_avg, non_derrick_avg, on="index").rename(columns={"index": "Metric"})
        melted = comparison.melt(id_vars="Metric", var_name="Shaker", value_name="Value")
        fig5 = px.bar(melted, x="Metric", y="Value", color="Shaker", barmode="group")
        st.plotly_chart(fig5, use_container_width=True)

with tabs[5]:
    st.subheader("⚙️ Advanced Filters")
    colA, colB = st.columns(2)
    with colA:
        if "AMW" in filtered.columns:
            amw_min, amw_max = filtered["AMW"].min(), filtered["AMW"].max()
            amw_range = st.slider("AMW", amw_min, amw_max, (amw_min, amw_max))
            filtered = filtered[(filtered["AMW"] >= amw_range[0]) & (filtered["AMW"] <= amw_range[1])]
    with colB:
        if "TD_Date" in filtered.columns:
            filtered["TD_Year"] = filtered["TD_Date"].dt.year
            filtered["TD_Month"] = filtered["TD_Date"].dt.strftime('%B')
            year_sel = st.selectbox("TD Year", ["All"] + sorted(filtered["TD_Year"].dropna().unique().astype(int).tolist()))
            month_sel = st.selectbox("TD Month", ["All"] + list(filtered["TD_Month"].dropna().unique()))
            if year_sel != "All":
                filtered = filtered[filtered["TD_Year"] == int(year_sel)]
            if month_sel != "All":
                filtered = filtered[filtered["TD_Month"] == month_sel]

    st.markdown("### 🧾 Final Filtered Table")
    AgGrid(filtered, height=300, fit_columns_on_grid_load=True)
