import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import seaborn as sns

# Set Page Config for Mobile/Wide screens
st.set_page_config(page_title="Academic Network Research", layout="wide")

st.title("🎓 Interdisciplinary Academic Network Analysis")
st.markdown("Exploring the popularity and connectivity of university departments.")

# 1. Load Data
@st.cache_data
def load_data():
    df = pd.read_csv('./../data/related-course.csv')
    df = df.dropna(subset=['Department', 'Related Dept'])
    return df

df = load_data()

# 2. Sidebar Filters
st.sidebar.header("Filter Connections")
min_weight = st.sidebar.slider("Minimum Connection Strength", 1, 10, 1)

# Group data and filter by slider
links = df.groupby(['Department', 'Related Dept']).size().reset_index(name='value')
links = links[links['value'] >= min_weight]

# 3. Main Dashboard Tabs
tab1, tab2, tab3 = st.tabs(["Network View", "Knowledge Flow", "Stats"])

with tab1:
    st.header("Departmental Relationship Web")
    # Using existing Chord or NetworkX logic
    # For simplicity, we can display your saved HTML Chord here
    with open("academic_chord_weighted.html", 'r') as f:
        html_data = f.read()
    st.components.v1.html(html_data, height=800, scrolling=True)

with tab2:
    st.header("Sankey Flow Diagram")
    # We can rebuild the Sankey dynamically based on the slider
    all_nodes = list(pd.concat([links['Department'], links['Related Dept']]).unique())
    mapping = {node: i for i, node in enumerate(all_nodes)}
    
    fig = go.Figure(data=[go.Sankey(
        node = dict(label = all_nodes, color = "teal"),
        link = dict(
            source = links['Department'].map(mapping),
            target = links['Related Dept'].map(mapping),
            value = links['value']
        )
    )])
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("Department Rankings")
    # Dynamic table
    G = nx.from_pandas_edgelist(links, 'Department', 'Related Dept', create_using=nx.DiGraph())
    rankings = pd.DataFrame({
        'Department': list(G.nodes()),
        'Influence Score': list(nx.in_degree_centrality(G).values())
    }).sort_values('Influence Score', ascending=False)
    
    st.dataframe(rankings, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.info("Developed for: Research on Departmental Popularity Trends.")