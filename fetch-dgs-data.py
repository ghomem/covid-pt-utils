# This script downloads the daily Covid files from the new DGS website. It became necessary since DGS 
# discontinued the Covid dashboard and started providing (incomplete) information in XLSX files.
#
# Because the URL changes depending on the month and the file name includes a subtring with the file size in kb (!!)
# we need to ugly tricks to make sure we are able to programatically download the file.

import requests
import io
import datetime
import os
import argparse
import os.path
from os import path

# Funny brute force workaround for DGS including the file size in the name (duh)
# we try different file size strings until one works
# "SIZE_MAX ought to be enough for anybody"

SIZE_MIN = 50
SIZE_MAX = 150
BASE_URL = 'covid19.min-saude.pt'

# our health authority provides daily files with randomly variant names components
VARIANCE = [ 'xls', 'xlsx', 'excel' ]

my_date   = datetime.date.today()


date_str  = str(my_date)
date_year = my_date.year
date_mon  = str(my_date.month).zfill(2) # to ensure we have the leading zero for single digit months

url_list = []

for size in range (SIZE_MIN, SIZE_MAX):
    for substr in VARIANCE:
        # almost the same but the difference is the hiphen vs the underscore before subsstr
        dgs_url1 = f"""https://{BASE_URL}/wp-content/uploads/{date_year}/{date_mon}/covid_dados_{date_str}_{substr}-{size}kb.xlsx"""
        dgs_url2 = f"""https://{BASE_URL}/wp-content/uploads/{date_year}/{date_mon}/covid_dados_{date_str}-{substr}-{size}kb.xlsx"""
        url_list.append(dgs_url1)
        url_list.append(dgs_url2)

parser = argparse.ArgumentParser(description='Download DGS files')
parser.add_argument('path', type=str, help='path to where files will be stored')
args = parser.parse_args()
path_args = args.path

# check if path exists and is a directory, return error otherwise
if os.path.exists(path_args) is not True: 
   print ("There is not such Folder")
   exit(1)
else:
   print ("Folder:" + path_args)

# check if we have write permissions, return error otherwise
if os.access(path_args, os.W_OK) is not True:
            print("Folder not writable")
            exit(1)
else :
            print("Folder writable")

# Downloading the xls file + giving acceptable name

print('\n')
for url in url_list:
    print('Trying ' + url)
    name_path_xls = os.path.basename(url)
    # fix the stupid name given by DGS ( _xls-37kb ... )
    file_name_path = 'covid_dados' + '-' + date_str + '.xlsx'
    req = requests.get(url)
    status_code = req.status_code
    print('Status ' + str(status_code) + '\n')

    if status_code == 200:
        print('Got ' + url)
        url_content = req.content
        new_file_namepath=os.path.join(path_args, file_name_path)
        xls_file = open(new_file_namepath, 'wb')
        xls_file.write(url_content)
        xls_file.close()
        print('Wrote ' + new_file_namepath)
        exit(0)

