#!/usr/bin/env python
# coding: utf-8


# =====================
# Handler code
# 1. Normalize/check if table matches correct structure, if not manipulate table to chronological 
# datetimes & mash together multiple sheets (steps 2 -> 5)
# 2. Remove impossible data, adjust to managable set, estimate missing fields(if data exists) (steps 6-12) 
# 
# continue if data set is complete for each city, if not must run local area averaging algorithm to fill in missing data points
#   -- Do this by using a distance finding (haversine) library function inside /lib/ 
#
# 1. First check for new cities in dataset, make sure the end state of cities matches (just NC cities)
# 2. check for extended dates beyond what is currently stored
# 3. Submit event for found tgtloc

# Note this will cause some distance calculations to be run more than once if requires averaging algorithm
# 
# Event hanlder for finding EXOG should store all its found distances so then if the calculation
# has already occured then restore it from "cache"  i.e. a distances.csv 
# =====================

import os
import getpass
import pandas as pd
import math
import numpy as np
import csv
import json
from ../lib/shasum import shasum


class DataWrangler:



    def onEvent(self):
        pass



# # Dynamic filepath finding
# try: 
#     __file__    # Jupyter vs regular python detection
# except:
#     curr_dir = os.path.abspath('')
# else:
#     curr_dir = os.path.dirname(os.path.realpath(__file__))
    
# app_root = curr_dir if os.path.basename(curr_dir) != "src" else os.path.dirname(curr_dir)

# if getpass.getuser() == "rainfalld":  # docker daemon
#     home = os.path.expanduser("~")
#     destdir = home                    # /var/cache/rainfall-predictor
# else:
#     destdir = os.path.join(app_root,'data','manipulated_data')      # non-docker stay in repository

# Load Files
file = os.path.join(app_root,'data','raw_data','NC Monthly Precipitation Data.xlsx')
latlong = pd.read_csv(os.path.join(app_root,'data','raw_data','latlong.csv'))
NCdata = pd.ExcelFile(file)


# Check if Data_Wrangling has already been accomplished
# If so, exit as success! If not or if changed dataset, accomplish
if getpass.getuser() == "rainfalld":                                # docker daemon
    original_datasets = { 
        "NC Monthly Precipitation Data.xlsx": shasum().file_sha(file),
        "latlong.csv": shasum().sha(latlong.to_csv())
    }
    output_data = {
        os.path.join(destdir,'rainfalldata.csv') : None,
        os.path.join(destdir,'distances.csv') : None,
        os.path.join(destdir,'ncrainfalldata.csv') : None,
        os.path.join(destdir,'exogen.json') : None
    }
    
    i = 0
    output_files = list(output_data.keys())
    try:
        while i < len(output_files):
            output_filename = output_files[i]
            output_data[output_filename] = shasum().file_sha(output_filename)
            i += 1

    except FileNotFoundError: 
        if i == 0:
            print("[DATA_WRANGLING] No previous data wrangling output found.  Starting from scratch!", flush=True)
        else:
            print("[DATA_WRANGLING] FileNotFoundError for file '{}'".format(output_files[i]))
            print("[DATA_WRANGLING] Handling missing file by starting from scratch!", flush=True)

    except:            # any error will cause entire Data Wrangling to run normally
        print("[DATA_WRANGLING] starting from scratch!", flush=True)

    else:
        completion_signature = shasum().sha( json.dumps({ **original_datasets, **output_data }) )
#         print(completion_signature)      # to update: uncomment this line, enable if-statement, run, and replace the next line's value
        if completion_signature == "7c8b32620e984fe4450e1f97fe75ad9361ec59dfc0a95d4d8cf8492baf76da46":
            print("COMPLETE: Output Files Exist & Data Integrity checked!")
            raise SystemExit(0)  # No need to complete rest of file
    


# #### Step 2
# I needed to bring all of the separate sheets in excel together into a single dataframe. Thus, this function uses a for loop to parse out each sheet from the excel file. Once I had the sheet, all of the months were in separate columns. The function takes all of the months and places them next to the year then places the rainfall amounts for each month in the next column. The function merges the resulting dataframe into the blank dataframe on the year and the month columns with an outer join in order to catch all the data from both the original and merging dataframe. 

# In[ ]:


