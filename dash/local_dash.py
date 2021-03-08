import dash
import fiona
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import numpy as np
import pandas as pd
import uuid
import time
import copy
import datetime
import simplejson as json
import argparse
from flask import request
import plotly.figure_factory as ff
import geopandas as gpd
import ast
import datetime
from datetime import timedelta
import pickle
import re
from statsmodels.tsa.seasonal import seasonal_decompose

'''
def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            print('%r  %2.2f ms' % \
                  (method.__name__, (te - ts) * 1000))
        return result
    return timed
'''

class MaxSizeCache:
    def __init__(self, size):
        self.cache = {}
        self.size = size
        self.birth_time = time.time()

    def in_cache(self, key):
        self.check_and_clear()
        return key in self.cache.keys()

    def add_to_cache(self, key, value):
        # if the max size have been reached delete the first 5 keys
        self.check_and_clear()
        self.manage_size()
        self.cache[key] = value

    def get(self, key):
        return self.cache[key]

    def check_and_clear(self):
        # check if the cache is older than 3 hours
        if self.birth_time + 10800 < time.time():
            print('Resenting Cache')
            self.cache = {}
            self.birth_time = time.time()

    def manage_size(self):
        if len(self.cache) == self.size:
            print('Removing Some Cache Items')
            keys = list(self.cache.keys())
            for i in range(5):
                del self.cache[keys[i]]


external_stylesheets = [dbc.themes.BOOTSTRAP,'style.css']
default_point_color = '#69A0CB'
trend_session_cache = MaxSizeCache(300)
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

trace_dict = {}

def geo_convert(j_file, today):

    if 'type' in j_file:
        df = pd.DataFrame()
        coordinates = []
        z_score = []
        new_jfile = {}

        new_jfile['type'] = j_file['type']
        new_jfile['features'] = []

        for i in range(len(j_file['features'])):

            new_jfile['features'].append(j_file['features'][i])
            coordinates.append(j_file['features'][i]['geometry']['coordinates'])
            z_score.append(j_file['features'][i]['properties']['z'])

        df['coordinates_'+today] = coordinates
        df['z_score_'+today] = z_score

        return df, new_jfile

    else:
        pass


def prep_session_data(session_id,url_path_name):
    if url_path_name is None:
        return

    id = str(session_id)

    if trend_session_cache.in_cache(id + '_df_geo') and trend_session_cache.in_cache(id + '_dates_times') + trend_session_cache.in_cache(id + '_new_jfile') + trend_session_cache.in_cache(id + '_df_dict'):
        return

    #KEEP FOR MULTIPLE CITIES
    #cities_df = pd.read_csv('cities.tsv',sep='\t')
    #KEEP FOR MULTIPLE CITIES

    #KEEP FOR MULTIPLE CITIES
    #sub = cities_df[cities_df['url'] == url_path_name]
    #KEEP FOR MULTIPLE CITIES

    if url_path_name[0] == '/':
        if len(url_path_name) == 1:
            print("Choosing Boulder as Default")
            url_path_name = 'boulder'
        else:
            print("Exchanging city...")
            url_path_name = url_path_name[1:]
        print(url_path_name)

    pickle_path = 'location_data/animation.pickle'
    with open(pickle_path, 'rb') as handle:  
        trend_session_cache.add_to_cache(id+'_df_geo', pickle.load(handle))

    with open('location_data/dates_times.pickle', 'rb') as handle:
        trend_session_cache.add_to_cache(id+'_dates_times', pickle.load(handle))

    with open('location_data/json_geo.json') as data_file:
        trend_session_cache.add_to_cache(id+'_new_jfile', json.load(data_file))

    pickle_path = 'location_data/trend_lines.pickle'
    with open(pickle_path, 'rb') as handle:
        trend_session_cache.add_to_cache(id+'_df_dict', pickle.load(handle))


