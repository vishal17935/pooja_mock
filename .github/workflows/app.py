import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import time

# ===============================
# CONFIG
# ===============================
SHEET_URL = "https://docs.google.com/spreadsheets/d/1msc3DBtNx-xx04CdoG7-dCNkz4wA2sxwKBGsaJHTaI4/export?format=csv&gid=1459153692"
POSITIVE_MARK = 1
NEGATIVE_MARK = 0.25

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(layout="wide")
st.title("Performance Dashboard")

# ===============================
# TOP CONTROLS
# ===============================
col1, col2 = st.columns([1, 4])

with col1:
    if st.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()

with col2:
    auto_refresh = st.checkbox("Auto Refresh (every 5 min)")

if auto_refresh:
    time.sleep(300)
    st.rerun()

# ===============================
# DATA LOADING
# ===============================
@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv(SHEET_URL, header=[0, 1])

    df.columns = [
        "test_number" if c[0].strip().lower() == "date"
        else f"{c[0].strip().lower()}_{c[1].strip().lower()}"
        for c in df.columns
    ]

    df = df.apply(pd.to_numeric)

    subjects = sorted({
        col.split("_")[0]
        for col in df.columns if "_" in col
    } - {"test", "total"})

    return df, subjects


# ===============================
# CALCULATIONS
# ===============================
def compute_metrics(df, subjects):

    for s in subjects:
        df[f"{s}_total"] = df[f"{s}_attempted"] + df[f"{s}_unattempt"]
        df[f"{s}_correct"] = df[f"{s}_attempted"] - df[f"{s}_wrong"]

        df[f"{s}_accuracy"] = df[f"{s}_correct"] / df[f"{s}_attempted"].replace(0, 1)
        df[f"{s}_attempt_ratio"] = df[f"{s}_attempted"] / df[f"{s}_total"].replace(0, 1)

        net = df[f"{s}_correct"] * POSITIVE_MARK - df[f"{s}_wrong"] * NEGATIVE_MARK
        df[f"{s}_net_score"] = net
        df[f"{s}_normalized_score"] = net / df[f"{s}_total"].replace(0, 1)

    df["total_attempted"] = df[[f"{s}_attempted" for s in subjects]].sum(axis=1)
    df["total_unattempt"] = df[[f"{s}_unattempt" for s in subjects]].sum(axis=1)
    df["total_wrong"] = df[[f"{s}_wrong" for s in subjects]].sum(axis=1)

    df["total_correct"] = df["total_attempted"] - df["total_wrong"]
    df["total_questions"] = df["total_attempted"] + df["total_unattempt"]

    df["overall_accuracy"] = df["total_correct"] / df["total_attempted"].replace(0, 1)
    df["overall_attempt_ratio"] = df["total_attempted"] / df["total_questions"].replace(0, 1)

    overall_net = df["total_correct"] * POSITIVE_MARK - df["total_wrong"] * NEGATIVE_MARK
    df["overall_net_score"] = overall_net
    df["overall_normalized_score"] = overall_net / df["total_questions"].replace(0, 1)

    return df


# ===============================
# DASHBOARD
# ===============================
def create_dashboard(df, subjects):

    fig = plt.figure(figsize=(18, 9))
    gs = gridspec.GridSpec(2, 3, height_ratios=[1, 1.2], hspace=0.4, wspace=0.3)

    metrics = [
        ("accuracy", "Accuracy", "Accuracy"),
        ("attempt_ratio", "Attempt Ratio", "Ratio"),
        ("normalized_score", "Normalized Score", "Score / Q"),
    ]

    for i, (key, title, ylabel) in enumerate(metrics):
        ax = fig.add_subplot(gs[0, i])
        for s in subjects:
            ax.plot(df["test_number"], df[f"{s}_{key}"], marker='o', label=s)
        ax.plot(df["test_number"], df[f"overall_{key}"], linewidth=3, label="overall")
        ax.set(title=title, xlabel="Test", ylabel=ylabel)
        ax.grid()
        ax.legend()

    latest = df.iloc[-1]

    for i, s in enumerate(subjects):
        ax = fig.add_subplot(gs[1, i])
        ax.pie(
            [latest[f"{s}_correct"], latest[f"{s}_wrong"], latest[f"{s}_unattempt"]],
            labels=["Correct", "Wrong", "Unattempted"],
            autopct="%1.1f%%",
            radius=1.25
        )
        ax.set_title(f"{s.capitalize()} (Latest)")

    return fig


# ===============================
# RUN APP
# ===============================
df, subjects = load_data()
df = compute_metrics(df, subjects)

st.caption(f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

fig = create_dashboard(df, subjects)
st.pyplot(fig, use_container_width=True)
