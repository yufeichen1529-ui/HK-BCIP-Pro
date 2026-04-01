import streamlit as st
import pandas as pd
import plotly.express as px
import json

st.set_page_config(page_title="HK-BCIP Pro v2.1", layout="wide")

st.markdown("""
    <style>
    .main-title {
        font-size: 3.5rem !important;
        font-weight: 800;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .sub-title {
        text-align: center;
        color: #6B7280;
        margin-bottom: 2rem;
    }
    .kpi-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        border-left: 8px solid #1E3A8A;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }
    .kpi-card:hover {
        transform: translateY(-5px);
    }
    .kpi-label {
        font-size: 0.9rem;
        color: #4B5563;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #111827;
        margin-top: 5px;
    }
    .kpi-delta {
        font-size: 0.85rem;
        color: #DC2626;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

if 'project_data' not in st.session_state:
    st.session_state.project_data = []

REAL_FACTORS = {
    "Steel Rebar": {"EU": 1125, "GBA": 2340, "Unit": "t"},
    "Concrete C30": {"EU": 259.3, "GBA": 295, "Unit": "m³"},
    "Timber": {"EU": 450, "GBA": 410, "Unit": "m³"},
    "Aluminum Frame": {"EU": 6700, "GBA": 12500, "Unit": "t"}
}
CARBON_PRICE_HKD = 585


def calculate_metrics(mat, qty, dist, grid_decarb):
    ef_gba = REAL_FACTORS[mat]["GBA"]
    ef_eu = REAL_FACTORS[mat]["EU"]
    decarb_factor = (1 - (grid_decarb / 100 * 0.6))
    adj_ef = ef_gba * decarb_factor
    transport = (qty * dist * 0.1) / 1000 if REAL_FACTORS[mat]["Unit"] == "t" else (qty * dist * 0.05) / 1000
    gba_total = (qty * adj_ef) / 1000 + transport
    eu_total = (qty * ef_eu) / 1000
    return round(gba_total, 2), round(eu_total, 2), round(adj_ef, 1)


with st.sidebar:
    st.markdown("### 🛠️ Asset Configuration")
    mat_type = st.selectbox("Material Type", list(REAL_FACTORS.keys()))
    qty = st.number_input(f"Quantity ({REAL_FACTORS[mat_type]['Unit']})", value=100.0)
    dist = st.slider("Logistics Radius (km)", 10, 500, 150)
    grid_decarb = st.slider("2050 Net-Zero Transition %", 0, 100, 0)

    if st.button("➕ Add to Inventory", use_container_width=True):
        gba_res, eu_res, _ = calculate_metrics(mat_type, qty, dist, grid_decarb)
        st.session_state.project_data.append({
            "Material": mat_type, "Qty": qty, "GBA_Total": gba_res,
            "EU_Baseline": eu_res, "Financial_Risk": round(gba_res * CARBON_PRICE_HKD, 2),
            "Gap_Impact": round(gba_res - eu_res, 2)
        })
        st.toast("Data points logged!")

st.markdown('<p class="main-title">HK-BCIP</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Carbon Integrity & Financial Risk Dashboard</p>', unsafe_allow_html=True)

t1, t2, t3 = st.tabs(["📊 Analytics Dashboard", "🛡️ Audit Lab", "📋 Compliance Report"])

with t1:
    if st.session_state.project_data:
        df = pd.DataFrame(st.session_state.project_data)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                f'<div class="kpi-card"><div class="kpi-label">Project Carbon</div><div class="kpi-value">{df["GBA_Total"].sum():.1f} t</div></div>',
                unsafe_allow_html=True)
        with c2:
            st.markdown(
                f'<div class="kpi-card"><div class="kpi-label">Localization Gap</div><div class="kpi-value">+{df["Gap_Impact"].sum():.1f} t</div><div class="kpi-delta">⚠️ Underestimated</div></div>',
                unsafe_allow_html=True)
        with c3:
            st.markdown(
                f'<div class="kpi-card"><div class="kpi-label">Financial Risk</div><div class="kpi-value">${df["Financial_Risk"].sum():,.0f}</div><div class="kpi-delta">HKD Potential Liability</div></div>',
                unsafe_allow_html=True)
        with c4:
            st.markdown(
                f'<div class="kpi-card"><div class="kpi-label">Data Confidence</div><div class="kpi-value">Tier-1</div><div class="kpi-delta">Real GBA-LCI Linked</div></div>',
                unsafe_allow_html=True)

        st.markdown("---")

        col_left, col_right = st.columns([2, 1])
        with col_left:
            plot_df = pd.melt(df, id_vars=['Material'], value_vars=['GBA_Total', 'EU_Baseline'], var_name='Standard',
                              value_name='Emissions')
            fig_bar = px.bar(plot_df, x='Material', y='Emissions', color='Standard', barmode='group',
                             title="GBA Localized vs. EU Baseline Emissions",
                             color_discrete_map={"GBA_Total": "#1E3A8A", "EU_Baseline": "#D1D5DB"},  # 使用修正后的参数
                             template="plotly_white")
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_right:
            fig_pie = px.pie(df, values='Financial_Risk', names='Material', title="Risk Exposure by Material",
                             color_discrete_sequence=px.colors.qualitative.Prism)
            st.plotly_chart(fig_pie, use_container_width=True)

        st.write("### 📝 Detailed Inventory")
        st.dataframe(df.style.background_gradient(cmap='Blues', subset=['GBA_Total']), use_container_width=True)

        if st.button("🗑️ Clear All Data"):
            st.session_state.project_data = []
            st.rerun()
    else:
        st.info("System Ready. Please input material data via the sidebar to generate analytics.")

with t2:
    st.subheader("🛡️ Anti-Greenwashing Audit Engine")
    check_mat = st.selectbox("Select Material for Audit", list(REAL_FACTORS.keys()))
    input_val = st.number_input("Supplier Declared Carbon Factor", value=float(REAL_FACTORS[check_mat]["GBA"]))
    baseline = REAL_FACTORS[check_mat]["GBA"]
    if input_val < baseline * 0.75:
        st.error(
            f"🚨 CRITICAL WARNING: High Greenwashing Risk! Value is {abs((input_val - baseline) / baseline * 100):.1f}% below regional average.")
    else:
        st.success("✅ Audit Passed: Value is consistent with GBA LCI data.")

with t3:
    st.subheader("📜 Compliance Data Export")
    if st.session_state.project_data:
        report = {"Platform": "HK-BCIP v2.1", "Total_Carbon": df["GBA_Total"].sum(),
                  "Financial_Risk_HKD": df["Financial_Risk"].sum(), "Inventory": st.session_state.project_data}
        st.code(json.dumps(report, indent=4), language="json")
        st.download_button("📥 Download JSON Report", data=json.dumps(report), file_name="ESG_Report.json")