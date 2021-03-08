
from optparse import OptionParser
import warnings; warnings.simplefilter('ignore')
import math
import geopandas as gpd
import simplejson as json
import pandas as pd
import ast
import sqlite3
import fb
from geopandas.tools import sjoin
from sklearn.linear_model import LinearRegression
import numpy as np
import argparse
import csv
import collections
import os
import shutil
import datetime
from shapely.geometry import Polygon, Point
import pickle

parser = OptionParser()

parser.add_option("--db",
	dest="db",
	help="Path to database file")

parser.add_option("--shapefile",
	dest="shapefile",
	help="Path to shapefile")

parser.add_option("--shapename",
	dest="shapename",
	help="Shapefile column name")


parser.add_option("--beg_doI",
	dest="beg_doI",
	help="beginning date")

parser.add_option("--end_doI",
	dest="end_doI",
	help="end date")

parser.add_option("--base_path",
	dest="base_path",
	help="base_path")

parser.add_option("--sit_rep_name",
	dest="sit_rep_name",
	help="sit_rep_name")

parser.add_option("--min_lat",
	dest="min_lat",
	help="min_lat")

parser.add_option("--max_lat",
	dest="max_lat",
	help="max_lat")

parser.add_option("--min_lon",
	dest="min_lon",
	help="min_lon")

parser.add_option("--max_lon",
	dest="max_lon",
	help="max_lon")

(options, args) = parser.parse_args()
if not options.db:
		parser.error('DB file not given')


D = fb.get_db_fields(options.db, ['n_baseline','n_crisis'] )


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


def  make_lat_lon_tile(lat, lon, lat_d, lon_d):


	x_l = lon - lon_d
	x_r = lon + lon_d
	y_t = lat + lat_d
	y_b = lat - lat_d

	return Polygon( ((x_l, y_t), (x_r, y_t), (x_r,y_b), (x_l, y_b)) )

def get_windows(header, window):
	last_day = header[0].split(' ')[1]
	d = []
	d.append(Window(index=0,dayofweek=last_day))
	header_i = 0
	D = []

	for field in header:
		state,day,date,time = field.split(' ')

		if day != last_day:
					#d.append((header_i,last_day))

			d.append( Window(index=header_i, dayofweek=last_day))
			last_day = day
			if d[1][0] - d[0][0] == window:
				D.append(d)
				#d = [(header_i,day)]
			d = [Window(index=header_i, dayofweek=day)]
		header_i += 1


	W = []
	for i in range(len(D)- window + 1):
		curr = D[i:i+window] #points in the current window
		W.append((curr[0][0],curr[-1][1]))

	return W
def get_hot_spot_vals(D, pos, dates_times, field):
	count = 0
	vals = []
	for date,time in dates_times[9:]:
		if date in D[pos]:
			previous_3_days = get_previous_days(date,3)
			if previous_3_days[0] in D[pos] and previous_3_days[1] in D[pos] and previous_3_days[2] in D[pos]:
				if len(D[pos][previous_3_days[0]]) >= 2 and len(D[pos][previous_3_days[1]]) >= 2 and len(D[pos][previous_3_days[2]]) >= 2:   
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
					else:
						count = count  +1 
						fill[i] = {'n_baseline': 'NA', 'n_crisis': 'NA'}
				if fill not in vals:
					vals.append(fill)					
		else:
			return None, None

	return vals,dates

def get_basis_vals(D, pos, dates_times, field):
	vals  = []
	for date,time in dates_times:
		if date not in D[pos]:
			print("date not in: ", pos)
			print("date not in : ", date)
			return None
		if time not in D[pos][date]:
			print("time not in: ", pos)
			print("time not in : ", date)
			print("time not in : ", time)
			return None
		vals.append(float(D[pos][date][time][field]))
	return vals

#clean all files before proceeding
def clean_files():
	sit_rep_path = options.base_path+'sitreps/'+options.sit_rep_name+'/'+ options.sit_rep_name +'_hot_spot_shapes' +'/'
	location_data_path = options.base_path + "dash/location_data/"

	if (os.path.isfile(sit_rep_path + 'temp1.txt')):
		os.remove(sit_rep_path + 'temp1.txt')

	for j in range(0,len(dates_times)):
		today = dates_times[j][0]
		time = dates_times[j][1] 
		date = today + '_' + time

		if(os.path.exists(sit_rep_path + options.sit_rep_name + '_hot_spot_county_shapes_' + date) and os.path.isdir(sit_rep_path + options.sit_rep_name +'_hot_spot_county_shapes_' + date)):
			shutil.rmtree(sit_rep_path + options.sit_rep_name +'_hot_spot_county_shapes_' + date)

		if(os.path.isfile(sit_rep_path + options.sit_rep_name +'_hot_spot_county_shapes_' + date + '.zip')):
			os.remove(sit_rep_path + options.sit_rep_name +'_hot_spot_county_shapes_' + date + '.zip')

		if(os.path.isfile(sit_rep_path + options.sit_rep_name + '_hotspot_geojson_'+today+'.geojson')):
			os.remove(sit_rep_path + options.sit_rep_name + '_hotspot_geojson_'+today+'.geojson')
