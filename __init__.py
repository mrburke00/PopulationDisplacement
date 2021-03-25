import json
import os
import datetime
from datetime import timedelta
import warnings; warnings.simplefilter('ignore')
#from datetime import timedelta, date
#####COVID19#####

def daterange(date1, date2):
    for n in range(int ((date2 - date1).days)+1):
        yield date1 + timedelta(n)

#clean all files before proceeding

def clean_files(sit_rep_name):

	base_path = "/Users/DBurke/Documents/Layerlab/generalized_pipeline" #CHANGE PATH
	sit_rep_path = base_path+'/sitreps/'+sit_rep_name+'/'+'Boulder_hot_spot_shapes' +'/'
	location_data_path = base_path + "/dash/saved_data/"+sit_rep_name+'/'

	if os.path.isfile(location_data_path + 'dates_times.pickle'):
		os.remove(location_data_path + 'dates_times.pickle')

	if os.path.isfile(location_data_path + 'animation.pickle'):
		os.remove(location_data_path + 'animation.pickle')

	if os.path.isfile(location_data_path + 'trend_lines.pickle'):
		os.remove(location_data_path + 'trend_lines.pickle')

	if os.path.isfile(location_data_path+'json_geo.json'):
		os.remove(location_data_path+'json_geo.json')

	if os.path.isfile(location_data_path+'pre_graph_data.csv'):
		os.remove(location_data_path+'pre_graph_data.csv')

###end file cleaning


def main():


	cities_requested = []
	with open("init.json") as f:
		init_data = json.load(f)



	#cities_requested = init_data['cities'].replace(',',' ').split()



	path = init_data['path']


	config_file = open("snake_config.json",)
	config = json.load(config_file)

	for i in range(len(init_data['cities'])):

		city = init_data['cities'][i]['city']
		clean_files(city)
		start_dt = init_data['cities'][i]['start_date']
		end_dt = init_data['cities'][i]['end_date']

		sit_rep_name = config[city]['sit_rep_name']
		county_name = config[city]['county_name']
		city_name = config[city]['city_name']
		db = config[city]['db']
		cities = config[city]['cities']
		county_shapes = config[city]['county_shapes']
		county_shapes_name = config[city]['county_shapes_name']
		city_shapes = config[city]['city_shapes']
		city_shapes_name = config[city]['city_shapes_name']
		repo = config[city]['repo']

		min_lat = config[city]['min_lat']
		max_lat = config[city]['max_lat']
		min_lon = config[city]['min_lon']
		max_lon = config[city]['max_lon']

		os.system('bash snake_wrapper.sh "'+sit_rep_name+'" "'+county_name+'" "'+city_name+'" '+db+' '+county_shapes+' '+ \
			county_shapes_name+' '+city_shapes+' '+city_shapes_name+' '+ repo + ' "' + start_dt + '" "' + end_dt + '" ' + path + ' ' + min_lat + ' ' + \
			max_lat + ' ' + min_lon + ' ' +  max_lon)


'''
{
"cities":"Boulder",
"start_date" : "2020,11,1",
"end_date" : "2020,11,30",
"path" : "/Users/DBurke/Documents/Layerlab/generalized_pipeline/"
}

{
"cities":"Mozambique",
"start_date" : "2020,12,30",
"end_date" : "2021,1,1",
"path" : "/Users/DBurke/Documents/Layerlab/generalized_pipeline/"
}

{
"cities":"Lebanon",
"start_date" : "2020,5,25",
"end_date" : "2020,6,25",
"path" : "/Users/DBurke/Documents/Layerlab/generalized_pipeline/"
}1
'''
if __name__ == '__main__':
    main()