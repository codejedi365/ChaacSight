#!/usr/bin/env python
# coding: utf-8

import os
import getpass
import pandas as pd
import math
import numpy as np
from math import radians, sin, cos, asin, sqrt
import csv
import json
from shasum import shasum

# Dynamic filepath finding
try: 
    __file__    # Jupyter vs regular python detection
except:
    curr_dir = os.path.abspath('')
else:
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    
app_root = curr_dir if os.path.basename(curr_dir) != "src" else os.path.dirname(curr_dir)

if getpass.getuser() == "rainfalld":  # docker daemon
    home = os.path.expanduser("~")
    destdir = home                    # /var/cache/rainfall-predictor
else:
    destdir = os.path.join(app_root,'data','manipulated_data')      # non-docker stay in repository

# Load Files
#file = os.path.join(app_root,'data','raw_data','NC Monthly Precipitation Data.xlsx')
latlong = pd.read_csv(os.path.join(app_root,'data','raw_data','latlong.csv'))






# Providing distance data from all locations to all other locations using LAT/LONG coordinates. First, the haversine function calculates the distance between two points on the globe

# In[ ]:


def haversine(lon1, lat1, lon2, lat2):
    ''' uses latitude and longitude coordinates of two locations and computes the distance in kilometers
    '''
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])    
    dlon = lon2 - lon1
    dlat = lat2 - lat1    
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 2 * 6371 * asin(sqrt(a))


# #### Step 14
# 
# Importing the latitude and longitude for each location that is in a csv file. Then separating the latitude and longitude for each location.

# In[ ]:


latlongsplit = latlong.iloc[0].apply(str.split, sep=',')


# #### Step 15
# 
# Creating the file as a pandas dataframe and then removing all duplicate locations as completed in step 12 for the filled data.

# In[ ]:


latlongdf = pd.DataFrame(latlongsplit)
latlongdf = latlongdf.drop(['Unnamed: 0'])
latlongdf_index = list(latlongdf.index)
for idx, name in enumerate(latlongdf_index):
    latlongdf_index[idx] = name.upper().strip()
latlongdf.index = latlongdf_index
latlongdf = latlongdf.drop(['RALEIGH AP, NC', 'GREENSBORO, NC', 'WILMINGTON 7 N, NC','LUMBERTON, NC',
                            'MYRTLE BEACH, SC','CHARLOTTE DOUGLAS AIRPORT, NC','GRNVL SPART INTL AP, SC',
                            'PICKENS, SC','MT. MITCHELL, NC','CAESARS HEAD AREA, SC'])
latlongdf.head()


# #### Step 16 
# 
# Next step is to find the distance between all of the locations which is done using the function below. It outputs a dataframe with the calculated distance between all locations. 

# In[ ]:


def distance_loc(df):
    '''calculates the distance between all locations and places it into a dataframe
    '''
    didf = pd.DataFrame(columns=df.index)
    row = {}
    for index in df.index:
        lat1, long1 = float(df.loc[index][0][0]), float(df.loc[index][0][1])
        for i in df.index:
            lat2, long2 = float(df.loc[i][0][0]), float(df.loc[i][0][1])
            dist = haversine(long1, lat1, long2, lat2)
            row[i] = dist
        didf = didf.append(row, ignore_index=True)
    return(didf)


# In[ ]:


# index is the same as the columns so just names the columns the same as the columns 
distdf = distance_loc(latlongdf)
distdf.index = distdf.columns
distdf.head(10)



# #### Step 18 
# 
# Separation of locations into north carolina and the surrounding states. 

# In[ ]:


locations = alldatadf_filled.columns
ncloc = locations[locations.str.endswith('NC')]
valoc = locations[locations.str.endswith('VA')]
scloc = locations[locations.str.endswith('SC')]
galoc = locations[locations.str.endswith('GA')]
tnloc = locations[locations.str.endswith('TN')]
ncdatadf = alldatadf_filled[ncloc]


# #### Step 19
# 
# Placing dataframes into csv files to be exported into other notebooks for calculations

# In[ ]:


csvfiles_to_create = [
    { 'data': alldatadf_filled, 'dest': os.path.join(destdir,'rainfalldata.csv') },
    { 'data': distdf, 'dest': os.path.join(destdir,'distances.csv') },
    { 'data': ncdatadf, 'dest': os.path.join(destdir,'ncrainfalldata.csv') }
]

for i in range(len(csvfiles_to_create)):
    csvfiles_to_create[i]['data'].to_csv(csvfiles_to_create[i]['dest'])
    print("[DATA_WRANGLING] Created file {}".format(csvfiles_to_create[i]['dest']), flush=True)


# In[ ]:


# list of target locations = tarloc
# list of exo locations = exoloc
# latitude, longitude df = lldf
def exofind(lldf, tarloc, exoloc):
    '''args: tarloc is the list of target locations 
             exoloc is the list of exo locations
             lldf is the latitude, longitude dataframe 
       returns: dictionary with keys being the location and values being the exogenous variables
    '''
    tarexoloc = tarloc.append(exoloc)
    tarexoll = lldf.loc[tarexoloc]
    # using the distance_loc function defined earlier to find the distances between just the 
    # target locations and the exogenous locations
    tartoexodist = distance_loc(tarexoll)
    exodistances = tartoexodist[exoloc] #subset of just the exogenous distances to target
    exodistances.index = tartoexodist.columns
    exodist2 = exodistances.drop(exoloc,axis=0)
    closeexo = exodist2[exodist2 <= 50] # subsetting only those locations that are within 50 kilometers of the 
                                            #target locations
    closeexo1 = closeexo.dropna(how='all') #dropping missing values
    closeexo2 = closeexo1.dropna(axis=1,how='all')
    exo = {}
    for i in closeexo2.index:
        ex = closeexo2.loc[i][closeexo2.loc[i].notnull()].index.tolist()
        exo[i]=ex
    return(exo)


# #### Step 20
# 
# creating the dictionary from the exogenous locations

# In[ ]:


exoloc = valoc.append(scloc)
exoloc = exoloc.append(galoc)
exoloc = exoloc.append(tnloc)
exogen = exofind(latlongdf,ncloc,exoloc)
exogen


# #### Step 21
# 
# storing the dictionary so that it can be retrieved from the other jupyter notebooks or other python programs

# In[ ]:


try:
  get_ipython().run_line_magic('store', 'exogen')
except NameError:             # For non-jupyter processing
    exogen_json = json.dumps(exogen, sort_keys=True, indent=4)
    exogen_filepath = os.path.join(destdir,"exogen.json")
    f = open(exogen_filepath,"w+")
    f.write(exogen_json+'\n')
    f.close()
    print("[DATA_WRANGLING] Created file {}".format(exogen_filepath), flush=True)

