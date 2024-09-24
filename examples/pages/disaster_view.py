import folium
import streamlit as st
from folium.plugins import GroupedLayerControl
from streamlit_folium import st_folium

import snowflake.connector
import pandas as pd

st.set_page_config(
    page_title="Properties in the disaster core and buffer",
    page_icon=":pencil:",
    layout="wide",
)

st.title("Properties in the disaster core and buffer")

# Function to connect to Snowflake and execute a query
# @st.cache_resource
def get_snowflake_data(sql):
    conn = snowflake.connector.connect(
        user='PYTHON_ETL',
        password='9Xm-7fY-xXs@.FZW',
        account='vka54242',
        warehouse='DATAOPS_XS',
        database='ANALYSIS',
        schema='KWAN',
        role='VEROS_RW'
    )
    
    cur = conn.cursor()
    cur.execute(sql)
    
    df = cur.fetch_pandas_all()
    
    cur.close()
    conn.close()
    
    return df
    
# check data for final report
runsql = (f"""
    SELECT * FROM ANALYSIS.KWAN.DV_FINAL_ARCHIVE order by client_ref_id;
    """)

# Load data from Snowflake
data = get_snowflake_data(runsql)

# Display the data in Streamlit
st.write("### The property list in the disaster")
st.dataframe(data)

# Only show the properties where both AVS_LATITUDE and AVS_LONGITUDE are not Null
m_df = data.dropna(subset=['AVS_LATITUDE', 'AVS_LONGITUDE'])

# Display the filtered dataframe in Streamlit
st.write("### Properties with Valid Latitude and Longitude")

st.dataframe(m_df)

# Check if filtered data is not empty
if not m_df.empty:
    # Get the last valid latitude and longitude to initialize the map
    init_lat = m_df.iloc[-1]["AVS_LATITUDE"]
    init_long = m_df.iloc[-1]["AVS_LONGITUDE"]
    
    # Initialize the Folium map
    m = folium.Map(location=[init_lat, init_long], zoom_start=6)

fg1 = folium.FeatureGroup(name="in event")
fg2 = folium.FeatureGroup(name="in buffer")
fg3 = folium.FeatureGroup(name="outside event")
                        
for i in m_df.index:
    lat = m_df.AVS_LATITUDE[i]
    long = m_df.AVS_LONGITUDE[i]
    pop_txt = folium.Popup(f"""
                           {m_df.PROPERTY_STREET_ADDRESS[i]}""",
                           max_width=150,
    )
    
    if lat and long:
        if ( m_df.DISASTER_INDICATOR[i]== 'INSIDE EVENT'):
            marker = folium.CircleMarker([lat, long],radius=0.5,color='red', fill=True,fill_color='red',fill_opacity=0.4).add_to(fg1)
        elif (m_df.DISASTER_INDICATOR[i]== 'IN BUFFER'):
            marker = folium.CircleMarker([lat, long],radius=0.5,color='orange', fill=True,fill_color='orange',fill_opacity=0.4).add_to(fg2)
        else:
            marker = folium.CircleMarker([lat, long],radius=0.5,color='green', fill=True,fill_color='green',fill_opacity=0.4).add_to(fg3)

m.add_child(fg1)
m.add_child(fg2)
m.add_child(fg3)
folium.LayerControl(collapsed=False).add_to(m)

#m.save(outfile= "test.html")
#m
st.write("### the view of properties in the map")
st_folium(m, width=1200)

# Optional: Simple data visualization (e.g., plotting data)
if not data.empty:
    st.write("## Data Overview")
    
    # Display some summary statistics
    st.write(data.describe())

    # Optional: Line chart based on numeric data
    if data.select_dtypes(include='number').shape[1] > 0:
        st.line_chart(data.select_dtypes(include='number'))

# Add other widgets or interactive elements as needed
