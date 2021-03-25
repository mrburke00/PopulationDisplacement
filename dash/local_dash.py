import dash
import fiona
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import flask
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
import os
import csv
import random
#from app import app


class MaxSizeCache:

	def __init__(self):
		self.df_geo = pd.DataFrame()
		self.dates_times = {}
		self.new_jfile = {}
		self.df_dict = {}

	def build(self, target):
		with open('saved_data/'+target+'/animation.pickle', 'rb') as handle:  
			self.df_geo = pickle.load(handle)

		with open('saved_data/'+target+'/dates_times.pickle', 'rb') as handle:
			self.dates_times = pickle.load(handle)

		with open('saved_data/'+target+'/json_geo.json') as data_file:
			self.new_jfile = json.load(data_file)

		with open('saved_data/'+target+'/trend_lines.pickle', 'rb') as handle:
			self.df_dict = pickle.load(handle)




external_stylesheets = [dbc.themes.BOOTSTRAP,'style.css']
default_point_color = '#69A0CB'
cache = MaxSizeCache()
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
#server = app.server
#app.config.suppress_callback_exceptions = True

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


def prep_session_data(url_path):

	target = url_path[1:]
	cache.build(target)
	#if len(cache.df_geo.index) != 0 and cache.dates_times and cache.new_jfile and cache.df_dict:
		#return



#@timeit
def get_map(point_indexes, build, url_path):
	if build:
		if url_path: prep_session_data(url_path)
		mapbox_access_token = open("mapbox_token").read()
		px.set_mapbox_access_token(open("mapbox_token").read())

		map_coords = random.choice(list(cache.df_dict.keys()))
		map_coords = map_coords.split(',')
		map_lat = round(float(map_coords[0]),3)
		map_lon = round(float(map_coords[1]),3)

		df = pd.DataFrame()
		df_geo = cache.df_geo
		new_jfile = cache.new_jfile
		dates_times = cache.dates_times

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
				'center':{"lat": map_lat, "lon": map_lon},
				'zoom':6,
				'style':'light',
			}
		)

		fig = go.Figure(data=data, layout=layout, frames=frames)

		

		fig.update_layout(title_x =0.5,mapbox_style = 'dark', template = 'plotly_dark',
						 mapbox = dict(center= dict(lat=map_lat, lon=map_lon),            
									   accesstoken= mapbox_access_token,
									   zoom=11
									   ))

		fig.update_layout(mapbox = dict(accesstoken= mapbox_access_token,
									   layers = [ dict(
										   type = "symbol",
										   color = "#2600ff",
										   coordinates = [map_lat, map_lon]
									   )]))
		print('print map done')
		return fig



@app.callback(
	[Output('weekend_score', 'figure'),
	Output('map', 'figure')],
	[Input('weekend_score', 'clickData'),
	Input('map','clickData'),
	Input('map','selectedData')])

def update_scatter_plots(
						 ws_data,
						 map_data,
						 map_selection
						 ):
	print('something here changed')
	df_geo = cache.df_geo

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

	return weekend_score_callback(ws_indexes, True, None), \
		get_map(map_indexes, True, None)