###end file cleaning

c = sqlite3.connect(options.db)
c.row_factory = dict_factory
C = {}

for row in c.execute('SELECT lat,lon,n_crisis FROM pop_tile WHERE n_crisis != "\\N"'):
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
model.fit(x,y)

D = get_db_fields(options.db, ['n_baseline', 'n_crisis'])

gdf = gpd.read_file(options.shapefile)

with open(options.base_path+'/dash/location_data/dates_times.pickle', 'rb') as handle:
	dates_times = pickle.load(handle)

clean_files()

sit_rep_path = options.base_path+'sitreps/'+options.sit_rep_name+'/'+ options.sit_rep_name +'_hot_spot_shapes' +'/'
location_data_path = options.base_path+ 'dash/location_data/'

file = sit_rep_path + 'temp1.txt'
f = open(file, "w")
header = ['shape','lat','lon']

for date,time in dates_times:
	header.append(' '.join(['crisis',
	fb.day_of_week(date),
	date,
	time]))
f.write('\t'.join(header))

vals = []
o = []

for pos in D:
	lat = float(pos[0])
	lon = float(pos[1])
	bounds = False

	if options.min_lat != 'NONE' or options.max_lat != 'NONE' or options.min_lon != 'NONE' or options.max_lon != 'NONE':
		if lat >= float(options.min_lat) and lat <= float(options.max_lat) and lon >= float(options.min_lon) and lon <= float(options.max_lon):
			bounds = True
	else:
		bounds = True

	if bounds:
		crisises, dates = get_crisis_vals(D,pos,dates_times,'n_crisis')
		if crisises is not None:
			crisis_f = []
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

			for x,y,z in zip(one,two,three):
				crisis_f.append(x)

				crisis_f.append(y)

				crisis_f.append(z)

				 
			df = pd.DataFrame()
			df['crisis'] = crisis_f

			df['crisis'] = df['crisis'].replace({'NA': None})
			missings = df[df['crisis'].isnull()].index.tolist() #index of missing values

			if len(missings) > 0:
				i = 0
				while len(missings) != 0:
					lower = missings[i] 
					upper = missings[i]
					low_gate = False
					up_gate = False
					if lower <= 0:
						j = lower+1
						while j in missings:
							j = j + 1                        
						df['crisis'].iloc[missings[i]] = float(df['crisis'].iloc[j])
						missings.pop(i)
						low_gate = True
						if len(missings) == 0: break

					if upper >= len(missings):
						j = upper-1
						while j in missings:
							j = j - 1
						df['crisis'].iloc[missings[i]] = float(df['crisis'].iloc[j])
						missings.pop(i)
						up_gate = True
						if len(missings) == 0: break

					if not low_gate and not up_gate:
						lower = lower - 1
						upper = upper + 1
						if lower not in missings and upper not in missings:
							avg = []
							avg.append(float(df['crisis'].iloc[lower]))
							avg.append(float(df['crisis'].iloc[upper]))
							df['crisis'].iloc[missings[i]] = np.mean(avg)
							missings.pop(i) 
					i = i + 1
					if i > len(missings)-1:
						i = 0
			crisis = []
			crisis = df['crisis'].to_numpy()
			crisis_avg = []

			shape = get_bounding_shape(lat, lon, gdf, "NAME") #pass from config file 

			if shape is not None:
				o.append([shape,lat,lon])
				vals.append(crisis)


f.close()

Window = collections.namedtuple('Window', 'index dayofweek')

shape_i = 0
crisis_range = {'start':0}
shapename = options.sit_rep_name
input_file = csv.reader(open(file), delimiter='\t')
header = None
crisis_header = None
shapename = None
L = []
B = []
C = []
row_i = 1
windows = None
for row,place in zip(vals, o):

	for line in input_file:
		if header is None:
			header = line
			crisis_header = line[crisis_range['start']:]
			continue 
	if shapename is None or place[shape_i] == shapename:
		L.append((float(place[1]),float(place[2]))) #split lat and lon into tuple 
		c = row[crisis_range['start']:] 
		c = [float(x) for x in c] #get every value for each coordinate position
		if len(c) >= 9: #this needs to be changed to ensure we have 1 value for each time point -> 3 time points a day
			C.append([float(x) for x in c])
		row_i += 1


# get distance between lat/lon and every other lon/lat
lats = {}
lons = {}
for lat,lon in L:
	if lat not in lats:
		lats[lat] = []
	if lon not in lons:
		lons[lon] = []
	lats[lat].append(float(lon))
	lons[lon].append(float(lat))


