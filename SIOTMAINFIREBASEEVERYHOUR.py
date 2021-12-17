from __future__ import print_function
import os.path
from apscheduler import schedulers
import numpy
from _plotly_utils.colors.colorbrewer import Greys
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from matplotlib.image import BboxImage
import pandas as pd
import json
import csv
from google.oauth2 import service_account
import pygsheets
import clients
import pickle
import math
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from collections import OrderedDict
from scipy.ndimage import gaussian_filter
import requests
import json
import time
import os
import subprocess
from datetime import date, datetime, timedelta, time
import schedule

def siotscript():
    #calling weather api to save weather conditions to variables for use later
    APIresponse = requests.get('https://api.openweathermap.org/data/2.5/weather?q=London&appid=c674ee3b2a7ff0fc6f40764e165004d7')
    apidata = APIresponse.text
    parse_json = json.loads(apidata)
    mainconditions = parse_json['weather'][0]['main']
    detailconditions = parse_json['weather'][0]['description']
    print(mainconditions)
    print(detailconditions)

    #calling google sheets api to access data stored in the database
    def gsheet_api_check(SCOPES):
        creds = None
        if os.path.exists('/Users/Alex Gibson/Desktop/SIOTPYTHON/token.pickle'):
            with open('/Users/Alex Gibson/Desktop/SIOTPYTHON//token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    '/Users/Alex Gibson/Desktop/SIOTPYTHON/credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('/Users/Alex Gibson/Desktop/SIOTPYTHON/token.pickle', 'wb') as token:
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

    #remove nans from the imported dataset
    df = df.dropna()

    headers =  ["Date", "Reading Type", "Humidity (%)", "Temperature (°Celcius)","Ambient Light"]
    df.columns = headers

    #turn column values into floats
    df["Humidity (%)"] = df["Humidity (%)"].astype(float)
    df["Temperature (°Celcius)"] = df["Temperature (°Celcius)"].astype(float)
    df["Ambient Light"] = df["Ambient Light"].astype(float)

    #only use data from specific date (today)
    now = datetime.now()
    today = date.today()
    todaystring = today.strftime("%B %d")
    thisday = now.day
    print(thisday)
    if thisday < 10:
        todaystring = todaystring.replace("0","")
    print("Today's date:", todaystring)
    #if you want another date, change todaystring to today's date
    df = df[df['Date'].str.contains('November 25')]

    print(df)

    #use only data from specific hour (for average temp, humidity and ambientlight numbers)
    thishour = now.strftime("%I")
    dfh = df[df['Date'].str.contains(str('{}:'.format(thishour)))]
    if now.hour > 12:
        amorpm = 'PM'
    else:
        amorpm = 'AM'
    print("Hour now:{}{}".format(thishour, amorpm))
    dfhr = dfh[dfh['Date'].str.contains(amorpm)]

    length = len(df)
    rootlen = int(math.sqrt(length))

    print('Length of dataset: {}'.format(length))
    print('Square root of dataset: {}'.format(rootlen))

    #add column titles 
    humiditydata = df.loc[:,'Humidity (%)']
    tempdata = df.loc[:,'Temperature (°Celcius)']
    ambientlightdata = df.loc[:,'Ambient Light']

    #create empty arrays to append the data from the data frame into - 
    #the function that creates the art requires the data in arrays
    humidityarray = []
    temparray = []
    ambientlightarray = []

    #append the data into the empty arrays
    for i in humiditydata:
        humidityarray.append(i)

    for i in tempdata:
        temparray.append(i)

    for i in ambientlightdata:
        ambientlightarray.append(i)

    #ensuring that datasets are square
    if length > rootlen**2: 
        difference = length - rootlen**2
        for i in range(difference): 
            humidityarray.pop()
        for i in range(difference): 
            temparray.pop()
        for i in range(difference): 
            ambientlightarray.pop()
        print('Rows to remove (difference between length and root of length): {}'.format(difference))
        print('New length of arrays: {}'.format(len(temparray)))
    
    #functions that break the arrays for each data source into a list of arrays, with length equal to the square root of the total dataset
    #this creates square datasets to feed into the art generation function
    def humiditychunky():
        humiditychunk = []
        for i in range(0, len(humidityarray), rootlen):
            humiditychunk.append(humidityarray[i:i + rootlen])
        return humiditychunk

    def tempchunky():
        tempchunk = []
        for i in range(0, len(temparray), rootlen):
            tempchunk.append(temparray[i:i + rootlen])
        return tempchunk

    def ambientlightchunky():
        ambientlightchunk = []
        for i in range(0, len(ambientlightarray), rootlen):
            ambientlightchunk.append(ambientlightarray[i:i + rootlen])
        return ambientlightchunk

    humiditychunk = humiditychunky()
    tempchunk = tempchunky()
    ambientlightchunk = ambientlightchunky()

    #equation for main pixel grid
    #play around with these factors to tweak how 
    #much each data source influences final art piece
    ambientlightfactor = 0.01
    humidityfactor = 1
    tempfactor = 1 
    fractionofambientlight = np.divide(ambientlightarray, 1/ambientlightfactor)
    fractionofhumidity = np.divide(humidityarray, 1/humidityfactor)
    fractionoftemp = np.divide(temparray, 1/tempfactor)
    humidityplustemp = np.add(fractionofhumidity,fractionoftemp)
    mainarray = np.add(humidityplustemp,fractionofambientlight)
    def mainchunky():
        mainchunk = []
        for i in range(0, len(mainarray), rootlen):
            mainchunk.append(mainarray[i:i + rootlen])
        return mainchunk

    mainchunk = mainchunky()

    #assign colour theme based on weather conditions
    def themechoose():
        #reverse this cmap to go from dark to light
        colourmap = plt.cm.get_cmap('YlGnBu')
        YlGnBureversed = colourmap.reversed()
        if detailconditions == 'few clouds':
            theme = 'viridis'
        elif detailconditions == 'scattered clouds':
            theme = 'plasma'
        elif detailconditions == 'broken clouds':
            theme = 'magma'
        elif detailconditions == 'overcast clouds':
            theme = 'copper'
        elif mainconditions == 'Rain':
            theme = 'ocean'
        elif mainconditions == 'Clear':
            theme = YlGnBureversed
        elif mainconditions == 'Mist':
            theme = 'cividis'
        elif mainconditions == 'Drizzle':
            theme = 'Bone'
        elif mainconditions == 'Thunderstorm':
            theme = 'gist_heat'
        else:
            theme = 'plasma'  
        return theme

    theme = themechoose()
    print(theme)

    #creating number pixel art for the output of hourly average onto visualisation website
    def numbergenerate():
        
        onedata = [[0,0,1,1,0,0],[0,1,1,1,0,0],[0,0,1,1,0,0],[0,0,1,1,0,0],[0,0,1,1,0,0],[0,0,1,1,0,0],[0,1,1,1,1,0]]
        twodata = [[0,1,1,1,1,0],[1,1,0,0,1,1],[0,0,0,0,1,1],[0,0,1,1,1,0],[0,1,1,0,0,0],[1,1,0,0,0,0],[1,1,1,1,1,1]]
        threedata = [[0,1,1,1,1,0],[1,1,0,0,1,1],[0,0,0,0,1,1],[0,0,1,1,1,0],[0,0,0,0,1,1],[1,1,0,0,1,1],[0,1,1,1,1,0]]
        fourdata = [[1,1,0,0,1,1],[1,1,0,0,1,1],[1,1,0,0,1,1],[1,1,0,0,1,1],[0,1,1,1,1,1],[0,0,0,0,1,1],[0,0,0,0,1,1]]
        fivedata = [[1,1,1,1,1,1],[1,1,0,0,0,0],[1,1,1,1,1,0],[0,0,0,0,1,1],[0,0,0,0,1,1],[1,1,0,0,1,1],[0,1,1,1,1,0]]
        sixdata = [[0,1,1,1,1,0],[1,1,0,0,1,1],[1,1,0,0,0,0],[1,1,1,1,1,0],[1,1,0,0,1,1],[1,1,0,0,1,1],[0,1,1,1,1,0]]
        sevendata = [[1,1,1,1,1,1],[0,0,0,0,1,1],[0,0,0,1,1,0],[0,0,1,1,0,0],[0,0,1,1,0,0],[0,0,1,1,0,0],[0,0,1,1,0,0]]
        eightdata = [[0,1,1,1,1,0],[1,1,0,0,1,1],[1,1,0,0,1,1],[0,1,1,1,1,0],[1,1,0,0,1,1],[1,1,0,0,1,1],[0,1,1,1,1,0]]
        ninedata = [[0,1,1,1,1,0],[1,1,0,0,1,1],[1,1,0,0,1,1],[0,1,1,1,1,1],[0,0,0,0,1,1],[1,1,0,0,1,1],[0,1,1,1,1,0]]
        zerodata = [[0,1,1,1,1,0],[1,1,0,0,1,1],[1,1,0,0,1,1],[1,1,0,0,1,1],[1,1,0,0,1,1],[1,1,0,0,1,1],[0,1,1,1,1,0]]

        numbersdata = [zerodata, onedata,twodata,threedata,fourdata,fivedata,sixdata,sevendata,eightdata,ninedata,zerodata]
        
        #create arrays for average hourly

        temphrdata = dfhr.loc[:,'Temperature (°Celcius)']
        humidityhrdata = dfhr.loc[:,'Humidity (%)']
        ambientlighthrdata = dfhr.loc[:,'Ambient Light']

        temphrarray = []
        humidityhrarray = []
        ambientlighthrarray = []

        for i in temphrdata:
            temphrarray.append(i)
        
        for i in humidityhrdata:
            humidityhrarray.append(i)

        for i in ambientlighthrdata:
            ambientlighthrarray.append(i)
        
        #averagetemp
        tempaverage = str((numpy.mean(temphrarray))*100)
        print(tempaverage)
        tempfirstno = int(str(tempaverage)[:1])
        tempsecondno = int(str(tempaverage)[1:2])
        tempthirdno = int(str(tempaverage)[2:3])

        tempfirstdata = numbersdata[(tempfirstno)]
        tempseconddata = numbersdata[(tempsecondno)]
        tempthirddata = numbersdata[(tempthirdno)]

        #if the temp is less than 10, place 0 at beginning
        if numpy.mean(temparray) < 10:
            ambientlightfirstdata = numbersdata[0]
            ambientlightseconddata = numbersdata[(tempfirstno)]
            ambientlightthirddata = numbersdata[(tempsecondno)]

        firsttempfig = plt.figure()
        firsttempfig.add_subplot()
        firsttempfig = plt.imshow(tempfirstdata, cmap='gray', interpolation='nearest')
        plt.axis('off')
        plt.savefig('/Users/Alex Gibson/Desktop/PORTFOLIOCODE/public/projectsites/SIOTSite/numbers/tempnumber/tempfirstno.png', bbox_inches='tight', pad_inches = 0)

        tempsecondfig = plt.figure()
        tempsecondfig.add_subplot()
        tempsecondfig = plt.imshow(tempseconddata, cmap='gray', interpolation='nearest')
        plt.axis('off')
        plt.savefig('/Users/Alex Gibson/Desktop/PORTFOLIOCODE/public/projectsites/SIOTSite/numbers/tempnumber/tempsecondno.png', bbox_inches='tight', pad_inches = 0)

        tempthirdfig = plt.figure()
        tempthirdfig.add_subplot()
        tempthirdfig = plt.imshow(tempthirddata, cmap='gray', interpolation='nearest')
        plt.axis('off')
        plt.savefig('/Users/Alex Gibson/Desktop/PORTFOLIOCODE/public/projectsites/SIOTSite/numbers/tempnumber/tempthirdno.png', bbox_inches='tight', pad_inches = 0)

        #averagehumidity
        humidityaverage = str((numpy.mean(humidityhrarray))*100)
        print(humidityaverage)
        humidityfirstno = int(str(humidityaverage)[:1])
        humiditysecondno = int(str(humidityaverage)[1:2])
        humiditythirdno = int(str(humidityaverage)[2:3])

        humidityfirstdata = numbersdata[(humidityfirstno)]
        humidityseconddata = numbersdata[(humiditysecondno)]
        humiditythirddata = numbersdata[(humiditythirdno)]

        firsthumidityfig = plt.figure()
        firsthumidityfig.add_subplot()
        firsthumidityfig = plt.imshow(humidityfirstdata, cmap='gray', interpolation='nearest')
        plt.axis('off')
        plt.savefig('/Users/Alex Gibson/Desktop/PORTFOLIOCODE/public/projectsites/SIOTSite/numbers/humiditynumber/humidityfirstno.png', bbox_inches='tight', pad_inches = 0)

        humiditysecondfig = plt.figure()
        humiditysecondfig.add_subplot()
        humiditysecondfig = plt.imshow(humidityseconddata, cmap='gray', interpolation='nearest')
        plt.axis('off')
        plt.savefig('/Users/Alex Gibson/Desktop/PORTFOLIOCODE/public/projectsites/SIOTSite/numbers/humiditynumber/humiditysecondno.png', bbox_inches='tight', pad_inches = 0)

        humiditythirdfig = plt.figure()
        humiditythirdfig.add_subplot()
        humiditythirdfig = plt.imshow(humiditythirddata, cmap='gray', interpolation='nearest')
        plt.axis('off')
        plt.savefig('/Users/Alex Gibson/Desktop/PORTFOLIOCODE/public/projectsites/SIOTSite/numbers/humiditynumber/humiditythirdno.png', bbox_inches='tight', pad_inches = 0)

        #averageambientlight
        ambientlightaverage = str((numpy.mean(ambientlighthrarray))*100)
        print(ambientlightaverage)

        #if the ambient light is less than 10, place 0s everywhere
        if int(str(ambientlightaverage)[:1]) == 0:
            ambientlightfirstno = 0
            ambientlightsecondno = 0
            ambientlightthirdno = 0
        else:
            ambientlightfirstno = int(str(ambientlightaverage)[:1])
            ambientlightsecondno = int(str(ambientlightaverage)[1:2])
            ambientlightthirdno = int(str(ambientlightaverage)[2:3])

        ambientlightfirstdata = numbersdata[(ambientlightfirstno)]
        ambientlightseconddata = numbersdata[(ambientlightsecondno)]
        ambientlightthirddata = numbersdata[(ambientlightthirdno)]

        #if the ambient light is less than 100, place 0 at beginning
        if numpy.mean(ambientlightarray) < 100:
            ambientlightfirstdata = numbersdata[0]
            ambientlightseconddata = numbersdata[(ambientlightfirstno)]
            ambientlightthirddata = numbersdata[(ambientlightsecondno)]
        
        firstambientlightfig = plt.figure()
        firstambientlightfig.add_subplot()
        firstambientlightfig = plt.imshow(ambientlightfirstdata, cmap='gray', interpolation='nearest')
        plt.axis('off')
        plt.savefig('/Users/Alex Gibson/Desktop/PORTFOLIOCODE/public/projectsites/SIOTSite/numbers/ambientlightnumber/ambientlightfirstno.png', bbox_inches='tight', pad_inches = 0)

        ambientlightsecondfig = plt.figure()
        ambientlightsecondfig.add_subplot()
        ambientlightsecondfig = plt.imshow(ambientlightseconddata, cmap='gray', interpolation='nearest')
        plt.axis('off')
        plt.savefig('/Users/Alex Gibson/Desktop/PORTFOLIOCODE/public/projectsites/SIOTSite/numbers/ambientlightnumber/ambientlightsecondno.png', bbox_inches='tight', pad_inches = 0)

        ambientlightthirdfig = plt.figure()
        ambientlightthirdfig.add_subplot()
        ambientlightthirdfig = plt.imshow(ambientlightthirddata, cmap='gray', interpolation='nearest')
        plt.axis('off')
        plt.savefig('/Users/Alex Gibson/Desktop/PORTFOLIOCODE/public/projectsites/SIOTSite/numbers/ambientlightnumber/ambientlightthirdno.png', bbox_inches='tight', pad_inches = 0)

    numbergenerate()
    #graph function creates graphs of data source against time, and formats them so they fit on the website
    def graph():
        #temperature graph
        tempgraph = plt.figure(figsize=(18,6))
        tempgraph.patch.set_facecolor('#101010')
        ax = tempgraph.add_subplot()
        tempgraph = plt.plot(temparray, color ='white',linewidth=3)
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
        plt.savefig('/Users/Alex Gibson/Desktop/PORTFOLIOCODE/public/projectsites/SIOTSite/graphs/tempgraph.png', bbox_inches='tight', pad_inches = 0)
        
        #ambient light graph
        ambientlightgraph = plt.figure(figsize=(18,6))
        ambientlightgraph.patch.set_facecolor('#101010')
        ax = ambientlightgraph.add_subplot()
        ambientlightgraph = plt.plot(ambientlightarray, color ='white',linewidth=3)
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
        plt.savefig('/Users/Alex Gibson/Desktop/PORTFOLIOCODE/public/projectsites/SIOTSite/graphs/ambientlightgraph.png', bbox_inches='tight', pad_inches = 0)

        #humidity graph
        humiditygraph = plt.figure(figsize=(18,6))
        humiditygraph.patch.set_facecolor('#101010')
        ax = humiditygraph.add_subplot()
        humiditygraph = plt.plot(humidityarray, color ='white',linewidth=3)
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
        plt.ylabel("Humidity %", fontname='Helvetica Neue')
        plt.savefig('/Users/Alex Gibson/Desktop/PORTFOLIOCODE/public/projectsites/SIOTSite/graphs/humiditygraph.png', bbox_inches='tight', pad_inches = 0)
    graph()

    #creating main pixel art figure
    pixeldata = gaussian_filter(mainchunk,2)
    pixelmain = plt.figure()
    pixelmain.add_subplot()
    pixelmain = plt.imshow(pixeldata, cmap=theme, interpolation='nearest')
    plt.axis('off')
    plt.savefig('/Users/Alex Gibson/Desktop/PORTFOLIOCODE/public/projectsites/SIOTSite/pixels/pixel.png', bbox_inches='tight', pad_inches = 0)

    #creating humidity figure
    pixeldatahumidity = gaussian_filter(humiditychunk,2)
    pixeltemp = plt.figure()
    pixeltemp.add_subplot()
    pixelmain = plt.imshow(pixeldatahumidity, cmap=theme, interpolation='nearest')
    plt.axis('off')
    plt.savefig('/Users/Alex Gibson/Desktop/PORTFOLIOCODE/public/projectsites/SIOTSite/pixels/humiditypixel.png', bbox_inches='tight', pad_inches = 0)

    #creating temp figure
    pixeldatatemp = gaussian_filter(tempchunk,2)
    pixeltemp = plt.figure()
    pixeltemp.add_subplot()
    pixelmain = plt.imshow(pixeldatatemp, cmap=theme, interpolation='nearest')
    plt.axis('off')
    plt.savefig('/Users/Alex Gibson/Desktop/PORTFOLIOCODE/public/projectsites/SIOTSite/pixels/temppixel.png', bbox_inches='tight', pad_inches = 0)

    #creating ambient light figure
    pixeldataambientlight = gaussian_filter(ambientlightchunk,2)
    pixeltemp = plt.figure()
    pixeltemp.add_subplot()
    pixelmain = plt.imshow(pixeldataambientlight, cmap=theme, interpolation='nearest')
    plt.axis('off')
    plt.savefig('/Users/Alex Gibson/Desktop/PORTFOLIOCODE/public/projectsites/SIOTSite/pixels/ambientlightpixel.png', bbox_inches='tight', pad_inches = 0)

    #accesses the operating system to deploy the website through the terminal once previous code has been run
    os.chdir("/Users/Alex Gibson/Desktop/PORTFOLIOCODE")
    subprocess.call("firebase deploy", shell=True)
    return

#list of hours that the script automatically runs at
hours = ["08:58","09:58","10:58","11:58","12:58","13:58","14:58","15:58","16:58","17:58","18:58","19:58"]

#for loop that runs the script (inside the siotscript function) at the times specified above
for i in hours:
    schedule.every().day.at(i).do(siotscript)

while True:
    schedule.run_pending()