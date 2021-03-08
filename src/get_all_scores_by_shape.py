import sqlite3
import sys
import numpy as np
from optparse import OptionParser
import datetime
from sklearn.linear_model import LinearRegression
import warnings; warnings.simplefilter('ignore')
import math


import geopandas as gpd
import fb

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

parser.add_option("--doI",
                  dest="doI",
                  help="date of date_of_interest")

(options, args) = parser.parse_args()
if not options.db:
    parser.error('DB file not given')

D = fb.get_db_fields(options.db, ['n_baseline','n_crisis'] )

dates_times = {}
for pos in D:
    for date in D[pos]:
        for time in D[pos][date]:
            if (date,time) not in dates_times:
                dates_times[(date,time)] = 1

dates_times = sorted(dates_times.keys())
if options.doI:
    new_dates_times = {}
    for date, time in dates_times:
        obj = datetime.datetime.strptime(options.doI, '%Y%m%d')
        temp = datetime.datetime.strptime(date, '%Y-%m-%d')
        if temp < obj:
            new_dates_times[(date,time)] = 1
    new_dates_times = sorted(new_dates_times.keys())
    dates_times = new_dates_times



def get_previous_days(today, number_of_days, include_today=True):
    date_time_obj = datetime.datetime.strptime(today, '%Y-%m-%d')
    previous_3_days = []
    if include_today:
        previous_3_days.append(today)
    for i in range(1,number_of_days):
        new_date = date_time_obj - datetime.timedelta(days=i)
        new_date_string = new_date.strftime("%Y-%m-%d")
        previous_3_days.append(new_date_string)
    return previous_3_days

def get_vals(D, pos, dates_times, field):
    vals = []
    for date,time in dates_times:
        if date in D[pos]:
            date_time_obj = datetime.datetime.strptime(date, '%Y-%m-%d')
            previous_3_days = []
            for i in range(1,4):
                new_date = date_time_obj - datetime.timedelta(days=i)
                new_date_string = new_date.strftime("%Y-%m-%d")
                previous_3_days.append(new_date_string)
            if previous_3_days[0] in D[pos] and previous_3_days[1] in D[pos] and previous_3_days[2] in D[pos]:
                if time in D[pos][date]:
                    #print("pos added: ", pos)
                    #print("date added: ", date)
                    #print("time added: ", time)
                    vals.append(float(D[pos][date][time][field]))
    if not vals or len(vals) < 10:
        return None
    #print(vals)
    #print('added')
    return vals
def get_crisis_vals(D, pos, dates_times, field):
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
                    #print(pos)
                    #print(previous_3_days[0])
                    #print(D[pos][previous_3_days[0]])
                    #print(previous_3_days[1])
                    #print(D[pos][previous_3_days[1]])
                    #print(previous_3_days[2])
                    #print(D[pos][previous_3_days[2]])
                    #print(len(D[pos][previous_3_days[0]]) + len(D[pos][previous_3_days[1]]) + len(D[pos][previous_3_days[2]]))
                    return None
            else:
                continue
                
        else:
            return None
    return vals

def get_basis_vals(D, pos, dates_times, field):
    vals  = []
    for date,time in dates_times:
        #print(date,time)
        if date not in D[pos]:
            return None
        if time not in D[pos][date]:

            return None
        #print("exists : ", pos)
        #print("exists : ", date)
        vals.append(float(D[pos][date][time][field]))
    return vals

header = ['shape','lat','lon']
for date,time in dates_times[:21]:
    header.append(' '.join(['baseline',
                            fb.day_of_week(date),
                            time]))
for date,time in dates_times:
    header.append(' '.join(['crisis',
                            fb.day_of_week(date),
                            date,
                            time]))

print('\t'.join(header))


gdf = gpd.read_file(options.shapefile)

for pos in D:
    lat = float(pos[0])
    lon = float(pos[1])

    crisis = get_crisis_vals(D,pos,dates_times,'n_crisis')
    baseline = get_crisis_vals(D,pos,dates_times,'n_baseline') #DO I USE SAME FOR BASELINE?

    if crisis is not None and baseline is not None:
        shape = fb.get_bounding_shape(lat, lon, gdf, "NAME")
        if shape is not None:
            o = [shape,lat,lon] + baseline[:21]  + crisis
            print('\t'.join([str(x) for x in o]))


'''
    if crisis is None and baseline is None:
        crisis = list(repeat(0.001,285))
        baseline = list(repeat(0.001,21))
    shape = fb.get_bounding_shape(lat, lon, gdf, options.shapename)
    #print('prelims complete')
    if shape is not None:
        #print("crisis: ", crisis)
        #print("baseline: ", baseline[:21])
        #print(shape, lat, lon)
        o = [shape,lat,lon] + baseline[:21]  + crisis
        print('\t'.join([str(x) for x in o]))
'''