#@timeit
def get_map(point_indexes, session_id):
    mapbox_access_token = open(".mapbox_token").read()
    px.set_mapbox_access_token(open(".mapbox_token").read())

    df = pd.DataFrame()

    if session_id:

        df_geo = trend_session_cache.get(session_id+'_df_geo')
        new_jfile = trend_session_cache.get(session_id+'_new_jfile')
        dates_times = trend_session_cache.get(session_id+'_dates_times')

        if len(point_indexes) > 0 and point_indexes[0] != -1:
            cols = []
            df = pd.DataFrame()
            for point in point_indexes:
                cols.append(df_geo.loc[df_geo['positions']== point])
            df = df.append(cols)
        else:
            df = df_geo 

        z_max = -1
        z_min = np.inf
        for j in range(0,len(dates_times)):
            today = dates_times[j][0]
            time = dates_times[j][1]
            today_index = today+'_'+time
            temp_max = df['z_score_'+today_index].max()
            temp_min = df['z_score_'+today_index].min()
            if temp_max > z_max:
                z_max = temp_max
            if temp_min < z_min:
                z_min = temp_min

        #CHANGE TO READ FROM FILE
        mapbox_access_token = 'pk.eyJ1IjoicnlhbmxheWVyIiwiYSI6ImNrOW9mZm1kcDAwMXczZG8xZGN2eWJsaWwifQ.-Ac4FRJlrzHzsyo4fmXUGA'
        #CHANGE TO READ FROM FILE

        frames = [{   
        'name':'frame_{}'.format(today+'_'+time),
        'data':[{
            'type':'choroplethmapbox',
            'z':df['z_score_'+today+'_'+time],
            'locations' : df['ids'], 
            'colorscale' : 'hot_r',
            'zmin' : z_min,
            'zmax' : z_max,
            'colorbar' : dict(thickness=20, ticklen=3),
            'geojson' : new_jfile,
            'text' : df['polygons'],
            'hovertemplate' : '<br> <b>Hot Spot </b>: %{z}<br>',
            'marker_line_width':0.1, 
            'marker_opacity': 0.7
        }],           
        } for today,time in dates_times]

        sliders = [{
            'transition':{'duration': 5},
            'x':0.08, 
            'len':0.88,
            'currentvalue':{'font':{'size':15}, 'visible':True, 'xanchor':'center'},  
            'steps':[
                {
                    'label':today+'_'+time[:2],
                    'method':'animate',
                    'args':[
                        ['frame_{}'.format(today+'_'+time)],
                        {'mode':'immediate', 'frame':{'duration':1000, 'redraw': True}, 
                         'transition':{'duration':150}}
                      ],
                } for today,time in dates_times]
        }]

        play_button = [{
            'type':'buttons',
            'buttons':[{ 
                'label':'Play', # Play
                'method':'animate',
                'args':[None]
            }]
        }]

        data = frames[0]['data']

        layout = go.Layout(
            sliders=sliders,
            updatemenus=[{
            'type':'buttons',
            'showactive':True,
            'x':0.045, 'y':-0.08,
            'buttons':[{ 
                'label':'Play',
                'method':'animate',
                'args':[
                    None,
                    {
                        'frame':{'duration':1000, 'redraw':True},
                        'transition':{'duration':150},
                        'fromcurrent':True,
                        'mode':'immediate',
                    }
                ]
            }]
        }],
            mapbox={
                'accesstoken':mapbox_access_token,
                'center':{"lat": 40.0086, "lon": -105.28},
                'zoom':6,
                'style':'light',
            }
        )

        fig = go.Figure(data=data, layout=layout, frames=frames)

        

        fig.update_layout(title_x =0.5,mapbox_style = 'dark', template = 'plotly_dark',
                         mapbox = dict(center= dict(lat=40.0086, lon=-105.275),            
                                       accesstoken= mapbox_access_token,
                                       zoom=11
                                       ))

        fig.update_layout(mapbox = dict(accesstoken= mapbox_access_token,
                                       layers = [ dict(
                                           type = "symbol",
                                           color = "#2600ff",
                                           coordinates = [40.0086, -105.28]
                                       )]))
        print('print map done')
        return fig

    else:
        print('try refreshing')

        fig = go.Figure(go.Scattermapbox(\
            mode='markers',
            marker=go.scattermapbox.Marker(size=14)))

        fig.update_layout(
        hovermode='closest',
        mapbox_style="dark",
        mapbox=dict(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=go.layout.mapbox.Center(
            ),
            pitch=0,
            zoom=10,
        ))

        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

        return fig


@app.callback(
    [Output('weekend_score', 'figure'),
    Output('map', 'figure')],
    [Input('weekend_score', 'clickData'),
    Input('session-id','children'),
    Input('map','clickData'),
    Input('map','selectedData'),
    Input('url', 'pathname')])

