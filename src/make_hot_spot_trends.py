import fiona
import dash
import geopandas as gpd
import simplejson as json
import plotly.express as px
import pandas as pd
import plotly.graph_objects as go
import ast
import numpy as np
import sqlite3
import fb
import datetime
import sys
from geopandas.tools import sjoin
import warnings; warnings.simplefilter('ignore')
from sklearn.linear_model import LinearRegression
import  sys
import numpy as np
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import seasonal_decompose
import argparse
import csv
import collections
from sklearn.linear_model import LinearRegression
import geopandas as gpd
import pandas as pd
import os
import shutil
import plotly.graph_objects as go
from shapely.geometry import Polygon, Point



#base_path = "/Users/DBurke/Documents/Layerlab/COvid19" #parameter
#sit_rep_path = base_path+'/sitreps/'+'Boulder'+'/'+today +'/' #parameter
db_path = '/Users/DBurke/Documents/Layerlab/COvid19/dbs/boulder.db' #parameter
beg_doI = '20200701' #parameter
end_doI = '20201027' #paramter



def get_bounding_shape(lat, lon, gdf, name):
	h=pd.DataFrame({'Lat':[lat], 'Lon':[lon]})
	geometry = [Point(xy) for xy in zip([lon], [lat])]
	hg = gpd.GeoDataFrame(h, geometry=geometry)
	hg.crs = {'init' :'epsg:4326'}
	hg_1 = hg.to_crs(gdf.crs)
	r = sjoin(gdf,hg_1)
	if r.empty:
		return None
	else:
		return r[name].tolist()[0]
	
def utc_to_local(utc_dt):
	return utc_dt.replace(tzinfo=datetime.timezone.utc).astimezone(tz=None)

def switch_tz(date, time):
	year, month, day = date.split('-')
	hour = time[:2]
	minute = time[2:]

	utc = datetime.datetime( int(year), int(month), int(day), int(hour), int(minute) )
	mnt = utc_to_local(utc)
	return ('-'.join([mnt.strftime('%Y'), mnt.strftime('%m'), mnt.strftime('%d')]) , \
			mnt.strftime('%H') + mnt.strftime('%M'))

def dict_factory(cursor, row):
	d = {}
	for idx, col in enumerate(cursor.description):
		d[col[0]] = row[idx]
	return d

def get_db_fields(db_path, fields, local_tz=True):
	c = sqlite3.connect(db_path)
	c.row_factory = dict_factory

	D = {}
	dates = []

	#for row in c.execute('SELECT * FROM pop_tile'):
	for row in c.execute('SELECT * FROM pop_tile WHERE n_crisis != "\\N"'):
		lat = row['lat']
		lon = row['lon']
		if (lat,lon) not  in D:
			D[(lat,lon)] = {}

		date, time = row['date_time'].split()

		#if local_tz:
			#date, time = switch_tz(date,time)

		if date not in dates:
			dates.append(date)

		if date not in D[(lat,lon)]:
			D[(lat,lon)][date] = {}

		d = {}
		for field in fields:
			d[field] = row[field]

		D[(lat,lon)][date][time] = d
	return D

def day_of_week(date):
	year,month,day = date.split('-')
	ans = datetime.date(int(year), int(month), int(day))
	day_of_week = ans.strftime("%A")
	return day_of_week


c = sqlite3.connect(db_path)
c.row_factory = dict_factory
C = {}

'''for row in c.execute('SELECT lat,lon,n_crisis FROM pop_tile WHERE n_crisis != "\\N"'):
	lat = row['lat']
	lon = row['lon']
	if (lat,lon) not  in C:
		C[(lat,lon)] = []
	C[(lat,lon)].append(float(row['n_crisis']))
C_stats = []
for c in C:
	C_stats.append( ( np.mean(C[c]), np.std(C[c]) ) )
model = LinearRegression()
x=[[c[0]] for c in C_stats]
y=[[c[1]] for c in C_stats]
model.fit(x,y)'''



def get_hot_spot_vals(D, pos, dates_times, field):
	count = 0
	vals = []
	for date,time in dates_times[9:]:
		if date in D[pos]:
			previous_3_days = get_previous_days(date,3)
			if previous_3_days[0] in D[pos] and previous_3_days[1] in D[pos] and previous_3_days[2] in D[pos]:
				if len(D[pos][previous_3_days[0]]) >= 2 and len(D[pos][previous_3_days[1]]) >= 2 and len(D[pos][previous_3_days[2]]) >= 2:   
					#count = count + 1
					times = D[pos][previous_3_days[0]].keys()
					for x in times:
						vals.append(float(D[pos][date][x][field]))
				else:

					return None
			else:
				continue
				
		else:
			return None
	return vals

def get_crisis_vals(D, pos, dates_times, field):
	count = 0
	vals = []
	dates = []
	for date,time in dates_times:
		if date in D[pos]:
			if date not in dates:
				dates.append(date)
			if len(D[pos][date]) >= 3:
				if D[pos][date] not in vals:
					vals.append(D[pos][date])
			else:
				fill = {}
				count = 0
				for i in ['0000','0800','1600']:
					if i in D[pos][date]:
						x = {i: D[pos][date][i]}
						fill[i] = D[pos][date][i]
						#vals.append(x)
					else:
						#x = {i: {'n_baseline': 'NA', 'n_crisis': 'NA'}}
						count = count  +1 
						fill[i] = {'n_baseline': 'NA', 'n_crisis': 'NA'}
						#print("+",x)
						#vals.append(x)
				if fill not in vals:
					vals.append(fill)


				
		else:
			return None, None

	return vals,dates

