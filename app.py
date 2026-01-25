import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import os

# Set Page Config for Mobile/Wide screens
st.set_page_config(page_title="Academic Network Research", layout="wide")

st.title("🎓 Interdisciplinary Academic Network Analysis")
st.markdown("Exploring the popularity and connectivity of university departments.")

# Helper to find files in the repo structure
def get_file_path(filename, subfolder=""):
    base_path = os.path.dirname(__file__)
    return os.path.join(base_path, subfolder, filename)

# 1. Load Data
@st.cache_data
def load_data():
    # Try multiple common paths to be safe
    possible_paths = [
        get_file_path("related-course.csv", "data"),
        get_file_path("related-course.csv"),
        "related-course.csv"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            df = pd.read_csv(path)
            df = df.dropna(subset=['Department', 'Related Dept'])
            # Clean strings to prevent duplicate nodes
            df['Department'] = df['Department'].astype(str).str.strip()
            df['Related Dept'] = df['Related Dept'].astype(str).str.strip()
            return df
    
    st.error("Data file 'related-course.csv' not found. Please check your GitHub folder structure.")
    return pd.DataFrame()

df = load_data()

if not df.empty:
    # 2. Sidebar Filters
    st.sidebar.header("Filter Connections")
    min_weight = st.sidebar.slider("Minimum Connection Strength (Number of Courses)", 1, 10, 1)

    # Group data and filter by slider
    links = df.groupby(['Department', 'Related Dept']).size().reset_index(name='value')
    links = links[links['value'] >= min_weight]

    # 3. Main Dashboard Tabs
    tab1, tab2, tab3 = st.tabs(["🌐 Network View", "🌊 Knowledge Flow", "📊 Department Stats"])

    with tab1:
        st.header("Interdisciplinary Chord Diagram")
        chord_path = get_file_path("academic_chord_weighted.html")
        
        if os.path.exists(chord_path):
            with open(chord_path, 'r', encoding='utf-8') as f:
                html_data = f.read()
            st.components.v1.html(html_data, height=800, scrolling=True)
        else:
            st.warning("Chord HTML file not found. Run your visualization script first.")

    with tab2:
        st.header("Sankey Flow Diagram")
        if not links.empty:
            all_nodes = list(pd.concat([links['Department'], links['Related Dept']]).unique())
            mapping = {node: i for i, node in enumerate(all_nodes)}
            
            fig = go.Figure(data=[go.Sankey(
                node = dict(
                    pad = 15, thickness = 20, line = dict(color = "black", width = 0.5),
                    label = all_nodes, color = "teal"
                ),
                link = dict(
                    source = links['Department'].map(mapping),
                    target = links['Related Dept'].map(mapping),
                    value = links['value']
                )
            )])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No connections match the current filter strength.")

    with tab3:
        st.header("Ranking Metrics")
        if not links.empty:
            G = nx.from_pandas_edgelist(links, 'Department', 'Related Dept', create_using=nx.DiGraph())
            
            rankings = pd.DataFrame({
                'Department': list(G.nodes()),
                'Influence (In-Degree)': list(nx.in_degree_centrality(G).values()),
                'Dependency (Out-Degree)': list(nx.out_degree_centrality(G).values()),
                'Bridge Factor': list(nx.betweenness_centrality(G).values())
            }).sort_values('Influence (In-Degree)', ascending=False)
            
            st.subheader("Top Influential Departments")
            st.dataframe(rankings.style.background_gradient(cmap='YlGnBu'), use_container_width=True)
            
            # Download Button
            csv = rankings.to_csv(index=False).encode('utf-8')
            st.download_button("Download Rankings CSV", data=csv, file_name="rankings.csv", mime="text/csv")

st.sidebar.markdown("---")
st.sidebar.info("Developed for: Research on Departmental Popularity Trends.")