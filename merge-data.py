import os
import glob
import argparse
import numpy as np
import pandas as pd
import datetime
import shutil

### CONFIG ###

INITIAL_DATE_STR = '26-02-2020'
PATCH_DATE_STR   = '14-03-2022'  # the day after the data from DSSG stopped flowing
PATCH_DATE_STR_D = '2022-03-14'  # the DSG files use a different format

HOSP_PATCH_DATE_STR = '15-03-2022'  # the first weekly hospitalizations record from the DSSG file

INITIAL_DATE = datetime.datetime.strptime(INITIAL_DATE_STR, '%d-%m-%Y').date()
PATCH_DATE   = datetime.datetime.strptime(PATCH_DATE_STR, '%d-%m-%Y').date()

TESTING_PATCH_DATE_STR = '02-06-2022' # the day after the testing data from DSSG stopped flowing
TESTING_PATCH_DATE     = datetime.datetime.strptime(TESTING_PATCH_DATE_STR, '%d-%m-%Y').date()

# this is a very complete file from the awesome DSSG-PT group, we saved the last complete version
# to inspect only the new cases and deaths we can use
# csvtool -t ',' col 1,12,14,15,16 data-2022-03-13.csv | csvtool -t ',' readable

# despite the name, this file has the last data at 2022-03-13
DSSG_FILE = 'data-2022-03-20.csv'

DGS_SUBDIR = 'dgs/'
DSSG_LATEST_SUBDIR = 'dssg/'
MERGED_DATA_SUBDIR = 'merged/'


### FUNCTIONS ###

def mk_dates( initial_date, days ):

    dates = []

    cur_date   = initial_date
    final_date = initial_date + datetime.timedelta(days=days)

    while cur_date < final_date:
        dates.append(cur_date.strftime('%d-%m-%Y'))
        cur_date = cur_date + datetime.timedelta(days=1)

    # the current date is formatted backwards, for the file name
    return dates, cur_date.strftime('%Y-%m-%d')


def print_summary( df ):
    print( df[ ['data', 'confirmados_novos', 'obitos'] ] )


# gets the most recent DGS info
def get_dgs_info( dgs_dir ):

    # this is the minimalistic DSG file that started being published around 13-03-2022
    # when the dashboard was discontinued (except for the 'amostras' part )

    # columns of the DGS file
    #
    # * confirmation_date1 - date
    # * day_cum_abs_num     - daily cases
    # * day_ob_abs_num      - daily deaths

    # find the latest available file
    dgs_file_list = glob.glob(dgs_dir + '/covid_dados-*.xlsx')
    dgs_path      = max(dgs_file_list, key=os.path.getctime)

    # read the second tab of the excel file
    dgs_data = pd.read_excel(dgs_path, sheet_name=1)

    return dgs_data, dgs_path


# gets the most recent DSSG info
def get_dssg_info( dssg_dir, search_str ):

    dssg_file_list = glob.glob(dssg_dir + search_str + '-*.csv')
    dssg_path      = max(dssg_file_list, key=os.path.getctime)

    dssg_data = pd.read_csv(dssg_path)

    return dssg_data, dssg_path


# convert the ECDC week date to a normal date
def mk_date_from_week_str ( week_str ):

    # 6 is Saturday, we are assuming the values come at the end of the week
    day_of_the_week = '6'
    iso_date = datetime.datetime.strptime(week_str + '-' + day_of_the_week, "%Y-W%W-%w").date()

    # this is the format in the DSSG files
    reverse_date = iso_date.strftime('%d-%m-%Y')

    return reverse_date


