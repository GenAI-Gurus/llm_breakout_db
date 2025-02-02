import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="LLM Breakout DB", layout="wide")
st.title("LLM Breakout DB: Public Crowd-Sourced Jailbreak Prompt Database")

# --- Function to load data from public URL (cached) ---
@st.cache_data(show_spinner=False)
def load_data():
    # Replace with your actual public URL of the CSV file hosted in Azure Blob Storage
    csv_url = "https://llmbreakout.blob.core.windows.net/appdata/jailbreak_data.csv"
    df = pd.read_csv(csv_url)
    return df

# --- Load the CSV data from the public URL ---
df_all = load_data()

# --- Sidebar: User Role, Filters, Search, and Sorting ---
st.sidebar.header("User Options")

# Simulated user role selector
role = st.sidebar.selectbox("Select your role", ["Anonymous", "Registered", "Moderator"])

# Filtering options
llm_options = df_all["LLM"].unique().tolist()
selected_llms = st.sidebar.multiselect("Select LLM(s)", options=llm_options, default=llm_options)

status_options = df_all["Verification Status"].unique().tolist()
selected_status = st.sidebar.multiselect("Select Verification Status", options=status_options, default=status_options)

# Search box for prompt text
search_query = st.sidebar.text_input("Search Prompt Text")

# Sorting options
sort_by = st.sidebar.selectbox("Sort by", ["Submission Date", "Effectiveness Score", "Reproducibility Score"])

# Apply filters
df_filtered = df_all[df_all["LLM"].isin(selected_llms)]
df_filtered = df_filtered[df_filtered["Verification Status"].isin(selected_status)]
if search_query:
    df_filtered = df_filtered[df_filtered["Prompt"].str.contains(search_query, case=False, na=False)]

# Apply sorting
if sort_by == "Submission Date":
    df_filtered["Submission Date"] = pd.to_datetime(df_filtered["Submission Date"], errors="coerce")
    df_filtered = df_filtered.sort_values("Submission Date", ascending=False)
elif sort_by == "Effectiveness Score":
    df_filtered = df_filtered.sort_values("Effectiveness Score", ascending=False)
elif sort_by == "Reproducibility Score":
    df_filtered = df_filtered.sort_values("Reproducibility Score", ascending=False)

# --- Define tabs based on user role ---
tabs = ["Prompt Entries", "Submitters Leaderboard"]
if role == "Moderator":
    tabs.append("Moderation Panel")
if role == "Registered":
    tabs.append("Submit New Prompt")

tab1, tab2, *extra_tabs = st.tabs(tabs)

# --- Tab 1: Display Prompt Entries ---
with tab1:
    st.subheader("Crowd-Sourced Jailbreak Prompt Entries")
    st.dataframe(df_filtered, use_container_width=True)

# --- Tab 2: Submitters Leaderboard ---
with tab2:
    st.subheader("Top 5 Submitters Leaderboard")
    # Only consider verified entries for leaderboard scoring
    df_verified = df_all[df_all["Verification Status"] == "Verified"]
    leaderboard = df_verified.groupby("Submitter").agg(
        Verified_Submissions=("ID", "count"),
        Avg_Effectiveness=("Effectiveness Score", "mean"),
        Avg_Reproducibility=("Reproducibility Score", "mean")
    ).reset_index()
    # Compute score: (verified submissions) + (2 * Avg_Effectiveness) + (2 * Avg_Reproducibility)
    leaderboard["Score"] = (
        leaderboard["Verified_Submissions"] +
        2 * leaderboard["Avg_Effectiveness"] +
        2 * leaderboard["Avg_Reproducibility"]
    )
    leaderboard = leaderboard.sort_values("Score", ascending=False).head(5)
    st.dataframe(leaderboard, use_container_width=True)

# --- Tab for Registered Users: Submit New Prompt ---
if role == "Registered" and "Submit New Prompt" in tabs:
    with extra_tabs[0]:
        st.subheader("Submit a New Jailbreak Prompt")
        st.markdown("""
        Instead of storing new submissions in this app, please use our [Google Form](https://docs.google.com/forms/d/e/1FAIpQLSeiaaYnkucv-re-8lf4yQzK7KWBCw3f9FAAoySsRCUFw7nBww/viewform?usp=dialog) to submit your new jailbreak prompt.
        
        Your submission will automatically be recorded in a Google Sheet for review.
        """)
        st.info("Note: The source code is public on GitHub and the CSV data is hosted in a public Azure Storage container.")

# --- Tab for Moderators: Moderation Panel ---
if role == "Moderator" and "Moderation Panel" in tabs:
    with extra_tabs[-1]:
        st.subheader("Moderation Panel")
        # Show all entries that are currently unverified
        df_unverified = df_all[df_all["Verification Status"] == "Unverified"]
        if df_unverified.empty:
            st.info("No entries pending moderation.")
        else:
            for idx, row in df_unverified.iterrows():
                st.markdown(f"**ID:** {row['ID']} | **Submitter:** {row['Submitter']} | **Prompt:** {row['Prompt']}")
                if st.button(f"Mark as Verified (ID: {row['ID']})", key=f"verify_{row['ID']}"):
                    # In a real implementation, update the database or CSV accordingly.
                    df_all.loc[df_all["ID"] == row['ID'], "Verification Status"] = "Verified"
                    st.experimental_rerun()
