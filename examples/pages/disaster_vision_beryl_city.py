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

st.title("Disaster Analysis for Hurricane Beryl")

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


county_sql = (f"""
        SELECT f.state,f.FIPS_COUNTY_CODE,g.AVS_LATITUDE,g.AVS_LONGITUDE 
        FROM disaster_data.dv.FEMA_DECLARATION_STAGE f 
        LEFT JOIN disaster_data.dv.FIPS_COUNTY_GEOMETRY g 
        ON f.state=g.state AND f.FIPS_COUNTY_CODE =g.FIPS_COUNTY_CODE 
        WHERE UPPER(f.DECLARATIONTITLE) LIKE '%BERYL%'
        order by f.FIPS_COUNTY_CODE desc;
        """)
county_data =  get_snowflake_data(county_sql)

st.write("### The fips counties declared by FEMA for the Event")
st.dataframe(county_data)

ia_sql = (f"""
        SELECT ia.state, ia.city, g.AVS_LATITUDE,g.AVS_LONGITUDE, 
                sum(ia.APPROVEDFORFEMAASSISTANCE) AS approved_assistances 
        FROM  disaster_data.dv.FEMA_IA ia
        LEFT JOIN disaster_data.dv.STATE_CITY_GEOMETRY g 
        ON ia.state=g.state AND ia.CITY =g.HOUSE_CITY 
        WHERE ia.state='TX' AND DISASTERNUMBER =4798
            AND g.AVS_LATITUDE IS NOT NULL AND g.AVS_LONGITUDE IS NOT NULL 
        GROUP BY ia.state,ia.CITY , g.AVS_LATITUDE, g.AVS_LONGITUDE
        HAVING approved_assistances >50
        order by sum(ia.APPROVEDFORFEMAASSISTANCE) desc;
        """)

ia_data =  get_snowflake_data(ia_sql)

st.write("### The zipcodes granted  by FEMA IA Program")
st.dataframe(ia_data)
  
# check data for final report
runsql = (f"""
        SELECT dv.FEMA_DISASTER_NUMBER, dv.DISASTER_INDICATOR,dv.DISASTER_TYPE,dv.CITY,
        avg(dv.AVS_LATITUDE) AS avs_latitude,
        avg(dv.AVS_LONGITUDE) AS AVS_LONGITUDE,
        count(*) AS HOMES
        FROM DISASTER_DATA.dv.DISASTER_VIEW dv
        WHERE dv.FEMA_DISASTER_NUMBER  IN (4798)
        GROUP BY dv.FEMA_DISASTER_NUMBER, dv.DISASTER_INDICATOR,dv.DISASTER_TYPE,dv.CITY 
        ORDER BY count(*) DESC;
    """)

# Load data from Snowflake
data = get_snowflake_data(runsql)

# Display the data in Streamlit
st.write("### The property list in the disaster")
st.dataframe(data.head(50))

# Only show the properties where both AVS_LATITUDE and AVS_LONGITUDE are not Null
m_df = data.dropna(subset=['AVS_LATITUDE', 'AVS_LONGITUDE'])

# Check if filtered data is not empty
if not m_df.empty:
    # Get the last valid latitude and longitude to initialize the map
    init_lat = m_df.iloc[-1]["AVS_LATITUDE"]
    init_long = m_df.iloc[-1]["AVS_LONGITUDE"]
    
    # Initialize the Folium map
    m = folium.Map(location=[init_lat, init_long], zoom_start=6, title ="Properties in the disaster event")

fg1 = folium.FeatureGroup(name="in event")
fg2 = folium.FeatureGroup(name="in buffer")
#fg3 = folium.FeatureGroup(name="outside event")
fg4 = folium.FeatureGroup(name="FEMA declared")
fg5 = folium.FeatureGroup(name="IA approved")
                        
for i in m_df.index:
    lat = m_df.AVS_LATITUDE[i]
    long = m_df.AVS_LONGITUDE[i]
    homes = m_df.HOMES[i]
    r = 1 if homes < 2000 else 2 if homes < 10000 else 3
    
    pop_txt = folium.Popup(f"""
                           city:{m_df.CITY[i]},homes:{homes}""",
                           max_width=150,
    )
    
    if lat and long:
        if ( m_df.DISASTER_INDICATOR[i]== 'INSIDE EVENT'):
            marker = folium.CircleMarker([lat, long], popup=pop_txt, radius=r,color='red', fill=True,fill_color='red',fill_opacity=0.5).add_to(fg1)
        elif (m_df.DISASTER_INDICATOR[i]== 'IN BUFFER'):
            marker = folium.CircleMarker([lat, long],popup=pop_txt,radius=r, color='orange', fill=True,fill_color='orange',fill_opacity=0.5).add_to(fg2)
        else:
            marker = folium.CircleMarker([lat, long],popup=pop_txt,radius=r,color='green', fill=True,fill_color='green',fill_opacity=0.5).add_to(fg3)


for j in county_data.index:
    lat = county_data.AVS_LATITUDE[j]
    long = county_data.AVS_LONGITUDE[j]
    pop_txt = folium.Popup(f"""
                           countyCode:{county_data.FIPS_COUNTY_CODE[j]}
                           """)
    if lat and long:
        marker = folium.CircleMarker([lat, long], popup=pop_txt, radius=3,color='gray', fill=True,fill_color='grey',fill_opacity=0.5).add_to(fg4)

for k in ia_data.index:
    lat = ia_data.AVS_LATITUDE[k]
    long = ia_data.AVS_LONGITUDE[k]
    pop_txt = folium.Popup(f"""
                           City:{ia_data.CITY[k]}
                           """)
    if lat and long:
        marker = folium.CircleMarker([lat, long], popup=pop_txt, radius=2,color='skyblue', fill=True,fill_color='skyblue',fill_opacity=0.5).add_to(fg5)
        
    
m.add_child(fg1)
m.add_child(fg2)
#m.add_child(fg3)
m.add_child(fg4)
m.add_child(fg5)
folium.LayerControl(collapsed=False).add_to(m)

#m.save(outfile= "test.html")

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
