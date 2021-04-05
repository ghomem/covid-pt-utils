# -*- coding: utf-8 -*-
"""
Created on Sun Mar 21 17:11:21 2021

@author: Diogo
"""



# Libraries needed for the tutorial

import pandas as pd
import requests
import io
import datetime
    
# Downloading the csv file from your GitHub account



#df = pd.read_csv('data.csv')

#print(df.head()) 


csv_url = "https://raw.githubusercontent.com/dssg-pt/covid19pt-data/master/data.csv" # Make sure the url is the raw version of the file on GitHub

#csv_url = "https://raw.githubusercontent.com/dssg-pt/covid19pt-data/master/amostras.csv" # Make sure the url is the raw version of the file on GitHub



#csv_url="https://raw.githubusercontent.com/dssg-pt/covid19pt-data/master/vacinas.csv"



#https://raw.githubusercontent.com/dssg-pt/covid19pt-data/master/data.csv
#https://github.com/dssg-pt/dados-SICOeVM/blob/master/mortalidade.csv
#https://raw.githubusercontent.com/dssg-pt/covid19pt-data/master/vacinas.csv


time_path = str(datetime.date.today())

name_path='data_'

file_name_path=name_path+time_path+'.csv'

req = requests.get(csv_url)
url_content = req.content
csv_file = open(file_name_path, 'wb')

csv_file.write(url_content)
csv_file.close()


df = pd.read_csv('downloaded.csv')


print (df)

print(file_name_path)





x = datetime.date.today()



print(x)
print(x.strftime("%A"))



#print("Hello new World")

#url = "https://github.com/dssg-pt/covid19pt-data/blob/master/data.csv" # Make sure the url is the raw version of the file on GitHub
#download = requests.get(url).content

#print(download)

# # Reading the downloaded content and turning it into a pandas dataframe


#df = pd.read_csv(io.StringIO(download.decode('utf-8')))

#  # Printing out the first 5 rows of the dataframe

#! pwd

# df = pd.read_csv(download)

# print (df.head())