# gets the most recent ECDC testing data
def get_ecdc_testing_info ( ecdc_dir ):

    ecdc_file_list = glob.glob(dssg_dir + 'ecdc-*.csv')
    ecdc_path      = max(ecdc_file_list, key=os.path.getctime)

    ecdc_data = pd.read_csv(ecdc_path)

    # filter for Portugal
    ecdc_data_PT = ecdc_data[ (ecdc_data['country'] == 'Portugal') & (ecdc_data['level'] == 'national') ]

    converted_dates = [ mk_date_from_week_str(x) for x in ecdc_data_PT['year_week'] ]

    # add column for normal dates
    ecdc_data_PT.insert(3, 'converted_date', converted_dates)

    # remove unnecessary columns, we can reenable them for debugging if necessary
    ecdc_data_PT_trimmed = ecdc_data_PT.drop(['country', 'country_code', 'level', 'region', 'region_name', 'testing_data_source' ], axis=1)

    # filger

    return ecdc_data_PT_trimmed, ecdc_path


# patch the DSSG testing dataset with data from ECDC
def merge_testing_data ( dssg_testing_data, ecdc_testing_data, patch_date ):

    date_str_f = ecdc_testing_data['converted_date'].values[-1]
    date_str_i = dssg_testing_data['data'].values[-1]

    date_f = datetime.datetime.strptime(date_str_f, '%d-%m-%Y').date()
    date_i = datetime.datetime.strptime(date_str_i, '%d-%m-%Y').date()

    time_delta = date_f - date_i

    ndays_testing = time_delta.days

    # generate the dates we need to have from patch_date on
    dates, last_date = mk_dates(patch_date, ndays_testing)

    tests_daily = []
    for d in dates:
        tests_lookup = ecdc_testing_data [ ecdc_testing_data['converted_date'] == d ]['tests_done'].values

        # either the value for that date is in the ECDC data or it isn't
        if len(tests_lookup) != 0:
            tests_daily.append(tests_lookup[0] / 7 ) # we divide by 7 because it is a weekly value
        else:
            # write NaN
            tests_daily.append(np.nan)
        #print(d, tests_daily[-1])

    # this is the list of fields of this file
    # data,amostras,amostras_novas,amostras_pcr,amostras_pcr_novas,amostras_antigenio,amostras_antigenio_novas
    # we only have amostras, the rest is filled with NaN
    extra_testing_data = pd.DataFrame( {'data': dates, 'amostras_novas': tests_daily, } )

    # and finally let's merge the dataframes
    merged_testing_data = dssg_testing_data.append(extra_testing_data, ignore_index=True, sort=False)

    # interpolate the weekly value
    merged_testing_data['amostras_novas'] = merged_testing_data['amostras_novas'].interpolate()

    return merged_testing_data, last_date


def write_to_csv( dataframe, path, filename ):

    print('\nSaving', filename, 'at', path)

    full_path = path + filename

    dataframe.to_csv(full_path, index=False)


def copy_files_to_final_location ( path, final_path ):

    print('')
    print('copying files from', path, 'to', final_path)

    files1 = glob.glob(path + MERGED_DATA_SUBDIR + 'data-*.csv')
    files2 = glob.glob(path + MERGED_DATA_SUBDIR + 'amostras-*.csv')
    files3 = glob.glob(path + DSSG_LATEST_SUBDIR + 'mortalidade-*.csv')
    files4 = glob.glob(path + DSSG_LATEST_SUBDIR + 'vacinas-*.csv')
    files5 = glob.glob(path + DSSG_LATEST_SUBDIR + 'data_concelhos_incidencia-*.csv')

    main_file  = max(files1, key=os.path.getctime)
    tests_file = max(files2, key=os.path.getctime)
    mort_file  = max(files3, key=os.path.getctime)
    vacc_file  = max(files4, key=os.path.getctime)
    geo_file   = max(files5, key=os.path.getctime)

    shutil.copy(main_file,  final_path + '/merged/data.csv')
    shutil.copy(tests_file, final_path + '/merged/amostras.csv')
    shutil.copy(mort_file,  final_path + '/dssg/mortalidade.csv')
    shutil.copy(vacc_file,  final_path + '/dssg/vacinas.csv')
    shutil.copy(geo_file,   final_path + '/dssg/data_concelhos_incidencia.csv')

### MAIN ###

parser = argparse.ArgumentParser(description='Merge DGS, DSSG and ECDC files')
parser.add_argument('path',       type=str, help='path to where files will be stored')
parser.add_argument('final_path', type=str, help='path to where the latest will be stored with a standard name')

