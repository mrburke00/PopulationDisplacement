import pickle
import datetime 
from datetime import timedelta
from optparse import OptionParser
import fb

parser = OptionParser()


parser.add_option("--db",
	dest="db",
	help="Path to database file")

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

(options, args) = parser.parse_args()

D = fb.get_db_fields(options.db, ['n_baseline','n_crisis'] )

dates_times = {}
for pos in D:
	for date in D[pos]:
		for time in D[pos][date]:
			if (date,time) not in dates_times:
				 dates_times[(date,time)] = 1

dates_times = sorted(dates_times.keys())

if options.beg_doI and options.end_doI:
	''''''
	start_t = options.beg_doI.replace(' ', '-')
	end_t = options.end_doI.replace(' ', '-')
	new_dates_times = {}
	for date, time in dates_times:
			beg_obj = datetime.datetime.strptime(start_t, '%Y-%m-%d')
			end_obj = datetime.datetime.strptime(end_t, '%Y-%m-%d')
			temp = datetime.datetime.strptime(date, '%Y-%m-%d')
			if temp >= beg_obj and temp <= end_obj:
				new_dates_times[(date,time)] = 1
	new_dates_times = sorted(new_dates_times.keys())
	dates_times = new_dates_times

with open(options.base_path+'/dash/location_data/dates_times.pickle', 'wb') as handle:
	pickle.dump(dates_times, handle, protocol=pickle.HIGHEST_PROTOCOL)