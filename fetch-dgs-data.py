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

SIZE_MIN = 40
SIZE_MAX = 60

# our health authority provides daily files with randomly variant names components
VARIANCE = [ 'xls', 'xlsx', 'excel', 'XLS' ]
VARIANCE_ON = True

USER_AGENT='Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:102.0) Gecko/20100101 Firefox/102.0'

### Main

parser = argparse.ArgumentParser(description='Download DGS files')
parser.add_argument('path',      type=str, help='path to where files will be stored')
parser.add_argument('base_url',  type=str, help='base URL from where the files will be downloaded')
args = parser.parse_args()

path_args = args.path
base_url  = args.base_url

# our heath authority sometimes names the files with the date of the upload day
# and other times with the date of the previous day... sic transit glori mundi
yesterday = datetime.date.today() - datetime.timedelta(days = 1)
today     = datetime.date.today()

# yesterday and then today
date_strs = [ str(today), str(yesterday) ]

date_year = today.year
date_mon  = str(today.month).zfill(2) # to ensure we have the leading zero for single digit months

url_list = []

# on the 25th of July of 2022, DGS heard the word of God and produced a file without variance in the name
# let's add that simplest option to the list of URLs and if things stabilize this way we might remove the variance handling code at some point

for date_str in date_strs:
    dgs_url_simple = f"""https://{base_url}/wp-content/uploads/{date_year}/{date_mon}/covid_dados_{date_str}.xlsx"""
    print('inserting basic URL', dgs_url_simple)
    # the most recent one will be at the beggining of the list
    url_list.append(dgs_url_simple)

# God also told DSG to filter the user agent making more difficult, but not impossible, automated downloads

if VARIANCE_ON:
    for date_str in date_strs:
        for size in range (SIZE_MIN, SIZE_MAX):
            for substr in VARIANCE:
                # almost the same but the difference is the hiphen vs the underscore before subsstr
                dgs_url1 = f"""https://{base_url}/wp-content/uploads/{date_year}/{date_mon}/covid_dados_{date_str}_{substr}-{size}kb.xlsx"""
                dgs_url2 = f"""https://{base_url}/wp-content/uploads/{date_year}/{date_mon}/covid_dados_{date_str}-{substr}-{size}kb.xlsx"""
                url_list.append(dgs_url1)
                url_list.append(dgs_url2)

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

downloads = []
print('\n')

yesterday = False
for url in url_list:
    print('Trying ' + url)
    name_path_xls = os.path.basename(url)
    # fix the stupid name given by DGS ( _xls-37kb ... )
    if date_strs[0] in name_path_xls:
        print ('URL from today')
        my_date = date_strs[0]
        yesterday = False
    if date_strs[1] in name_path_xls:
        print ('URL file from yesterday')
        my_date = date_strs[1]
        yesterday = True

    file_name_path = 'covid_dados' + '-' + my_date + '.xlsx'
    headers = { 'User-Agent': USER_AGENT }
    req = requests.get(url, headers=headers)
    status_code = req.status_code
    print('Status ' + str(status_code) + '\n')

    if status_code == 200:
        print('Got ' + url)
        url_content = req.content
        new_file_namepath=os.path.join(path_args, file_name_path)
        xls_file = open(new_file_namepath, 'wb')
        xls_file.write(url_content)
        xls_file.close()
        print('Wrote ' + new_file_namepath+ '\n')
        # touch the file appropriately
        if yesterday:
            os.utime(new_file_namepath, ( os.stat(new_file_namepath).st_mtime-24*3600, os.stat(new_file_namepath).st_mtime-24*3600))
        downloads.append(new_file_namepath)

        # we are currently allowing to downloads because we touch the old one, if it gets downloaded
        if len(downloads) == 2:
            print('Downloaded files', downloads)
            exit(0)

print('Downloaded files', downloads)