args = parser.parse_args()

path_args  = args.path
final_path = args.final_path

for p in [ path_args, final_path ]:
    if os.path.exists(p) is not True:
        print("There is no folder called", p)
        exit(1)
    else:
        print("Folder:" + path_args)

    if os.access(p, os.W_OK) is not True:
        print('Folder', p, 'is not writable')
        exit(1)
    else:
        print('Folder', p, 'is writable')

# start the work on data files

base_path = path_args + '/'

# first the static DSSG file that we use for historic data

dssg_path = base_path + DSSG_FILE
dssg_data = pd.read_csv(dssg_path)

# then the latest DGS file with daily data

dgs_dir = base_path + DGS_SUBDIR
dgs_data, dgs_path = get_dgs_info(dgs_dir)

print('\nMerging', dssg_path, 'with', dgs_path, '\n')

# we now wish to patch the DSSG file using the data from the DGS file starting at PATCH_DATE

index = dgs_data.loc[ dgs_data['confirmation_date1'] == PATCH_DATE_STR_D ].index[0]

dgs_data_tail = dgs_data.loc[index:]

# now lets obtain the necessary values

cases  = dgs_data_tail['day_cum_abs_num']
deaths = dgs_data_tail['day_ob_abs_num' ]
ndays  = len(cases.index)

dates, last_date = mk_dates(PATCH_DATE, ndays)

# the deaths need to be cumulative, and the last value from DSSG needs to be added

cum_deaths = np.cumsum(deaths) + dssg_data.iloc[-1]['obitos']

# let's create a dataframe with the DSSG naming, the remaining columns are filled with NaN

extra_dssg_data = pd.DataFrame( {'data': dates, 'confirmados_novos': cases.to_list(), 'obitos': cum_deaths.astype(int).to_list() } )

# and finally let's merge the dataframes

merged_dssg_data = dssg_data.append(extra_dssg_data, ignore_index=True, sort=False)

print_summary(merged_dssg_data)

# now let's look for the latest dssg file to extract the hospitalizations data

dssg_dir = base_path + DSSG_LATEST_SUBDIR
dssg_latest_data, dssg_latest_path = get_dssg_info(dssg_dir, 'data')

index = dssg_latest_data.loc[ dssg_latest_data['data'] == HOSP_PATCH_DATE_STR ].index[0]

dssg_latest_data_tail = dssg_latest_data.loc[index:]

# let's fetch the weekly values for the hospitalizations and try to insert them in the extended dataframe
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

# now we need to do the same for the testing data which we now collect from ECDC

# now let's write to CSV

filename = 'data-' + str(last_date) + '.csv'

merged_path = base_path + MERGED_DATA_SUBDIR

write_to_csv( merged_dssg_data, merged_path, filename)

# can be inspected with
# csvtool -t ',' col 1,12,14,15,16  /path/to/data/merged/data-2022-06-02.csv  |csvtool -t ',' readable - |less

print('\nInspect with:\n', 'csvtool -t \',\' col 1,12,14,15,16', merged_path+filename, '|csvtool -t \',\' readable - |less' )

######## ECDC testing information ########

ecdc_dir = base_path + DSSG_LATEST_SUBDIR # we are for now using the same dir for ECDC
ecdc_latest_data, ecdc_latest_path = get_ecdc_testing_info(dssg_dir)

dssg_latest_testing_data, dssg_latest_path = get_dssg_info(dssg_dir, 'amostras')

merged_testing_data, last_date_testing = merge_testing_data(dssg_latest_testing_data, ecdc_latest_data, TESTING_PATCH_DATE)

print('\n')
print(merged_testing_data)

filename = 'amostras-' + str(last_date_testing) + '.csv'
write_to_csv( merged_testing_data, merged_path, filename)

print('\nInspect with:\n', 'csvtool -t \',\' readable ', merged_path+filename, '|less' )

######## ECDC ########

### FINAL STEP ######

# as a final step we copy the latest of each type of file to a standard filename in a standard place

copy_files_to_final_location( base_path, final_path)