d = []
for lon in lons:
	s_lats = sorted(lons[lon])
	d_curr = []
	if len(s_lats) > 4:
		for i in range(1,len(s_lats)):
			d_curr.append(abs(s_lats[i-1] - s_lats[i]))
		d.append(min(d_curr))	

lat_u = np.mean(d)
lat_d = lat_u/2

d = []
for lat in lats:
	s_lons = sorted(lats[lat])
	d_curr = []
	if len(s_lons) > 4:

		for i in range(1,len(s_lons)):
			d_curr.append(abs(s_lons[i-1] - s_lons[i]))
		d.append(min(d_curr))

lon_u = np.mean(d)
lon_d = lon_u/2

k = 0
for j in range(0,len(dates_times)):
	k = k + 1
	geometry =  []
	data = []
	coordinates = []

	date = dates_times[j][0]
	time = dates_times[j][1]

	for i in range(len(C)):
		z = C[i][j]
		lat = L[i][0]
		lon = L[i][1]
		coord_temp = str(lat) + ', ' + str(lon)
		data.append([z])
		coordinates.append(str(lat) + ', ' + str(lon))
		tile = make_lat_lon_tile(float(lat), float(lon), lat_d, lon_d)
		geometry.append(tile)
	df = pd.DataFrame(data, columns = ['z'])
	df['coordinates'] = coordinates
	crs = {'init': 'epsg:4326'}
	gdf = gpd.GeoDataFrame(df, crs=crs, geometry=geometry)
	outfile = sit_rep_path + options.sit_rep_name+'_hot_spot_county_shapes_' + date + '_' + time
	os.mkdir(outfile)
	gdf.to_file(driver='ESRI Shapefile', filename=outfile)
	shutil.make_archive(outfile, 'zip', outfile)



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


df_temp = pd.DataFrame()
df_geo = pd.DataFrame()
df_dict = {}
today_index = 0
for j in range(0,len(dates_times)):
	today = dates_times[j][0]
	time = dates_times[j][1] 
	df = pd.DataFrame()

	hot_spot_county_shape = sit_rep_path + options.sit_rep_name+'_hot_spot_county_shapes_' + today + '_' + time + '/'

	hot_spot_county_geojson = sit_rep_path + options.sit_rep_name+ '_hotspot_geojson_' + today + '.geojson'
	
	geodf = gpd.read_file(hot_spot_county_shape + options.sit_rep_name + "_hot_spot_county_shapes_" + today + '_' + time + ".shp")
	geodf.to_file(hot_spot_county_geojson, driver = "GeoJSON")
	j_file = geodf.to_json()
	j_file = ast.literal_eval(j_file)

	coordinates = []
	z_score = []
	new_jfile = {}
	og_coords = []
	new_jfile['type'] = j_file['type']
	new_jfile['features'] = []

	for i in range(len(j_file['features'])):
		new_jfile['features'].append(j_file['features'][i])
		og_coords.append(j_file['features'][i]['properties']['coordinate'])
		coordinates.append(j_file['features'][i]['geometry']['coordinates'])
		z_score.append(j_file['features'][i]['properties']['z'])
		
	
	df['coordinates'] = coordinates
	df['z_score'] = z_score
	df['og_coords'] = og_coords
	
	new_jfile['features'][0].keys()
	if today_index == len(dates_times) - 1:
		save_jfile = new_jfile
	today_index = today_index + 1 
	for k in range(len(new_jfile['features'])):
		new_jfile['features'][k]['id'] = k
	ids=[]
	new_jfile['features'][0].keys()
	for k in range(len(new_jfile['features'])):
		ids.append(new_jfile['features'][k]['id'])
	df['ids'] = ids
	df_dict[today+'_'+time] = df

with open(options.base_path+'dash/location_data/json_geo.json', 'w') as outfile:
	json.dump(save_jfile, outfile)

df_dict_final = {}
today = dates_times[j][0]
time = dates_times[j][1]
today_index = today+'_'+time
df = df_dict[today_index]
og_coordinates = df['og_coords']
coordinates = df['coordinates']
ids = df['ids']
df_new = pd.DataFrame()
df_new['positions'] = og_coordinates
df_new['ids'] = ids
df_new['polygons'] = coordinates
for j in range(0,len(dates_times)):
	today = dates_times[j][0]
	time = dates_times[j][1]
	today_index = today+'_'+time
	df = df_dict[today_index]
	df_new['z_score_'+today_index] = df['z_score']
df_geo = df_new

with open(options.base_path+'dash/location_data/animation.pickle', 'wb') as handle:
	pickle.dump(df_geo, handle, protocol=pickle.HIGHEST_PROTOCOL)

clean_files()

