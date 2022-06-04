import os
import glob
import argparse
import numpy as np
import pandas as pd
import datetime

### CONFIG ###

INITIAL_DATE_STR = '26-02-2020'
PATCH_DATE_STR   = '14-03-2022' # the day after the data from DSSG stopped flowing
PATCH_DATE_STR_D = '2022-03-14' # the DSG files use a different format

HOSP_PATCH_DATE_STR = '15-03-2022' # the first weekly hospitalizations record from the DSSG file

INITIAL_DATE = datetime.datetime.strptime(INITIAL_DATE_STR,'%d-%m-%Y').date()
PATCH_DATE   = datetime.datetime.strptime(PATCH_DATE_STR,'%d-%m-%Y').date()

# this is a very complete file from the awesome DSSG-PT group, we saved the last complete version
# to inspect only the new cases and deaths we can use
# csvtool -t ',' col 1,12,14,15,16 data-2022-03-13.csv | csvtool -t ',' readable

# despite the name, this file has the last data at 2022-03-13
DSSG_FILE = 'data-2022-03-20.csv'

DGS_SUBDIR = 'dgs/'
DSSG_LATEST_SUBDIR = 'dssg/'
MERGED_DATA_SUBDIR = 'merged/'


### FUNCTIONS ###

def mk_dates ( initial_date, days ):

    dates = []

    cur_date   = initial_date
    final_date = initial_date + datetime.timedelta(days=days)

    while cur_date < final_date:
        dates.append(cur_date.strftime('%d-%m-%Y'))
        cur_date = cur_date + datetime.timedelta(days=1)

    # the current date is formatted backwards, for the file name
    return dates, cur_date.strftime('%Y-%m-%d')

def print_summary ( df ):
    print( df[ ['data', 'confirmados_novos', 'obitos'] ] )

### MAIN ###

parser = argparse.ArgumentParser(description='Download DSSG files')
parser.add_argument('path', type=str, help='path to where files will be stored')
args = parser.parse_args()
path_args = args.path

if os.path.exists(path_args) is not True:
   print ("There is no folder called", path_args)
   exit(1)
else:
   print ("Folder:" + path_args)

if os.access(path_args, os.W_OK) is not True:
            print("Folder is not writable")
            exit(1)
else :
            print("Folder is writable")

# read both files

base_path = path_args + '/'
dssg_path = base_path + DSSG_FILE
dssg_data = pd.read_csv(dssg_path)

# this is the minimalistic DSG file that started being published around 13-03-2022
# when the dashboard was discontinued (except for the 'amostras' part )

# columns of the DGS file
#
# * confirmation_date1 - date
# * day_cum_abs_num     - daily cases
# * day_ob_abs_num      - daily deaths

dgs_dir = base_path + DGS_SUBDIR

# find the latest available file
dgs_file_list = glob.glob(dgs_dir + 'covid_dados-*.xlsx')
dgs_path  = max(dgs_file_list, key=os.path.getctime)

print('\nMerging', dssg_path, 'with', dgs_path, '\n')

dgs_data  = pd.read_excel(dgs_path, sheet_name=1) # second tab

# we now wish to patch the DSSG file using the data from the DGS file starting at PATCH_DATE

index = dgs_data.loc[ dgs_data['confirmation_date1'] == PATCH_DATE_STR_D ].index[0]

dgs_data_tail = dgs_data.loc[index:]

# now lets obtain the necessary values

cases  = dgs_data_tail['day_cum_abs_num']
deaths = dgs_data_tail['day_ob_abs_num' ]
ndays  = len(cases.index)

dates, last_date  = mk_dates(PATCH_DATE, ndays)

# the deaths need to be cumulative, and the last value from DSSG needs to be added

cum_deaths = np.cumsum(deaths) + dssg_data.iloc[-1]['obitos']

# let's create a dataframe with the DSSG naming, the remaining columns are filled with NaN

extra_dssg_data = pd.DataFrame( {'data':dates, 'confirmados_novos':cases.to_list(), 'obitos':cum_deaths.astype(int).to_list() } )

# and finally let's merge the dataframes

merged_dssg_data = dssg_data.append(extra_dssg_data, ignore_index = True, sort = False)

print_summary(merged_dssg_data)

# now let's look for the latest dssg file to extract the hospitalizations data

dssg_file_list = glob.glob(base_path + DSSG_LATEST_SUBDIR + 'data-*.csv')
dssg_latest_path = max(dssg_file_list, key=os.path.getctime)

dssg_latest_data = pd.read_csv(dssg_latest_path)

index = dssg_latest_data.loc[ dssg_latest_data['data'] == HOSP_PATCH_DATE_STR ].index[0]

dssg_latest_data_tail = dssg_latest_data.loc[index:]

# let's fetch the weekly values and try to insert them in the extended dataframe
for d in dssg_latest_data_tail['data']:
    hospitalized     = dssg_latest_data.loc[ dssg_latest_data['data'] == d ]['internados'].values[0]
    hospitalized_uci = dssg_latest_data.loc[ dssg_latest_data['data'] == d ]['internados_uci'].values[0]

    # protect the case where the dates are not found (ex: DGS file is too outdated)
    aux = merged_dssg_data.loc[ merged_dssg_data['data'] == d ]
    if not aux.empty:
        idx = aux.index[0]
        merged_dssg_data.at[idx, 'internados']     = hospitalized
        merged_dssg_data.at[idx, 'internados_uci'] = hospitalized_uci

# now let's interpolate to compensate for the spaced hospitalization data

merged_dssg_data['internados']     = merged_dssg_data['internados'].interpolate()
merged_dssg_data['internados_uci'] = merged_dssg_data['internados_uci'].interpolate()

# now let's write to CSV

merged_file = 'data-' + str(last_date) + '.csv'

merged_path = base_path + MERGED_DATA_SUBDIR + merged_file

print('\nSaving CSV at', merged_path)

# can be inspected with
# csvtool -t ',' col 1,12,14,15,16  /path/to/data/merged/data-2022-06-02.csv  |csvtool -t ',' readable - |less

merged_dssg_data.to_csv(merged_path, index=False)

print('\nInspect with:\n', 'csvtool -t \',\' col 1,12,14,15,16', merged_path, '|csvtool -t \',\' readable - |less' )

