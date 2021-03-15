import pandas as pd
import numpy as np
import sqlite3
import argparse
import collections
from sklearn.linear_model import LinearRegression
from optparse import OptionParser
import pickle
import warnings; warnings.simplefilter('ignore')

parser = OptionParser()

parser.add_option("--db",
	dest="db",
	help="Path to database file")

parser.add_option("--base_path",
	dest="base_path",
	help="base_path")

parser.add_option("--beg_doI",
	dest="beg_doI",
	help="beginning date")

parser.add_option("--end_doI",
	dest="end_doI",
	help="end date")

parser.add_option("--sit_rep_name",
	dest="sit_rep_name",
	help="sit_rep_name")

parser.add_option("--shapefile",
	dest="shapefile",
	help="Path to shapefile")

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

sit_rep_path = options.base_path+'sitreps/'+options.sit_rep_name+'/'+ options.sit_rep_name +'_density_trends' +'/'

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

with open(options.base_path+'/dash/location_data/dates_times.pickle', 'rb') as handle:
	dates_times = pickle.load(handle)

with open(options.base_path+'/dash/location_data/animation.pickle', 'rb') as handle:
    b = pickle.load(handle)

df_dict_animation = b
df_dict = {}

for pos in D:
	lat = float(pos[0])
	lon = float(pos[1])
	position = pos[0] + ', ' + pos[1]
	bounds = False
	
	if options.min_lat != 'NONE' or options.max_lat != 'NONE' or options.min_lon != 'NONE' or options.max_lon != 'NONE':
		if lat >= float(options.min_lat) and lat <= float(options.max_lat) and lon >= float(options.min_lon) and lon <= float(options.max_lon):
			bounds = True
	else:
		bounds = True

	if bounds:
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
			if len(missings) > 7:
				df['0000'].drop
				continue
			else:
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
							df['0000'].iloc[missings[i]] = float(df['0000'].iloc[j])
							missings.pop(i)
							if len(missings) == 0:
								break
							low_gate = True

						if upper >= len(missings):
							j = upper-1
							while j in missings:
								j = j - 1
							df['0000'].iloc[missings[i]] = float(df['0000'].iloc[j])
							missings.pop(i)
							if len(missings) == 0:
								break
							up_gate = True

						if not low_gate and not up_gate:
							lower = lower - 1
							upper = upper + 1
							if lower not in missings and upper not in missings:
								avg = []
								avg.append(float(df['0000'].iloc[lower]))
								avg.append(float(df['0000'].iloc[upper]))
								df['0000'].iloc[missings[i]] = np.mean(avg)
								missings.pop(i)
								if len(missings) == 0:
									break
						i = i + 1
						if i > len(missings)-1:
							i = 0
							
			df['0800'] = two
			df['0800'] = df['0800'].replace({'NA': None})
			missings = df[df['0800'].isnull()].index.tolist()
			if len(missings) > 7:
				df['0800'].drop
				continue
			else:
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
							df['0800'].iloc[missings[i]] = float(df['0800'].iloc[j])
							missings.pop(i)
							if len(missings) == 0:
								break
							low_gate = True

						if upper >= len(missings):
							j = upper-1
							while j in missings:
								j = j - 1
							df['0800'].iloc[missings[i]] = float(df['0800'].iloc[j])
							missings.pop(i)
							if len(missings) == 0:
								break
							up_gate = True

						if not low_gate and not up_gate:
							lower = lower - 1
							upper = upper + 1
							if lower not in missings and upper not in missings:
								avg = []
								avg.append(float(df['0800'].iloc[lower]))
								avg.append(float(df['0800'].iloc[upper]))
								df['0800'].iloc[missings[i]] = np.mean(avg)
								missings.pop(i)
								if len(missings) == 0:
									break
						i = i + 1
						if i > len(missings)-1:
							i = 0
			df['1600'] = three
			df['1600'] = df['1600'].replace({'NA': None})
			missings = df[df['1600'].isnull()].index.tolist()
			if len(missings) > 7:
				df['1600'].drop
				continue
			else:
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
							df['1600'].iloc[missings[i]] = float(df['1600'].iloc[j])
							missings.pop(i)
							if len(missings) == 0:
								break
							low_gate = True

						if upper >= len(missings):
							j = upper-1
							while j in missings:
								j = j - 1
							df['1600'].iloc[missings[i]] = float(df['1600'].iloc[j])
							missings.pop(i)
							if len(missings) == 0:
								break
							up_gate = True

						if not low_gate and not up_gate:
							lower = lower - 1
							upper = upper + 1
							if lower not in missings and upper not in missings:
								avg = []
								avg.append(float(df['1600'].iloc[lower]))
								avg.append(float(df['1600'].iloc[upper]))
								df['1600'].iloc[missings[i]] = np.mean(avg)
								missings.pop(i)
								if len(missings) == 0:
									break
						i = i + 1
						if i > len(missings)-1:
							i = 0
		else:
			continue
		coordinates = df_dict_animation.loc[df_dict_animation['polygons'] == position]
		df['coordinates'] = coordinates['polygons']
		df_dict[position] = df

with open(options.base_path+'/dash/location_data/trend_lines.pickle', 'wb') as handle:
	pickle.dump(df_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)





