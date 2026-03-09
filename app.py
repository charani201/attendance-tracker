import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import streamlit.components.v1 as components
from email_alert import send_email

st.set_page_config(layout="wide")

st.title("📊 Student Attendance Anomaly Monitoring System")

# ---------- SESSION STATE INITIALIZATION ----------

if "running" not in st.session_state:
    st.session_state.running = False

if "index" not in st.session_state:
    st.session_state.index = 0

if "x" not in st.session_state:
    st.session_state.x = []

if "y" not in st.session_state:
    st.session_state.y = []

if "anomaly_x" not in st.session_state:
    st.session_state.anomaly_x = []

if "anomaly_y" not in st.session_state:
    st.session_state.anomaly_y = []

if "anomaly_students" not in st.session_state:
    st.session_state.anomaly_students = []

# ---------- CSV UPLOAD ----------

uploaded_file = st.file_uploader("📂 Upload Section CSV", type=["csv"])

if uploaded_file is None:
    st.info("Please upload a CSV file to begin.")
    st.stop()

# Reset simulation and clear old data when a new file is uploaded
if "last_uploaded" not in st.session_state:
    st.session_state.last_uploaded = None

if st.session_state.last_uploaded != uploaded_file.name:
    st.session_state.last_uploaded = uploaded_file.name
    st.session_state.running = False
    st.session_state.index = 0
    st.session_state.x = []
    st.session_state.y = []
    st.session_state.anomaly_x = []
    st.session_state.anomaly_y = []
    st.session_state.anomaly_students = []

data = pd.read_csv(uploaded_file)

# ---------- CONTROL BUTTONS ----------

col1, col2, col3 = st.columns(3)

if col1.button("▶ Start"):
    st.session_state.running = True

if col2.button("⏸ Pause"):
    st.session_state.running = False

if col3.button("🔄 Reset"):
    st.session_state.running = False
    st.session_state.index = 0
    st.session_state.x = []
    st.session_state.y = []
    st.session_state.anomaly_x = []
    st.session_state.anomaly_y = []
    st.session_state.anomaly_students = []

# ---------- PLACEHOLDERS ----------

alert_box = st.empty()
chart_placeholder = st.empty()
table_placeholder = st.empty()

# ---------- BUILD PLOTLY FIGURE ----------

def build_figure():
    fig = go.Figure()

    # Attendance line
    fig.add_trace(go.Scatter(
        x=st.session_state.x,
        y=st.session_state.y,
        mode="lines",
        name="Attendance %",
        line=dict(color="#1f77b4", width=2)
    ))

    # Anomaly markers
    if st.session_state.anomaly_x:
        fig.add_trace(go.Scatter(
            x=st.session_state.anomaly_x,
            y=st.session_state.anomaly_y,
            mode="markers",
            name="Anomaly",
            marker=dict(color="red", size=10, symbol="circle")
        ))

    # Threshold line
    fig.add_hline(
        y=40,
        line_dash="dash",
        line_color="red",
        annotation_text="Threshold (40%)",
        annotation_position="top left"
    )

    fig.update_layout(
        xaxis_title="Student Index",
        yaxis_title="Attendance %",
        yaxis=dict(range=[0, 100]),
        height=400,
        margin=dict(l=40, r=40, t=30, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        # uirevision keeps zoom/pan state stable across reruns — critical for smooth UX
        uirevision="attendance_chart"
    )

    return fig

# ---------- SIMULATION STEP ----------

if st.session_state.running and st.session_state.index < len(data):

    row = data.iloc[st.session_state.index]
    attendance = row["Attendance_Percentage"]

    st.session_state.x.append(st.session_state.index)
    st.session_state.y.append(attendance)

    if attendance < 40:
        st.session_state.anomaly_x.append(st.session_state.index)
        st.session_state.anomaly_y.append(attendance)

        st.session_state.anomaly_students.append({
            "Student Name": row["Student_Name"],
            "Parent Email": row["Parent_Email"],
            "Attendance %": attendance
        })

        alert_box.warning(
            f"🚨 ALERT: {row['Student_Name']} attendance = {attendance}%"
        )

        components.html(
            f"""
            <script>
                /* unique token forces Streamlit to re-render: {time.time()} */
                var ctx = new (window.AudioContext || window.webkitAudioContext)();
                var oscillator = ctx.createOscillator();
                var gainNode = ctx.createGain();
                oscillator.connect(gainNode);
                gainNode.connect(ctx.destination);
                oscillator.type = 'sine';
                oscillator.frequency.setValueAtTime(880, ctx.currentTime);
                gainNode.gain.setValueAtTime(1, ctx.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
                oscillator.start(ctx.currentTime);
                oscillator.stop(ctx.currentTime + 0.5);
            </script>
            """,
            height=0
        )

        send_email(row["Parent_Email"], row["Student_Name"], attendance)

    st.session_state.index += 1

    # Render chart before rerun — stable key prevents widget remount/flicker
    chart_placeholder.plotly_chart(
        build_figure(),
        use_container_width=True,
        key="live_chart"
    )

    if st.session_state.anomaly_students:
        table_placeholder.subheader("🚨 Students With Low Attendance")
        table_placeholder.dataframe(
            pd.DataFrame(st.session_state.anomaly_students),
            use_container_width=True
        )

    time.sleep(0.4)
    st.rerun()

# ---------- PAUSED / STOPPED STATE ----------

else:
    chart_placeholder.plotly_chart(
        build_figure(),
        use_container_width=True,
        key="live_chart"
    )

    if st.session_state.anomaly_students:
        table_placeholder.subheader("🚨 Students With Low Attendance")
        table_placeholder.dataframe(
            pd.DataFrame(st.session_state.anomaly_students),
            use_container_width=True
        )