def weekend_score_callback(point_indexes, build, url_path):

	if build:
		if url_path: prep_session_data(url_path)
		df_dict = cache.df_dict
		df_geo = cache.df_geo
		new_jfile = cache.new_jfile

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
				if(len(dates)< 14):
					period = len(dates)//2
				else:
					period = 7
				j = 0
				for c in [c_0, c_8, c_16]:
					result_mul = seasonal_decompose(c,
										 period=period,
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

def build_pre_graphs(target):
	path = 'saved_data/'+target+'/pre_graph_data.csv'

	with open(path, 'r') as file:
	    reader = csv.reader(file)
	    rows = [r for r in reader]
	    trends_lower = rows[0]
	    trends_upper = rows[1]
	    trends_median = rows[2]
	    dates = rows[3]

	fig = go.Figure()
	fig.add_trace(go.Scatter(y=trends_lower, x=dates,
						mode='lines',
						name='decrease'))
	fig.add_trace(go.Scatter(y=trends_upper, x=dates,
						mode='lines',
						name='increase'))
	fig.add_trace(go.Scatter(y=trends_median, x=dates,
						mode='lines',
						name='median'))
	fig.update_layout(template = 'plotly_dark')
	return fig


colors =  {
	'background' :'black'
}


'''def layout():
	
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
								   figure=get_map([]),
								   style={'backgroundColor' : colors['background'],'height':'90vh'})),
			],no_gutters=True),

		],width=7,style={'backgroundColor' : colors['background'],'float': 'left','height':'100vh','padding':'0'}),
		dbc.Col([
			dcc.Graph(id='weekend_score', figure = weekend_score_callback([]), style={'backgroundColor' : colors['background'],'height':'90vh'}),

		],width=5,style={'backgroundColor' : colors['background'],'float': 'left','height':'100vh'}),

	])'''
def layout(build, url_path):
	print("here")
	layout1 = html.Div(style = {'backgroundColor' : colors['background']},
			children = [
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
									   figure=get_map([], build, url_path),
									   style={'backgroundColor' : colors['background'],'height':'90vh'})),
				],no_gutters=True),

			],width=7,style={'backgroundColor' : colors['background'],'float': 'left','height':'100vh','padding':'0'}),
			dbc.Col([
				dcc.Graph(id='weekend_score', figure = weekend_score_callback([], build, url_path), style={'backgroundColor' : colors['background'],'height':'90vh'}),

			],width=5,style={'backgroundColor' : colors['background'],'float': 'left','height':'100vh'}),

		])
	return layout1

def generate_html():
	path = "/Users/DBurke/Documents/Layerlab/generalized_pipeline/dash/saved_data/"
	children = []
	cities_requested = [] 
	children.append(dbc.Row([
						html.Div([
							html.H1('COvid-19'),
						],style={'backgroundColor' : colors['background'],'grid-row': '1','grid-column': '2'}),
						html.Div([
							html.Img(src='assets/covid19.png', height=50),
							html.Img(src='assets/cu.png', height=50),
							html.Img(src='assets/csu.jpg', height=50)
						], style={'backgroundColor' : colors['background'],'grid-row': '1','grid-column': '3'})
					],style={'backgroundColor' : colors['background'],'display': 'grid', 'grid-template-columns': 'auto auto auto'}),)
	height = 100/(len((os.listdir(path)))-1)
	height = str(height)+"vh"
	for file in os.listdir(path):

		if file != '.DS_Store':
			cities_requested.append(file)
			new = path + file
			graph = dbc.Col([
						dcc.Link(str(file), href='/' + str(file)),
						dbc.Row([
						dbc.Col( dcc.Graph(id='test', figure = build_pre_graphs(str(file)),
										   style={'backgroundColor' : colors['background'],'height':height})),
					],no_gutters=True)
					])
			children.append(graph)
	return children, cities_requested
	

url_bar_and_content_div = html.Div([
	dcc.Location(id='url', refresh=False),
	html.Div(id='page-content')
])
children, cities_requested = generate_html()
layout_index = html.Div(style = {'backgroundColor' : colors['background']},
	children = children)
'''layout_index = html.Div(style = {'backgroundColor' : colors['background']},
	children = [
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
		dcc.Link('Boulder', href='/Boulder'),
		dbc.Row( [
			dbc.Col( dcc.Graph(id='test', figure = build_pre_graphs('Boulder'),
							   style={'backgroundColor' : colors['background'],'height':'45vh'})),
		],no_gutters=True)
	]),
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
		dcc.Link('Chile', href='/Chile'),
		dbc.Row( [
			dbc.Col( dcc.Graph(id='test', figure = build_pre_graphs('Chile'),
							   style={'backgroundColor' : colors['background'],'height':'45vh'})),
		],no_gutters=True)
	])
])'''

app.layout = url_bar_and_content_div
app.title = 'COvid-19'


app.validation_layout = html.Div([
	url_bar_and_content_div,
	layout_index,
	layout(False, None)
])

@app.callback(Output('page-content', 'children'),
			  [Input('url', 'pathname')])

def display_page(pathname):
	print('URL changed', pathname[1:])
	if pathname[1:] in cities_requested:
		return layout(True, pathname)
	else:
		return layout_index



if __name__ == '__main__':
	app.run_server(debug=True)