
import os
import time
from datetime import datetime, timedelta

import pandas as pd
import psutil
import plotly.express as px
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# ---------------- CONFIGURATION ----------------
CPU_THRESHOLD = 80
RAM_THRESHOLD = 80
DISK_THRESHOLD = 90
REFRESH_SECONDS = 5
LOG_FILE = "resource_log.csv"

st.set_page_config(
    page_title="System Resource Monitor",
    page_icon="🖥️",
    layout="wide"
)

# ---------------- CUSTOM DESIGN ----------------
st.markdown("""
<style>
.stApp {
    background-color: #05090c;
    color: #e6edf3;
}
h1, h2, h3 {
    color: #25d9f2 !important;
}
[data-testid="stMetric"] {
    background: #080e13;
    border: 1px solid #263744;
    border-radius: 8px;
    padding: 18px;
}
[data-testid="stMetricLabel"] {
    color: #9fb4c4;
}
[data-testid="stMetricValue"] {
    color: #31e875;
}
div[data-testid="stDataFrame"] {
    border: 1px solid #263744;
}
.block-container {
    padding-top: 1.5rem;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HELPER FUNCTIONS ----------------
def get_uptime():
    seconds = int(time.time() - psutil.boot_time())
    return str(timedelta(seconds=seconds))


def initialize_log():
    if not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0:
        pd.DataFrame(columns=[
            "Timestamp",
            "CPU Usage (%)",
            "RAM Usage (%)",
            "Disk Usage (%)",
            "Uptime"
        ]).to_csv(LOG_FILE, index=False)


def collect_metrics():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cpu = psutil.cpu_percent(interval=0.3)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(os.path.abspath(os.sep))
    uptime = get_uptime()

    record = {
        "Timestamp": timestamp,
        "CPU Usage (%)": cpu,
        "RAM Usage (%)": memory.percent,
        "Disk Usage (%)": disk.percent,
        "Uptime": uptime
    }

    pd.DataFrame([record]).to_csv(
        LOG_FILE,
        mode="a",
        header=False,
        index=False
    )

    return record, memory, disk


def make_chart(data, column, title, color):
    chart_data = data.tail(30).copy()

    fig = px.line(
        chart_data,
        x="Timestamp",
        y=column,
        title=title,
        markers=True
    )

    fig.update_traces(
        line=dict(color=color, width=2),
        marker=dict(size=5)
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#05090c",
        plot_bgcolor="#05090c",
        font=dict(color="#dbe7ef"),
        title_font=dict(color=color, size=16),
        margin=dict(l=15, r=15, t=45, b=15),
        height=280,
        yaxis=dict(
            range=[0, 100],
            title="Usage (%)",
            gridcolor="#18252e"
        ),
        xaxis=dict(
            title="Time",
            gridcolor="#18252e"
        ),
        showlegend=False
    )

    return fig


# ---------------- LIVE DASHBOARD ----------------
initialize_log()

st_autorefresh(
    interval=REFRESH_SECONDS * 1000,
    key="dashboard_refresh"
)

st.title("🖥️ System Resource Monitor")
st.caption("LIVE DASHBOARD  •  Windows System Performance")

record, memory, disk = collect_metrics()

# Read saved history
data = pd.read_csv(LOG_FILE)
data["Timestamp"] = pd.to_datetime(data["Timestamp"], errors="coerce")
data = data.dropna(subset=["Timestamp"])

# ---------------- TOP METRICS ----------------
cpu_col, ram_col, disk_col, uptime_col = st.columns(4)

with cpu_col:
    st.metric("🟢 CPU Usage", f"{record['CPU Usage (%)']:.1f}%")
    st.progress(min(record["CPU Usage (%)"] / 100, 1.0))
    st.caption(f"{psutil.cpu_count(logical=True)} logical CPU cores")

with ram_col:
    st.metric("🔵 RAM Usage", f"{memory.percent:.1f}%")
    st.progress(min(memory.percent / 100, 1.0))
    st.caption(
        f"{memory.used / (1024**3):.2f} GB used / "
        f"{memory.total / (1024**3):.2f} GB total"
    )

with disk_col:
    st.metric("🔴 Disk Usage", f"{disk.percent:.1f}%")
    st.progress(min(disk.percent / 100, 1.0))
    st.caption(
        f"{disk.used / (1024**3):.1f} GB used / "
        f"{disk.total / (1024**3):.1f} GB total"
    )

with uptime_col:
    st.metric("🟡 System Uptime", get_uptime())
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    st.caption(f"Boot time: {boot_time:%Y-%m-%d %H:%M:%S}")

# ---------------- THRESHOLD ALERTS ----------------
alerts = []

if record["CPU Usage (%)"] >= CPU_THRESHOLD:
    alerts.append("CPU usage has exceeded its configured threshold.")

if memory.percent >= RAM_THRESHOLD:
    alerts.append("RAM usage has exceeded its configured threshold.")

if disk.percent >= DISK_THRESHOLD:
    alerts.append("Disk usage has exceeded its configured threshold.")

for alert in alerts:
    st.warning(alert)

# ---------------- LIVE CHARTS ----------------
st.subheader("📊 Resource Usage — Recent Readings")

chart1, chart2, chart3 = st.columns(3)

with chart1:
    st.plotly_chart(
        make_chart(data, "CPU Usage (%)", "CPU Usage", "#20e875"),
        use_container_width=True
    )

with chart2:
    st.plotly_chart(
        make_chart(data, "RAM Usage (%)", "RAM Usage", "#24b9ff"),
        use_container_width=True
    )

with chart3:
    st.plotly_chart(
        make_chart(data, "Disk Usage (%)", "Disk Usage", "#ff525c"),
        use_container_width=True
    )

# ---------------- RECENT HISTORY ----------------
st.subheader("📋 Recent Resource Usage")

recent = data.tail(10).sort_values(
    "Timestamp", ascending=False
).copy()

recent["Timestamp"] = recent["Timestamp"].dt.strftime(
    "%Y-%m-%d %H:%M:%S"
)

st.dataframe(
    recent,
    use_container_width=True,
    hide_index=True
)

st.caption(
    f"Logging to {LOG_FILE} • "
    f"Refreshes every {REFRESH_SECONDS} seconds"
)

st.download_button(
    "Download Resource History (CSV)",
    data=open(LOG_FILE, "rb").read(),
    file_name="resource_log.csv",
    mime="text/csv"
)
