import numpy as np
import pickle
import pandas as pd
import csv
from optparse import OptionParser
import argparse
import json

parser = OptionParser()

parser.add_option("--base_path",
	dest="base_path",
	help="base_path")

parser.add_option("--sit_rep_name",
	dest="sit_rep_name",
	help="sit_rep_name")

(options, args) = parser.parse_args()

with open(options.base_path + '/dash/saved_data/' +options.sit_rep_name+'/animation.pickle', 'rb') as handle:  
	df_geo = pickle.load(handle)

with open(options.base_path + '/dash/saved_data/' +options.sit_rep_name+'/dates_times.pickle', 'rb') as handle:
	dates_times = pickle.load(handle)

with open(options.base_path + '/dash/saved_data/' +options.sit_rep_name+'/json_geo.json') as data_file:
	new_jfile = json.load(data_file)

with open(options.base_path + '/dash/saved_data/' +options.sit_rep_name+'/trend_lines.pickle', 'rb') as handle:
	df_dict = pickle.load(handle)

trends = {}
dates = []
for i in range(0,len(dates_times),3):
	date = dates_times[i][0]
	dates.append(date)
	vals = []
	for key in df_dict.keys():
		df = df_dict[key]
		vals.extend((df.loc[df['dates'] == date].values[0][1:4].astype(float)))
	#print(vals)
	q_25 = np.percentile(vals, 25)
	q_50 = np.percentile(vals, 50)
	q_75 = np.percentile(vals, 75)
	trends[date] = (q_25, q_50, q_75)
trends_lower = []
trends_upper = []
trends_median = []
for i in range(0,len(dates_times),3):
	date = dates_times[i][0]
	lower_count = 0
	upper_count = 0
	median_count = 0
	for key in df_dict.keys():
		df = df_dict[key]
		vals = ((df.loc[df['dates'] == date].values[0][1:4].astype(float)))
		if (np.percentile(vals, 25)) <= trends[date][0]:
			lower_count = lower_count + 1
		elif ((np.percentile(vals, 75)) >= trends[date][2]):
			upper_count = upper_count + 1
		else:
			median_count = median_count + 1
	trends_lower.append(lower_count)
	trends_upper.append(upper_count)
	trends_median.append(median_count)

with open(options.base_path + '/dash/saved_data/' + options.sit_rep_name +'/pre_graph_data.csv', 'w') as out_file:
	write = csv.writer(out_file)
	write.writerow(trends_lower)
	write.writerow(trends_upper)
	write.writerow(trends_median)
	write.writerow(dates)