def update_scatter_plots(
                         ws_data,
                         session_id,
                         map_data,
                         map_selection,
                         url_path_name,
                         ):
    prep_session_data(session_id,url_path_name)


    df_geo = trend_session_cache.get(session_id + '_df_geo')

    ctx = dash.callback_context
    map_indexes = [-1]
    ws_indexes = [-1]

    if ctx.triggered[0]['prop_id'] == 'weekend_score.clickData':

        ws_indexes = [int(ws_data['points'][0]['curveNumber'])]
        map_indexes = []
        for point in ws_indexes:
            map_indexes.append(trace_dict[point])

    elif ctx.triggered[0]['prop_id'] == 'map.clickData':

        indexes = [map_data['points'][0]['location']]
        map_indexes = []
        for point in indexes:
            map_indexes.append(df_geo.loc[df_geo['ids']== int(point)]['positions'].values[0])
        ws_indexes = []
        for pos in map_indexes:
            cross_points = [k for k,v in trace_dict.items() if v == pos]
            ws_indexes.extend(cross_points)

    elif ctx.triggered[0]['prop_id'] == 'map.selectedData':

        indexes = [x['location'] for x in map_selection['points']]
        map_indexes = []
        for point in indexes:
            map_indexes.append(df_geo.loc[df_geo['ids']== int(point)]['positions'].values[0])
        ws_indexes = []
        for pos in map_indexes:
            cross_points = [k for k,v in trace_dict.items() if v == pos]
            ws_indexes.extend(cross_points)

    return weekend_score_callback(session_id,ws_indexes), \
        get_map(map_indexes, session_id)


def weekend_score_callback(session_id,point_indexes):

    df_dict = trend_session_cache.get(session_id + '_df_dict')
    df_geo = trend_session_cache.get(session_id + '_df_geo')
    new_jfile = trend_session_cache.get(session_id + '_new_jfile')

    dict_keys = []

    if len(point_indexes) > 0 and point_indexes[0] != -1:
        cols = []
        for point in point_indexes:
            cols.append(trace_dict[point])

        dict_keys = cols    
    else:
        dict_keys = df_dict.keys()

    fig = make_subplots(rows=3, cols=1, subplot_titles = ("0000 UTC", "0800 UTC", "1600 UTC"))
    i = 0
    for key in df_dict.keys():
        if key in dict_keys:

            df = df_dict[key]
            df['0000'] = df['0000'].astype(float)
            df['0800'] = df['0800'].astype(float)
            df['1600'] = df['1600'].astype(float)
            dates = df['dates']


            c_0 = df['0000'].to_list()
            c_8 = df['0800'].to_list()
            c_16 = df['1600'].to_list()

            j = 0
            for c in [c_0, c_8, c_16]:
                result_mul = seasonal_decompose(c,
                                     period=7,
                                     model = 'multiplicative',
                                     extrapolate_trend='freq')
            
                s  = result_mul.seasonal
                t  = result_mul.trend
                t  = np.array(result_mul.trend)
                t = t - t[0]
                trace_dict[i] = key
                fig.add_trace(go.Scatter(x = dates, y = t, mode = 'lines', customdata = df_geo['ids'], showlegend = False),row = j+1, col = 1)
                i = i + 1
                j = j + 1


    fig.update_layout(template = 'plotly_dark')
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_xaxes(title_text="Date", row=3, col=1)
    fig.update_yaxes(title_text="Crisis Density", row=1, col=1)
    fig.update_yaxes(title_text="Crisis Density", row=2, col=1)
    fig.update_yaxes(title_text="Crisis Density", row=3, col=1)

    print('fig done')

    return fig

colors =  {
    'background' :'black'
}

def layout():
    session_id = str(uuid.uuid4())

    return html.Div(style = {'backgroundColor' : colors['background']},
        children = [dcc.Location(id='url', refresh=False),
        dbc.Row([
            html.Div([
                html.H1('COvid-19'),
            ],style={'backgroundColor' : colors['background'],'grid-row': '1','grid-column': '2'}),
            html.Div([
                html.Img(src='assets/covid19.png', height=50),
                html.Img(src='assets/cu.png', height=50),
                html.Img(src='assets/csu.jpg', height=50)
            ], style={'backgroundColor' : colors['background'],'grid-row': '1','grid-column': '3'})
        ],style={'backgroundColor' : colors['background'],'display': 'grid', 'grid-template-columns': 'auto auto auto'}),
        dbc.Col([
            dbc.Row( [
                dbc.Col( dcc.Graph(id='map',
                                   figure=get_map([], None),
                                   style={'backgroundColor' : colors['background'],'height':'90vh'})),
            ],no_gutters=True),

        ],width=7,style={'backgroundColor' : colors['background'],'float': 'left','height':'100vh','padding':'0'}),
        dbc.Col([
            dcc.Graph(id='weekend_score',style={'backgroundColor' : colors['background'],'height':'90vh'}),

        ],width=5,style={'backgroundColor' : colors['background'],'float': 'left','height':'100vh'}),
        # Hidden div inside the app that stores the intermediate value
        html.Div(session_id,id='session-id', style={'display': 'none'})
    ])


app.layout = layout
app.title = 'COvid-19'

if __name__ == '__main__':
    app.run_server(debug=True)