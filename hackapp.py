import streamlit as st
import pandas as pd
import pydeck as pdk
from iso3166 import countries
import datetime
import plotly.express as px
import json
#import graphviz as graphviz

data = pd.DataFrame()
cnt_code3 = ''
tf = ''
currev = {}
ev_col_dict = {}
evlist = []
zoom_level = 0

def main():
  global data
  global currev
  global ev_col_dict
  global zoom_level
  title = st.sidebar.header("NATO ACT TIDE Hackathon App")
  knights = st.sidebar.warning("by ⚔️ who say Ni")

  info = st.text("Loading 🗺️...")
  country_list = load_countries()
  country_lat_lon = load_country_lat_lan()
  ev_col_dict = {"Battles": '[255,0,0,255]', 
                 "Protests": '[0,0,255,128]',
                 "Explosions/Remote violence": '[0,0,255,255]', 
                 "Strategic developments": '[255,255,0,160]', 
                 "Riots": '[255,0,0,128]',
                 "Violence against civilians": '[255,192,0,255]'}
  mapstyle_dict = {"streets": "streets-v11",
                   "light": "light-v10",
                   "dark": "dark-v10",
                   "satellite": "satellite-v9"}
  info.text('')
  
  page = st.sidebar.selectbox("Choose a page", ["Homepage", "Exploration", "Prediction", "Country statistics", "Workflow", "Sourcecode", "Test"])

  if page == "Homepage":
    st.image('data/hackathon.jpg')
  elif page == "Exploration":
    global cnt_code3
    global tf
    event_start = datetime.date(1997,1,1)
    event_end = datetime.date(2020,2,18)

    try:
      with open('sources.json') as f:
        sources = json.load(f)
        datasource = st.sidebar.selectbox('Data source (work in progress)', [s for s,_ in sources.items()], 0)
        data_source = sources[datasource]
        run = True
    except:
      st.error('sources.json not found')
      run = False

    if st.sidebar.checkbox("Select Country"):
      country = st.sidebar.selectbox('',country_list)
      cnt_code2 = countries.get(country).alpha2
      cnt_code3 = countries.get(country).alpha3
      lat = country_lat_lon.loc[cnt_code2].lat
      lon = country_lat_lon.loc[cnt_code2].lon
    else:
      lat = 31.046051
      lon = 34.851612

    zoom_level = st.sidebar.slider("Zoomlevel", 2, 11, 5, 1)
    mapstyle = st.sidebar.selectbox('Map style', list(mapstyle_dict), 1) 
    style = mapstyle_dict[mapstyle]
    events = st.sidebar.multiselect('Select events', [e for e,_ in ev_col_dict.items()], [e for e,_ in ev_col_dict.items()][0])
    st.sidebar.text('Timeframe (todo)')
    #event_start = st.sidebar.date_input("First event", datetime.date(1997, 1, 1))
    #event_end = st.sidebar.date_input("Last event", datetime.date(2020, 2, 18))
    #ev_start = datetime.datetime.combine(event_start, datetime.time(0,0,0))
    #ev_end = datetime.datetime.combine(event_end, datetime.time(0,0,0))
    currev = {}
    for event in events:
      currev[event] = ev_col_dict[event]

    if run:
      if st.button("Run"):
        data = load_data(data_source)
        info.text = ''
        ALL_LAYERS = prepare_layers(data, currev)
        selected_layers = [layer for _, layer in ALL_LAYERS.items()]
        st.pydeck_chart(pdk.Deck(map_style="mapbox://styles/mapbox/"+style,
            initial_view_state={"latitude": lat, "longitude": lon, "zoom": zoom_level, "pitch": 0},
            layers=selected_layers))
  elif page == "Prediction":
    df = pd.read_csv('data/result.csv')
    fig = px.choropleth(df, locations="iso3", locationmode="ISO-3", hover_name="iso3", 
                        animation_frame="date", color='rfc', width=600, height=800,
                        projection="orthographic")
    st.plotly_chart(fig)
  elif page == "Country statistics":
    st.sidebar.warning('Currently using ACLED dataset')
    data = load_data('data/acled_data_sm.csv')
    event_start = datetime.date(1997,1,1)
    event_end = datetime.date(2020,2,18)
    country = st.selectbox('Select country',country_list)
    cnt_code2 = countries.get(country).alpha2
    cnt_code3 = countries.get(country).alpha3
    lat = country_lat_lon.loc[cnt_code2].lat
    lon = country_lat_lon.loc[cnt_code2].lon
    try:
      dg = data
      dg['event_date'] = pd.to_datetime(dg['event_date'])
      dg = dg.groupby(['iso3', 'event_date', 'event_type']).agg('count').reset_index()
      dg = dg[dg['iso3'] == cnt_code3]
      dh = dg[['event_date', 'event_type', 'fatalities']]
      event_start = dh.iloc[0].event_date.date()
      dh.rename(columns={'fatalities': 'counter'}, inplace=True)
      st.text(f'Data available from {event_start} - {event_end}')
      data_uv = data
      dg = data_uv.groupby(['event_type', 'iso3']).agg(['count'])
      statistic = []
      for event,_ in ev_col_dict.items():
        statistic.append(f'{event}: {dg.loc[(event,cnt_code3)][0]}')
      for sta in statistic:
        st.text(f'{sta}')
      evtyp = st.selectbox('event', [e for e in ev_col_dict.keys()], 0)
      dh = dh[dh['event_type'] == evtyp]
      fig = px.scatter(dh, x="event_date", y="counter")
      st.plotly_chart(fig)
    except:
      st.header(f'No statistics for {country} found')
  elif page == "Sourcecode":
    with open('hackapp.py', encoding='utf-8') as f:
      st.code(f.read())
  elif page == "Test":
    # get curated list
    from os import listdir
    onlyfiles = [f for f in listdir('data/curated')]
    filedict = {}
    for dfile in onlyfiles:
        filedict[f'{dfile.split(".")[0].replace("_"," ")}'] = dfile
    source = st.sidebar.selectbox('Aggregated data', [f for f in filedict.keys()], 2)
    dfile = filedict[source]
    df = pd.read_csv('data/curated/'+dfile)
    dg = df.groupby(['Year', 'Country']).agg(sum).reset_index()
    maxval = dg.loc[dg['Events' if 'events' in dfile else 'Fatalities'].idxmax()][2]
    temp = []
    for c in dg['Country']:
       temp.append(countries.get(c).alpha3)
    dg['ISO3'] = temp
    fig = px.choropleth(dg, locations="ISO3", hover_name="Country", locationmode="ISO-3", animation_frame="Year", color='Events' if 'events' in dfile else 'Fatalities',
                        range_color=(0,maxval), width=600, height=800, projection="orthographic")
    st.plotly_chart(fig)
    # df = pd.read_csv('data/hackathon_crisis.csv')
    # df.drop(columns=['country'])
    # dg = df.groupby(['month', 'iso3']).agg(sum).reset_index()
    # fig = px.choropleth(dg, locations="iso3", hover_name="iso3", locationmode="ISO-3", animation_frame="month", color='battle_case', width=600, height=800, projection="orthographic")
    # st.plotly_chart(fig)