blank = pd.DataFrame()
def datachunks(s, e, df): #s and e stand for the beginning and end of the chunk you want
    for i in range(s,e):
        to_merge = NCdata.parse(i, skiprows=[0,1], usecols=[0,1,2,3,4,5,6,7,8,9,10,11,12]) #first two rows in the data were titles
        to_merge = to_merge.dropna() #removes two rows from the data that were labeled as NaN and not needed
        to_merge = to_merge.set_index('Year') #set the index to year to remove the following 3 rows
        to_merge = to_merge.drop(['Mean','Max', 'Min'])
        to_merge = to_merge.reset_index() #resets the index so that the dataframe can be melted on Year
        to_merge1 = pd.melt(to_merge, id_vars=['Year'], value_vars=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug',
        'Sep','Oct','Nov','Dec'], var_name='Month') 
        to_merge1.iloc[:,2] = pd.to_numeric(to_merge1.iloc[:,2], errors = 'coerce')
        if i == 0:
            df = to_merge1
        else:
            df = pd.merge(df, to_merge1, on = ['Year','Month'], how = 'outer')
    return df

ncdata = datachunks(0,234, blank)
ncdata.tail()


# #### Step 3
# Column names to be placed on top of the dataframe

# In[ ]:


colnames = ['YEAR', 'MONTH']
names = NCdata.sheet_names
for idx, name in enumerate(names):
    names[idx] = name.upper().strip()
names[:10]


# In[ ]:


ncdata.columns = colnames + names
ncdata.head()


# #### Step 4
# In order to sort the data based on the year and month I needed to first convert the columns to datetime

# In[ ]:


ncdata["MONTH"] = pd.to_datetime(ncdata.MONTH, format='%b', errors='coerce').dt.month
ncdata["YEAR"] = pd.to_datetime(ncdata.YEAR, format='%Y', errors='coerce').dt.year
ncdata[['YEAR', 'MONTH']].head()


# In[ ]:


#this sorts the data based on year then month
ncdata_sorted = ncdata.sort_values(['YEAR','MONTH'])
ncdata_sorted.tail(12)


# #### Step 5
# Instead of separate columns for year and month the following code creates a single Date column and sets it as the index. The index is a string because datetime does not allow for dates without a day; however, having a day listed in the datetime would not be reasonable in this dataset because these are monthly totals of rainfall not occurring on a single day. 

# In[ ]:


ncdata_sorted['YEAR'] = ncdata_sorted.YEAR.apply(str)
ncdata_sorted['MONTH'] = ncdata_sorted.MONTH.apply(str)
ncdata_sorted['Date'] = ncdata_sorted['MONTH'] + '-' + ncdata_sorted['YEAR']
ncdata1 = ncdata_sorted.set_index('Date')
ncdata1 = ncdata1.drop(['YEAR', 'MONTH'], axis=1)
ncdata1.head()


# #### Step 6 - removing impossible data
# I gathered this data in May 2019; thus, it was impossible to have any totals from months that had not happened yet; therefore, I removed them

# In[ ]:


ncdata1 = ncdata1.drop(['5-2019', '6-2019', '7-2019', '8-2019','9-2019','10-2019','11-2019','12-2019'], axis=0)
ncdata1.tail(12)


# #### Step 7
# There was a lot of missing data from several locations. Due to this I created the following for loop in order to see which rows (corresponding to a single month) had at least 70% of data. Since the function len() counts missing data while the method .count() does not, I used these two functions to figure out the percentage that each row has and made it a column in the dataframe called 'percent_number'
# 
# I found that from January 1956-present all had data from at least 70% of the locations. 

# In[ ]:


lop = []
for i in ncdata1.index:
    l = len(ncdata1.loc[i])
    c = ncdata1.loc[i].count()
    percent = (c/l)*100
    if i == 0:
        lop = [percent]
    else:
        lop = lop + [percent]
ncdata1['percent_number'] = lop
ncdata1.percent_number[ncdata1.percent_number >= 80].head(20)


# #### Step 8
# Since I had the Date column as my index and I didn't want to remove it, I created a new index row called row_number. I used the row number to figure out which row 1-1956 was located at in order to create the dataframe that includes only data from 1-1956-present

# In[ ]:


nl = [i for i in range(1948)]
ncdata1['row_number'] = nl 
ncdata1.row_number.loc['1-1980'] # provides the row which Jan 1956 is located


# In[ ]:


ncdata_80 = ncdata1[ncdata1.row_number >= 1476]
ncdata_80.head()


# In[ ]:


#this drops the percent number column that is no longer needed.
ncdata_80 = ncdata_80.drop(['percent_number'],axis=1)


# #### Step 9
# The dataset also has some missing data from when the location began gathering data to the present. For example, even though Raleigh, NC has been gathering data from 1-1956 until the present there was one month in October of 2000 where the monthly total was not recorded. Thus the following function fills in missing data that are contained within the locations. This function finds the months with missing data and fills them in by averaging the rainfall totals from the previous year, previous month and next month. If the any of these points are not available either the function uses the data from two years prior, two months prior, or two months after. If just one of these is not available it ignores the NaN and averages the other two, otherwise it keeps the datapoint as NaN. Thus, this function does not get rid of all missing values, but fills in the missing values as long as there is adequate data to do so.