D = get_db_fields(db_path, ['n_baseline', 'n_crisis'])
gdf = gpd.read_file("/Users/DBurke/Documents/Layerlab/COvid19/facebook/shapefiles/co_counties") #PARAMETER?

def get_crisis_df():
	dates_times = {}
	for pos in D:
		for date in D[pos]:
			for time in D[pos][date]:
				if (date,time) not in dates_times:
					dates_times[(date,time)] = 1

	dates_times = sorted(dates_times.keys())
	if beg_doI and end_doI:
		new_dates_times = {}
		for date, time in dates_times:
			beg_obj = datetime.datetime.strptime(beg_doI, '%Y%m%d')
			end_obj = datetime.datetime.strptime(end_doI, '%Y%m%d')
			temp = datetime.datetime.strptime(date, '%Y-%m-%d')
			if temp >= beg_obj and temp <= end_obj:
				new_dates_times[(date,time)] = 1
		new_dates_times = sorted(new_dates_times.keys())
		dates_times = new_dates_times



	df_dict = {}

	for pos in D:

		lat = float(pos[0])
		lon = float(pos[1])
		#Campus/Hill/Other
		if lat >= 39.95 and lat <= 40.086 and lon >= -105.305 and lon <= -105.205: #boulder cut off 
			#crisis = get_hot_spot_vals(D,pos,dates_times,'n_crisis')
			#baseline = get_hot_spot_vals(D,pos,dates_times,'n_baseline') #DO I USE SAME FOR BASELINE?
			crisises, dates = get_crisis_vals(D, pos, dates_times, 'n_crisis')
			if crisises is not None:
				one = []
				two = []
				three = []
				for crisis in crisises:
					if crisis['0000']['n_crisis'] != 'NA':
						one.append(crisis['0000']['n_crisis'])
					else:
						one.append('NA')
						
					if crisis['0800']['n_crisis'] != 'NA':
						two.append(crisis['0800']['n_crisis'])
					else:
						two.append('NA')
					
					if crisis['1600']['n_crisis'] != 'NA':
						three.append(crisis['1600']['n_crisis'])
					else:
						three.append('NA')
							
				df = pd.DataFrame()
				df['dates'] = dates
				
				df['0000'] = one
				df['0000'] = df['0000'].replace({'NA': None})
				missings = df[df['0000'].isnull()].index.tolist()
				if len(missings) > 50:
					df['0000'].drop
					continue
				else:
					if len(missings) > 0:
						for i in range(len(missings)):
							lower = missings[i]
							upper = missings[i]
							while upper in missings:
								upper = upper + 1
							while lower in missings:
								lower = lower - 1
								if lower == 0:
									lower = upper
								break
							if upper >= len(one):
								upper = lower
							avg = []
							avg.append(float(df['0000'].iloc[lower]))
							avg.append(float(df['0000'].iloc[upper]))
							df['0000'].iloc[missings[i]] = np.mean(avg)
							
				df['0800'] = two
				df['0800'] = df['0800'].replace({'NA': None})
				missings = df[df['0800'].isnull()].index.tolist()
				if len(missings) > 50:
					df['0800'].drop
					continue
				else:
					if len(missings) > 0:
						for i in range(len(missings)):
							lower = missings[i]
							upper = missings[i]
							while upper in missings:
								upper = upper + 1
							while lower in missings:
								lower = lower - 1
								if lower == 0:
									lower = upper
								break
							if upper >= len(one):
								upper = lower
							avg = []
							avg.append(float(df['0800'].iloc[lower]))
							avg.append(float(df['0800'].iloc[upper]))
							df['0800'].iloc[missings[i]] = np.mean(avg)   

				df['1600'] = three
				df['1600'] = df['1600'].replace({'NA': None})
				missings = df[df['1600'].isnull()].index.tolist()
				if len(missings) > 50:
					df['1600'].drop
					continue
				else:
					if len(missings) > 0:
						for i in range(len(missings)):
							lower = missings[i]
							upper = missings[i]
							while upper in missings:
								upper = upper + 1
							while lower in missings:
								lower = lower - 1
								if lower == 0:
									lower = upper
								break
							if upper >= len(one):
								upper = lower
							avg = []
							avg.append(float(df['1600'].iloc[lower]))
							avg.append(float(df['1600'].iloc[upper]))
							df['0800'].iloc[missings[i]] = np.mean(avg)   
			else:
				continue		
			df_dict[pos] = df 


	return df_dict
#df.to_csv('/Users/DBurke/Documents/Layerlab/COvid19/dash/test.csv')


'''import csv
import pandas as pd 

def saver(dictex):
	for key, val in dictex.items():
		val.to_csv("Users/DBurke/Documents/Layerlab/COvid19/dash/data_{}.csv".format(str(key)))

	with open("keys.txt", "w") as f: #saving keys to file
		f.write(str(list(dictex.keys())))

saver(df_dict)'''