def load_data(datasource):
  if 'http' in datasource:
    df = pd.read_json(datasource)
    df = pd.json_normalize(df['data'])
    df = df.drop(columns = ['actor1', 'assoc_actor_1', 'inter1', 'actor2', 'assoc_actor_2', 'inter2',
           'interaction', 'year', 'iso', 'event_id_no_cnty', 'notes', 'timestamp', 'admin1', 'admin2', 'admin3',
                          'time_precision', 'data_id', 'geo_precision', 'source', 'source_scale'])
    return df
  else:
    return pd.read_csv(datasource)

@st.cache
def load_countries():
  country_list = [c.name for c in countries]
  del country_list[1] # remove °Aland islands
  return country_list

@st.cache
def load_country_lat_lan():
  return pd.read_csv('data/countries.csv', header=0, index_col=0)

def getdata(ev_type):
  data_uv = data
  data_uv.groupby(['event_type', 'country']).agg(['count'])
  data_uv['event_date'] = pd.to_datetime(data_uv['event_date'])
  if tf:
    ev_t = data_uv[(data_uv['event_type'] == ev_type) & (data_uv['event_date']>ev_start) & (data_uv['event_date']<ev_end)]
  else:
    ev_t = data_uv[((data_uv['event_type'] == ev_type) & (data_uv['iso3'] == cnt_code3)) if cnt_code3 != '' else (data_uv['event_type'] == ev_type)]
  return ev_t[['latitude', 'longitude']].reset_index(drop=True)

def prepare_layers(data, evclist):
  data_layer = st.text('Preparing')
  data_progress = st.progress(0)
  ALL_LAYERS = {}
  count = len(evclist)
  steps = int(100/count)
  count = 1
  for event, color in evclist.items():
    data_layer.text(f'Preparing {event} layer')
    layer = pdk.Layer("ScatterplotLayer", getdata(event), get_position=["longitude", "latitude"], get_radius=2000 if zoom_level<10 else 250, get_color=color)
    ALL_LAYERS[event] = layer
    data_progress.progress(steps*count)
    count += 1
  data_progress.empty()
  data_layer.empty()
  return ALL_LAYERS

if __name__=='__main__':
  main()