# In[ ]:


def missingfill(df, column):
    missing = df.index[df[column].isnull()]
    if len(missing) > 0:
        for n in missing:
            moth = df.loc[n].row_number # finds the row index for the missing data point
            if ((moth >= 1488) & (moth <= 1945)): #must be a year after 1-1956 (rownumber=1188) otherwise it is impossible to have the previous year's data to gather from
                ly = moth - 12 #the previous year's row number
                lyrd = df[[column]][df['row_number'] == ly] # the previous year's rainfall amount as a dataframe
                lyrd1 = lyrd[column][0] #separates the value of the previous year's dataframe to just the rainfall amount
                lm = moth - 1 # the next 6 lines perform the same as the previous 3 except for previous month and following month
                lmrd = df[[column]][df['row_number'] == lm]
                lmrd1 = lmrd[column][0]
                nm = moth + 1
                nmrd = df[[column]][df['row_number'] == nm]
                nmrd1 = nmrd[column][0]
                if ((math.isnan(lyrd1)) & (moth >= 1500)): # if the previous year was not available, go back 2 years
                    twy = moth - 24
                    twyrd = df[[column]][df['row_number'] == twy]
                    lyrd1 = twyrd[column][0]
                if (math.isnan(lmrd1)): #if the previous month was not available, go back 2 months
                    lm = moth - 2
                    lmrd = df[[column]][df['row_number'] == lm]
                    lmrd1 = lmrd[column][0]
                if (math.isnan(nmrd1)): #if the next month was not available, go forward 2 months
                    nm = moth + 2
                    nmrd = df[[column]][df['row_number'] == nm]
                    nmrd1 = nmrd[column][0]
                newpoint = np.nanmean([lyrd1,lmrd1,nmrd1]) #finds the average of the 3 values 
                df.loc[n,column] = newpoint #places the value into the missing data slot
    return(df)


# #### Step 10 
# performs the function defined in the previous cell and applies the function to every column. The runtime warning just means that np.nanmean has only nan values and thus is returning a nan value again, which is fine. 

# In[ ]:


for i in ncdata_80.columns:
    ncdata_80 = missingfill(ncdata_80, i)
ncdata_80.info()


# #### Step 11
# 
# Drop the row_number column since it is no longer needed, and make a csv file from the dataframe. 

# In[ ]:


# drops the row_number column since it is no longer needed. 
ncdata_80 = ncdata_80.drop(['row_number'],axis=1)
ncdatarein = ncdata_80.reset_index()
# #converts Date to datetime object
ncdatarein['Date'] = pd.to_datetime(ncdatarein['Date'])
alldatadf = ncdatarein.set_index('Date')
alldatadf.head()


# #### Step 12
# 
# Removal of duplicate sites.

# In[ ]:


alldatadf = alldatadf.drop(['RALEIGH AP, NC', 'GREENSBORO, NC', 'WILMINGTON 7 N, NC','LUMBERTON, NC',
                            'MYRTLE BEACH, SC','CHARLOTTE DOUGLAS AIRPORT, NC','GRNVL SPART INTL AP, SC',
                            'PICKENS, SC','MT. MITCHELL, NC','CAESARS HEAD AREA, SC'], axis=1)


# Now there is still the issue of missing data for some sites. The next steps fill in that missing data using locations that are within 85 kilometers of the location with missing data. First the latitude and longitude coordinates of each site are used to calculate the distance between sites. Then a function is used to subset only the surrounding locations of the location with missing data. Lastly, if there is more than one external location within 85 kilometers to the location with missing data then the average of those external locations were taken. 

# #### Step 13
# 
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


# #### Step 17
# 
# The subsequent function fills in the months that are missing from a certain location by averaging the rainfall amounts for the missing month in surrounding locations. 

# In[ ]:


def missingfillsurrounding(rdf, ddf):
    ''' args: rdf = rainfall dataframe
              ddf = distance df
        first finds any locations that are missing data at any point in the column 
        then from that list it loops over it to find the locations that are within 85 kilometers
        then creates a new datapoint from the mean of the surrounding locations. 
        returns: dataframe of filled data
    '''
    locwmd = rdf.columns[rdf.isna().any()].tolist()
    for loc in locwmd:
        nbloc = rdf[ddf[[loc]][ddf[loc] <=85].index]
        missing = nbloc.index[nbloc[loc].isnull()]
        if len(missing) >0:
            for m in missing:
                newpt = np.nanmean(nbloc.loc[m])
                rdf.loc[m,loc] = newpt
    return(rdf)
alldatadf_filled = missingfillsurrounding(alldatadf, distdf)


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



