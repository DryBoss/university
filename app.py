import streamlit as st
import pandas as pd
import os

# Set Page Config
st.set_page_config(page_title="Academic Network Research", layout="wide")

st.title("🎓 Interdisciplinary Academic Network Analysis")

# --- 1. CONFIGURATION & MAPPING ---
DEPT_MAPPER = {
    "ACCE": "Applied Chemistry and Chemical Engineering",
    "CSE": "Computer Science and Engineering",
    "EEE": "Electrical and Electronic Engineering",
    "GEB": "Genetic Engineering and Biotechnology",
    "HRM": "Human Resource Management",
    "IER": "Institute of Education and Research",
    "LAW": "Law",
    "Language & Linguistics": "Linguistics",
    "Pali": "Pali and Buddhist Studies"
}

# --- 2. FILE HELPER ---
def get_file_path(filename):
    search_paths = [
        filename,
        os.path.join("data", filename),
        os.path.join("data", "subject-choice", filename),
        os.path.join("..", "data", "subject-choice", filename)
    ]
    for p in search_paths:
        if os.path.exists(p):
            return p
    return None

# --- 3. DATA LOADING ---
@st.cache_data
def load_all_data():
    df_net = pd.DataFrame()
    net_path = get_file_path("related-course.csv")
    if net_path:
        df_net = pd.read_csv(net_path)
        df_net.columns = df_net.columns.str.strip()
        df_net = df_net.dropna(subset=['Department', 'Related Dept'])
        df_net['Department'] = df_net['Department'].astype(str).str.strip()
        df_net['Related Dept'] = df_net['Related Dept'].astype(str).str.strip()

    all_prestige = []
    units, years = ['a', 'b', 'c', 'd'], ['2122', '2223', '2324']
    for u in units:
        for y in years:
            fname = f"{y}{u}.csv"
            path = get_file_path(fname)
            if path:
                try:
                    tmp = pd.read_csv(path)
                    tmp.columns = tmp.columns.str.strip()
                    if 'Department' in tmp.columns:
                        tmp.rename(columns={'Department': 'Subject'}, inplace=True)
                    if 'Subject' in tmp.columns and 'Merit' in tmp.columns:
                        tmp['Unit'] = u.upper()
                        all_prestige.append(tmp[['Subject', 'Merit', 'Unit']])
                except: continue
    
    df_pres = pd.concat(all_prestige, ignore_index=True) if all_prestige else pd.DataFrame()
    if not df_pres.empty:
        df_pres['Merit'] = pd.to_numeric(df_pres['Merit'], errors='coerce')
        df_pres = df_pres.dropna(subset=['Subject', 'Merit'])
        df_pres['Clean_Subject'] = df_pres['Subject'].astype(str).str.strip()

    return df_net, df_pres

df_net, df_pres = load_all_data()

# --- 4. UI LOGIC ---
if df_net.empty:
    st.error("🚨 'related-course.csv' not found.")
else:
    tab1, tab2 = st.tabs(["🔍 Department Recommender", "🌐 Network View"])

    with tab1:
        st.header("🔍 Department Recommender")
        dept_list = sorted(df_net['Department'].unique())
        selected_dept = st.selectbox("Search for a Department:", dept_list)

        if selected_dept:
            # A. NETWORK ANALYSIS
            recs_all = df_net[df_net['Department'] == selected_dept]
            total_raw_links = recs_all['Related Dept'].nunique()
            
            # Visual Logic: Display only connections with 3+ courses
            rec_stats = recs_all.groupby('Related Dept').size().reset_index(name='count')
            rec_stats_visual = rec_stats[rec_stats['count'] >= 3].sort_values('count', ascending=False)
            
            prestige_score = "N/A"
            selected_rank_range = "Rank N/A"
            
            # B. MERIT ANALYSIS for Selected Dept
            if not df_pres.empty:
                search_term = DEPT_MAPPER.get(selected_dept, selected_dept)
                dept_data = df_pres[df_pres['Clean_Subject'].str.contains(search_term, case=False, na=False)]
                
                if not dept_data.empty:
                    g_max = df_pres['Merit'].max()
                    dept_merit = dept_data['Merit'].median()
                    if pd.notna(dept_merit):
                        score = ((g_max - dept_merit) / g_max) * 100
                        prestige_score = f"{score:.1f}/100"
                    
                    # Calculate Selected Dept Rank Range
                    s_min = int(dept_data['Merit'].min())
                    s_max = int(dept_data['Merit'].max())
                    selected_rank_range = f"{s_min} - {s_max}"

            # C. DISPLAY METRICS
            c1, c2, c3 = st.columns(3)
            c1.metric("Prestige Score", prestige_score)
            c2.metric("Total Connections", f"{total_raw_links} Depts")
            c3.metric("Merit Range", selected_rank_range, help="The historical merit range for this department.")

            st.divider()

            # D. FULL WIDTH CURRICULUM LINKS WITH MERIT RANGES
            st.subheader("🎯 Curriculum Links")
            
            if not rec_stats_visual.empty:
                FIXED_MAX = 10 
                
                for _, row in rec_stats_visual.iterrows():
                    related_name = row['Related Dept']
                    progress_val = min(1.0, row['count'] / FIXED_MAX)
                    
                    # Fetch Merit Range for the Related Department
                    rank_range = "Rank N/A"
                    if not df_pres.empty:
                        rel_search = DEPT_MAPPER.get(related_name, related_name)
                        rel_data = df_pres[df_pres['Clean_Subject'].str.contains(rel_search, case=False, na=False)]
                        
                        if not rel_data.empty:
                            min_rank = int(rel_data['Merit'].min())
                            max_rank = int(rel_data['Merit'].max())
                            rank_range = f"Merit: {min_rank} - {max_rank}"
                    
                    # Layout
                    with st.container():
                        col_name, col_rank, col_bar = st.columns([2, 1, 3])
                        with col_name:
                            st.write(f"**{related_name}**")
                        with col_rank:
                            st.write(f"`{rank_range}`")
                        with col_bar:
                            st.progress(progress_val)
                            st.caption(f"{row['count']} Shared Courses")
            else:
                st.info(f"No strong curriculum connections (3+ courses) found for {selected_dept}.")

    with tab2:
        st.header("🌐 Global Connectivity Map")
        chord_path = get_file_path("academic_chord.html")
        if chord_path:
            with open(chord_path, 'r') as f:
                st.components.v1.html(f.read(), height=800)