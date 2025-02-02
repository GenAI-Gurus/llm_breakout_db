import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime
import config  # Import configuration file

# --- Set page config as the very first Streamlit command ---
st.set_page_config(page_title="Jailbreak Prompt Database", layout="wide")

# --- Google Analytics Integration using tracking ID from config ---
ga_tracking_id = config.GOOGLE_ANALYTICS_TRACKING_ID
# Increase height to force the iframe to render, and wrap in a hidden div.
components.html(
    f"""
    <div style="display:none;">
      <!-- Global site tag (gtag.js) - Google Analytics -->
      <script async src="https://www.googletagmanager.com/gtag/js?id={ga_tracking_id}"></script>
      <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{ dataLayer.push(arguments); }}
        gtag('js', new Date());
        gtag('config', '{ga_tracking_id}');
      </script>
    </div>
    """,
    height=100,
)

st.title("Public Crowd-Sourced Jailbreak Prompt Database")

# --- Function to load data from the public URL (cached) ---
@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_csv(config.CSV_URL)
    return df

# --- Load the CSV data from the public URL ---
df_all = load_data()

# --- Sidebar: Filters, Search, and Sorting Options ---
st.sidebar.header("Filter Options")

llm_options = df_all["LLM"].unique().tolist()
selected_llms = st.sidebar.multiselect("Select LLM(s)", options=llm_options, default=llm_options)

status_options = df_all["Verification Status"].unique().tolist()
selected_status = st.sidebar.multiselect("Select Verification Status", options=status_options, default=status_options)

search_query = st.sidebar.text_input("Search Prompt Text")

sort_by = st.sidebar.selectbox("Sort by", ["Submission Date", "Effectiveness Score", "Reproducibility Score"])

# Apply filters to the DataFrame
df_filtered = df_all[df_all["LLM"].isin(selected_llms)]
df_filtered = df_filtered[df_filtered["Verification Status"].isin(selected_status)]
if search_query:
    df_filtered = df_filtered[df_filtered["Prompt"].str.contains(search_query, case=False, na=False)]

if sort_by == "Submission Date":
    df_filtered["Submission Date"] = pd.to_datetime(df_filtered["Submission Date"], errors="coerce")
    df_filtered = df_filtered.sort_values("Submission Date", ascending=False)
elif sort_by == "Effectiveness Score":
    df_filtered = df_filtered.sort_values("Effectiveness Score", ascending=False)
elif sort_by == "Reproducibility Score":
    df_filtered = df_filtered.sort_values("Reproducibility Score", ascending=False)

# --- Define the tabs (all users are anonymous) ---
tabs = ["Prompt Entries", "Submitters Leaderboard", "Submit New Prompt"]
tab1, tab2, tab3 = st.tabs(tabs)

# --- Tab 1: Display Prompt Entries with dynamic height ---
with tab1:
    st.subheader("Crowd-Sourced Jailbreak Prompt Entries")
    row_count = max(len(df_filtered), 10)  # at least 10 rows
    table_height = row_count * 40         # approx 40 pixels per row
    st.dataframe(df_filtered, height=table_height, use_container_width=True)

# --- Tab 2: Submitters Leaderboard ---
with tab2:
    st.subheader("Top 5 Submitters Leaderboard")
    df_verified = df_all[df_all["Verification Status"] == "Verified"]
    leaderboard = df_verified.groupby("Submitter").agg(
        Verified_Submissions=("ID", "count"),
        Avg_Effectiveness=("Effectiveness Score", "mean"),
        Avg_Reproducibility=("Reproducibility Score", "mean")
    ).reset_index()
    leaderboard["Score"] = (
        leaderboard["Verified_Submissions"] +
        2 * leaderboard["Avg_Effectiveness"] +
        2 * leaderboard["Avg_Reproducibility"]
    )
    leaderboard = leaderboard.sort_values("Score", ascending=False).head(5)
    st.dataframe(leaderboard, use_container_width=True)

# --- Tab 3: Submit New Prompt ---
with tab3:
    st.subheader("Submit a New Jailbreak Prompt")
    st.markdown(f"""
    To submit a new jailbreak prompt, please use our [Google Form]({config.GOOGLE_FORM_URL}).

    Your submission will be recorded in a Google Sheet for later review.
    """)
    st.info("Note: New submissions are stored externally for review, and both the source code and CSV data are public.")
