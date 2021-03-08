import datetime
import glob
import os
import warnings; warnings.simplefilter('ignore')
from datetime import timedelta

sit_rep_name = config['sit_rep_name']
county_name = config['county_name']
city_name = config['city_name']
db = config['db']
county_shapes = config['county_shapes']
county_shapes_name = config['county_shapes_name']
city_shapes = config['city_shapes']
city_shapes_name = config['city_shapes_name']
repo = config['repo']
start_dt = config['start_date']
end_dt = config['end_date']
path = config['path']

min_lat = config['min_lat']
max_lat = config['max_lat']
min_lon = config['min_lon']
max_lon = config['max_lon']

print(db)

def time_stamp(fmt='%Y%m%d'):
    return datetime.datetime.now().strftime(fmt)

def daterange(date1, date2):
    for n in range(int ((date2 - date1).days)+1):
        yield date1 + timedelta(n)


base_path = path
sit_rep_path = base_path+'sitreps/'+sit_rep_name+'/'
location_data_path = base_path + "dash/location_data/"
src = base_path+'src'
hot_spot_shapes = sit_rep_path + sit_rep_name + '_hot_spot_shapes/'
density_trends = sit_rep_path + sit_rep_name + '_density_trends/'


list_of_tiles = glob.glob(repo + '*csv')
latest_tile = max(list_of_tiles, key=os.path.getctime)

rule all:
	input:
		db,
		location_data_path+'animation.pickle',
		location_data_path+'json_geo.json',
		location_data_path+'trend_lines.pickle',
		location_data_path+'dates_times.pickle'
		
rule db:
	input:
		latest_tile
	output:
		db
	shell:
		"bash snake_src/db.sh {src} {db} {repo}"

rule dates_times:
	input:
		db
	output:
		location_data_path+'dates_times.pickle'
	shell:
		'mkdir -p ' + hot_spot_shapes + ';' + \
		 'python {src}/make_dates_times.py \
		     --db {db} \
		    --beg_doI "{start_dt}" \
    		--end_doI "{end_dt}" \
    		--sit_rep_name {sit_rep_name}\
    		--base_path {base_path}'

rule hot_spot_shapes:
	input:
		db,
		location_data_path+'dates_times.pickle'
	output:
		location_data_path+'animation.pickle',
		location_data_path+'json_geo.json'
	shell:
		'mkdir -p ' + hot_spot_shapes + ';' + \
		 'python {src}/make_hot_spot_shapes.py \
    		--db {db} \
    		--shapefile {county_shapes} \
    		--shapename {county_shapes_name} \
    		--beg_doI "{start_dt}" \
    		--end_doI "{end_dt}" \
    		--sit_rep_name {sit_rep_name}\
    		--base_path {base_path}\
    		--min_lat {min_lat}\
    		--max_lat {max_lat}\
    		--min_lon {min_lon}\
    		--max_lon {max_lon}'

rule density_trends:
	input:
		db,
		location_data_path+'dates_times.pickle',
		location_data_path+'animation.pickle',
		location_data_path+'json_geo.json'
	output:
		location_data_path+'trend_lines.pickle'
	shell:
		'mkdir -p ' + density_trends + ';' + \
		 'python {src}/make_density_trends.py \
    		--db {db} \
    		--shapefile {county_shapes} \
    		--beg_doI "{start_dt}" \
    		--end_doI "{end_dt}" \
    		--sit_rep_name {sit_rep_name}\
    		--base_path {base_path}\
    		--min_lat {min_lat}\
    		--max_lat {max_lat}\
    		--min_lon {min_lon}\
    		--max_lon {max_lon}'


