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

csv_url = [ "https://raw.githubusercontent.com/dssg-pt/covid19pt-data/master/data.csv",
            "https://raw.githubusercontent.com/dssg-pt/covid19pt-data/master/amostras.csv,",
            "https://raw.githubusercontent.com/dssg-pt/covid19pt-data/master/mortalidade.csv",
            "https://raw.githubusercontent.com/dssg-pt/covid19pt-data/master/vacinas.csv",
          ]

time_path = str(datetime.date.today())

# Downloading the csv file + giving name

for url in csv_url:
    print('downloading ' + url)
    name_path_csv = os.path.basename(url)
    name_path_split = name_path_csv.split('.')
    name_path = name_path_split[0]
    file_name_path = name_path + '-' + time_path + '.csv'
    print('saving ' + file_name_path)
    req = requests.get(url)
    url_content = req.content
    csv_file = open(file_name_path, 'wb')
    csv_file.write(url_content)
    csv_file.close()
