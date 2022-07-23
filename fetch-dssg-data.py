# -*- coding: utf-8 -*-
"""
Created on Sun Mar 21 17:11:21 2021

@author: Diogo
"""
# Libraries needed for the tutorial

import requests
import io
import datetime
import os
import argparse
import os.path
from os import path

csv_url = [ "https://raw.githubusercontent.com/dssg-pt/covid19pt-data/master/data.csv",
            "https://raw.githubusercontent.com/dssg-pt/covid19pt-data/master/amostras.csv",
            "https://raw.githubusercontent.com/dssg-pt/dados-SICOeVM/master/mortalidade.csv",
            "https://raw.githubusercontent.com/dssg-pt/covid19pt-data/master/vacinas.csv",
            "https://raw.githubusercontent.com/dssg-pt/covid19pt-data/master/data_concelhos_14dias.csv",
            "https://raw.githubusercontent.com/dssg-pt/covid19pt-data/master/data_concelhos_incidencia.csv",
            "https://opendata.ecdc.europa.eu/covid19/testing/csv/data.csv", # we need this complementary file from ECDC because DSSG does not have "amostras" anymore
          ]

parser = argparse.ArgumentParser(description='Download DSSG files')
parser.add_argument('path', type=str, help='path to where files will be stored')
args = parser.parse_args()
path_args = args.path

#descobrir se o path existe e simultamente que seja directório no sistema, e dar erro c.c
if os.path.exists(path_args) is not True: 
   print ("There is not such Folder")
   exit(1)
else:
   print ("Folder:" + path_args)

#descobrir se tenho permissões para escrever e caso não tenha dá erro
if os.access(path_args, os.W_OK) is not True:
            print("Folder not writable")
            exit(1)
else :
            print("Folder writable")

time_path = str(datetime.date.today())

# Downloading the csv file + giving name

for url in csv_url:
    print('downloading ' + url)
    name_path_csv = os.path.basename(url)
    name_path_split = name_path_csv.split('.')
    name_path = name_path_split[0]
    # this is to avoid name conflict, if we need for ECDC files in the future we will need to review this
    if 'ecdc' in url:
        file_name_path = 'ecdc-' + name_path + '-' + time_path + '.csv'
    else:
        file_name_path = name_path + '-' + time_path + '.csv'
    print('saving ' + file_name_path)
    req = requests.get(url)
    url_content = req.content
    new_file_namepath=os.path.join(path_args, file_name_path)
    csv_file = open(new_file_namepath, 'wb')
    csv_file.write(url_content)
    csv_file.close()

