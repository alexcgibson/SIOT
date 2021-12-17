from __future__ import print_function
from os import remove
import os.path
import numpy
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import pandas as pd
from google.oauth2 import service_account
import pickle
import math
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
import requests
import json
import time
from datetime import date
from scipy.ndimage.measurements import mean
from scipy.signal import find_peaks
from itertools import groupby

#finding the highest changes in temperature, ambient light and humidity - these areas signify a change in environment

#calling google sheets api to access the database
def gsheet_api_check(SCOPES):
    creds = None
    if os.path.exists('/Users/alexgibson/Documents/DESENG/DE4/Sensing & IoT/Coursework/SIOT Python/token.pickle'):
        with open('/Users/alexgibson/Documents/DESENG/DE4/Sensing & IoT/Coursework/SIOT Python/token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                '/Users/alexgibson/Documents/DESENG/DE4/Sensing & IoT/Coursework/SIOT Python/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('/Users/alexgibson/Documents/DESENG/DE4/Sensing & IoT/Coursework/SIOT Python/token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def pull_sheet_data(SCOPES,SPREADSHEET_ID,DATA_TO_PULL):
    creds = gsheet_api_check(SCOPES)
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=DATA_TO_PULL).execute()
    values = result.get('values', [])
    
    if not values:
        print('No data found.')
    else:
        rows = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                  range=DATA_TO_PULL).execute()
        data = rows.get('values')
        print("COMPLETE: Data copied")
        return data

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

SPREADSHEET_ID = '1AKFnuvhTEsSRvXL8453bPbXv8SCa2bwqBxEJPYObmqQ'
DATA_TO_PULL = 'Sheet1'
data = pull_sheet_data(SCOPES,SPREADSHEET_ID,DATA_TO_PULL)
df = pd.DataFrame(data[1:], columns=data[0])

headers =  ["Date", "Reading Type", "Humidity (%)", "Temperature (°Celcius)","Ambient Light"]
df.columns = headers

#set the data used as today's or choose a day from the past
today = date.today()
todaystring = today.strftime("%B %d, %Y")
print("Today's date:", todaystring)
#if you want today's date, change dayused to todaystring
#if you want another date, change dayused to that days date
dayused = 'November 25'
df = df[df['Date'].str.contains(str(dayused))]


#turn column values into floats
df["Humidity (%)"] = df["Humidity (%)"].astype(float)
df["Temperature (°Celcius)"] = df["Temperature (°Celcius)"].astype(float)
df["Ambient Light"] = df["Ambient Light"].astype(float)

print(df)

length = len(df)
rootlen = int(math.sqrt(length))

print('Length of dataset: {}'.format(length))
print('Square root of dataset: {}'.format(rootlen))

#add column titles
humiditydata = df.loc[:,'Humidity (%)']
tempdata = df.loc[:,'Temperature (°Celcius)']
ambientlightdata = df.loc[:,'Ambient Light']

#create empty arrays to append the data from the data frame into - 
#the function that differentiates the data requires the data in arrays
humidityarray = []
temparray = []
ambientlightarray = []

for i in humiditydata:
    humidityarray.append(i)

for i in tempdata:
    temparray.append(i)

for i in ambientlightdata:
    ambientlightarray.append(i)

#turning the dataset into readable integers for the the differentation function
dfnew = pd.DataFrame({'temp': temparray,
                    'ambientlight':ambientlightarray,
                    'humidity': humidityarray})

#differentiate the dataset
roc = dfnew.diff()
#drop NaNs from the differentiated dataset
roc = roc.dropna()

#temperature graph
#white = data
#red = differentiated data
#dots = peaks
tempgraph = plt.figure(figsize=(18,6))
tempgraph.patch.set_facecolor('#101010')
ax = tempgraph.add_subplot()
tempgraph = plt.plot(dfnew['temp'], color ='white',linewidth=3)
temprocgraph = plt.plot(roc['temp'], color ='red',linewidth=3)
ax.set_facecolor('#101010')
ax.spines['bottom'].set_color('#FFFFFF')
ax.spines['top'].set_color('#101010')
ax.spines['right'].set_color('#101010')
ax.spines['left'].set_color('#FFFFFF')
ax.xaxis.label.set_color('#FFFFFF')
ax.yaxis.label.set_color('#FFFFFF')
ax.tick_params(axis='x', colors='white')
ax.tick_params(axis='y', colors='white')
plt.xlabel('Minutes', fontname='Helvetica Neue')
plt.ylabel("Temperature (°Celcius)", fontname='Helvetica Neue')
x = np.array(dfnew['temp'])
temproc = np.array(roc['temp'])
xtroughs, _ = find_peaks(-x, height=-18)
xtroughsroc, _ = find_peaks(-temproc, height=2)
plt.plot(xtroughs, x[xtroughs], "o", linewidth=3, markersize=8)
plt.plot(xtroughsroc, temproc[xtroughsroc], "o", linewidth=3, markersize=8)
plt.savefig('/Users/alexgibson/Documents/DESENG/PORTFOLIO/PORTFOLIOCODE/public/projectsites/SIOTSite/graphs/tempgraph.png', bbox_inches='tight', pad_inches = 0)

