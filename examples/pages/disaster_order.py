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

#######################
# Load data

#st.write("### Upload the DV Order Spreadsheet")
#dv_order = pd.read_csv('data/DV_CALIBER.csv')
#st.dataframe(dv_order)

#######################

# Upload CSV file
st.write("### Upload the DV Order Spreadsheet")

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")


if uploaded_file is not None:
    # Read the CSV file into a Pandas DataFrame
    df = pd.read_csv('data/DV_CALIBER.csv')
    
    # Display the DataFrame
    # st.write("### Uploaded Data:")
    st.dataframe(df)


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
    SELECT distinct * FROM ANALYSIS.KWAN.DV_FINAL_ARCHIVE 
    where property_state='FL'
    order by client_ref_id;
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
            marker = folium.Marker([lat, long],popup=pop_txt,icon=folium.Icon(color='red',icon_size=(35, 35), icon='home', prefix='fa')).add_to(fg1)
        elif (m_df.DISASTER_INDICATOR[i]== 'IN BUFFER'):
            marker = folium.Marker([lat, long],popup=pop_txt, icon=folium.Icon(color='orange', icon='home', prefix='fa')).add_to(fg2)
        else:
            marker = folium.Marker([lat, long],popup=pop_txt,icon=folium.Icon(color='green', icon='home', prefix='fa')).add_to(fg3)

m.add_child(fg1)
m.add_child(fg2)
m.add_child(fg3)
folium.LayerControl(collapsed=False).add_to(m)

#m.save(outfile= "test.html")
#m
st.write("### the view of properties in the map")
st_folium(m, width=1150)

# Optional: Simple data visualization (e.g., plotting data)
if not data.empty:
    st.write("## Data Overview")
    
    # Display some summary statistics
    st.write(data.describe())

    # Optional: Line chart based on numeric data
    if data.select_dtypes(include='number').shape[1] > 0:
        st.line_chart(data.select_dtypes(include='number'))

# Add other widgets or interactive elements as needed