#ambient light graph
#white = data
#red = differentiated data
#dots = peaks
ambientlightgraph = plt.figure(figsize=(18,6))
ambientlightgraph.patch.set_facecolor('#101010')
ax = ambientlightgraph.add_subplot()
ambientlightgraph = plt.plot(ambientlightarray, color ='white',linewidth=3)
ambientlightrocgraph = plt.plot(roc['ambientlight'], color ='red',linewidth=3)
ax.set_facecolor('#101010')
ax.spines['bottom'].set_color('#FFFFFF')
ax.spines['top'].set_color('#101010')
ax.spines['right'].set_color('#101010')
ax.spines['left'].set_color('#FFFFFF')
ax.xaxis.label.set_color('#FFFFFF')
ax.yaxis.label.set_color('#FFFFFF')
ax.tick_params(axis='x', colors='white')
ax.tick_params(axis='y', colors='white')
plt.xlabel('Minutes', fontname='Helvetica Neue')
plt.ylabel("Ambient Light", fontname='Helvetica Neue')
y = np.array(dfnew['ambientlight'])
ambientlightroc = np.array(roc['ambientlight'])
ypeaks, _ = find_peaks(y, height=2000)
ypeakroc, _ = find_peaks(ambientlightroc, height=2000)
plt.plot(ypeaks, y[ypeaks], "o", linewidth=3, markersize=8)
plt.plot(ypeakroc, ambientlightroc[ypeakroc], "o", linewidth=3, markersize=8)
plt.savefig('/Users/alexgibson/Documents/DESENG/PORTFOLIO/PORTFOLIOCODE/public/projectsites/SIOTSite/graphs/ambientlightgraph.png', bbox_inches='tight', pad_inches = 0)

#humidity graph
#white = data
#red = differentiated data
#dots = peaks
humiditygraph = plt.figure(figsize=(18,6))
humiditygraph.patch.set_facecolor('#101010')
ax = humiditygraph.add_subplot()
humiditygraph = plt.plot(humidityarray, color ='white',linewidth=3)
humidityrocgraph = plt.plot(roc['humidity'], color ='red',linewidth=3)
ax.set_facecolor('#101010')
ax.spines['bottom'].set_color('#FFFFFF')
ax.spines['top'].set_color('#101010')
ax.spines['right'].set_color('#101010')
ax.spines['left'].set_color('#FFFFFF')
ax.xaxis.label.set_color('#FFFFFF')
ax.yaxis.label.set_color('#FFFFFF')
ax.tick_params(axis='x', colors='white')
ax.tick_params(axis='y', colors='white')
plt.xlabel('Minutes', fontname='Helvetica Neue')
plt.ylabel("Humidity (%)", fontname='Helvetica Neue')
z = np.array(dfnew['humidity'])
humidityroc = np.array(roc['humidity'])
zpeaks, _ = find_peaks(z, height=65)
zpeakroc, _ = find_peaks(humidityroc, height=10)
plt.plot(zpeaks, z[zpeaks], "o", linewidth=3, markersize=8)
plt.plot(zpeakroc, humidityroc[zpeakroc], "o", linewidth=3, markersize=8)
plt.savefig('/Users/alexgibson/Documents/DESENG/PORTFOLIO/PORTFOLIOCODE/public/projectsites/SIOTSite/graphs/humiditygraph.png', bbox_inches='tight', pad_inches = 0)
plt.show()

#create lists of time and magnitude of temperature troughs
xtrough_pos = xtroughsroc[:]
xtrough_height = x[xtroughsroc[:]]
print('Temperature greatest rate of change position: {}, Temperature greatest rate of change: {}'.format(xtrough_pos, xtrough_height))

#create lists of time and magnitude of ambient light peaks
ypeak_pos = ypeakroc[:]
ypeak_height = y[ypeakroc[:]]
print('Ambient light greatest rate of change position: {}, Ambient light greatest rate of change: {}'.format(ypeak_pos, ypeak_height))

#create lists of time and magnitude of humidity peaks
zpeak_pos = zpeakroc[:]
zpeak_height = z[zpeakroc[:]]
print('Humidity peaks position: {}, Humidity peaks height: {}'.format(zpeak_pos, zpeak_height))

xtroughlist = []
zpeakslist = []

for i in xtrough_pos:
    xtroughlist.append(i)

for i in zpeak_pos:
    zpeakslist.append(i)

print("Minutes at which temperature change is maximum: {}".format(xtroughlist))
print("Minutes at which humidity change is maximum: {}".format(zpeakslist))

#remove values that are closer than 20 mins together as they do not signify a change in environment
def runs(difference=20):
    start = None
    def inner(n):
        nonlocal start
        if start is None:
            start = n
        elif abs(start-n) > difference:
            start = n
        return start
    return inner

xtroughlistreduced = ([next(g) for k, g in groupby(xtroughlist, runs())])
zpeaklistreduced = ([next(g) for k, g in groupby(zpeakslist, runs())])

#add the lists of time signatures together - viewing them together allows the clusters to be viewed
tempandhumiditypeak = xtroughlistreduced + zpeaklistreduced
tempandhumiditypeak.sort()
print(tempandhumiditypeak)

#cluster values removed from the combined temperature and humidity lists
tempandhumiditypeakreduced = ([next(g) for k, g in groupby(zpeakslist, runs())])

print("Minutes at which temperature change is maximum, with repeats removed: {}".format(xtroughlistreduced))
print("Minutes at which humidity change is maximum, with repeats removed: {}".format(zpeaklistreduced))
print("Minutes at which temp and humidity change are maximum, with repeats removed: {}".format(tempandhumiditypeakreduced))

print('Number of times user changed environment on {}: {}'.format(dayused,len(tempandhumiditypeakreduced)))
