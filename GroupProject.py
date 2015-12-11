# -*- coding: utf-8 -*-
"""
Created on Sat Nov 28 14:29:42 2015

@authors: Sonya Tahir, Amit Talapatra, Wendy Zhang, Wei Zheng
"""
import pandas as pd
import requests as rq
import json 
import urllib2
from bs4 import BeautifulSoup as bs
import re
import pandas as pd
import MySQLdb as mySQL
import pandas.io.sql as pdSQL

def create_link(state):
    """
    purpose: helper function create api link for FRED
    """
    query_params = {
        "api_key": "ba56d8833265bdeb2ba533cd5d901905",
        "file_type": "json",
        "observation_start": '1976-01-01',
        "observation_end": "2015-09-01",
        "series_id": state + "UR"
    }
    queries = ['{0}={1}'.format(key, query_params[key]) for key in query_params]
    qry_str = "&".join(queries)
    fed_url = "https://api.stlouisfed.org/fred/series/observations?" + qry_str
    return fed_url

def get_series(link, state):
    """
    purpose: given a link, return state unemployment rate
    """
    response = rq.get(link)
    data_dict = json.loads(response.text)
    obs = data_dict["observations"]
    obs_json = json.dumps(obs)
    df = pd.read_json(obs_json)
    df['date'] = pd.to_datetime(df['date'])    
    df = df[['date','value']]
    df.columns = ['date', state]
    df.set_index('date', inplace=True)
    return df

def get_state_ur():
    """
    purpose: get unemployment rates for 50 states
    """
    states = ["AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID",
              "IL","IN","IA","KS","KY","LA","ME","MD","MA","MI","MN","MS",
              "MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK",
              "OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV",
              "WI","WY"]
    series = []
    for state in states:
        link = create_link(state)
        series.append(get_series(link, state))
    all_states = series[0]
    for ser in series[1:]:
        all_states = all_states.merge(ser, right_index=True, left_index=True) 
    return all_states

def state_ur_annually(all_states):
     """
    purpose: calculate annual rates
    """
    all_states.reset_index(level=0, inplace=True)
    all_states['date'] = all_states['date'].astype(str)
    all_states['date'] = all_states['date'].str[:4]
    all_states.rename(columns={'date': 'year'}, inplace=True)
    all_states = all_states.groupby('year').mean()  
    return all_states

def state_ur_monthly():
    """
    purpose: transform data for R mapping codes
    """
    states = ["AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID",
              "IL","IN","IA","KS","KY","LA","ME","MD","MA","MI","MN","MS",
              "MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK",
              "OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV",
              "WI","WY"]
    series = []
    for state in states:
        link = create_link(state)
        series.append(get_series(link, state))
    all_states = series[0]
    for ser in series[1:]:
        all_states = all_states.merge(ser, right_index=True, left_index=True)
    all_states_long = all_states.stack().reset_index()
    all_states_long.columns = ['Date', 'State', 'UR']
    us_state_abbrev = {
            'Alabama': 'AL',
            'Alaska': 'AK',
            'Arizona': 'AZ',
            'Arkansas': 'AR',
            'California': 'CA',
            'Colorado': 'CO',
            'Connecticut': 'CT',
            'Delaware': 'DE',
            'Florida': 'FL',
            'Georgia': 'GA',
            'Hawaii': 'HI',
            'Idaho': 'ID',
            'Illinois': 'IL',
            'Indiana': 'IN',
            'Iowa': 'IA',
            'Kansas': 'KS',
            'Kentucky': 'KY',
            'Louisiana': 'LA',
            'Maine': 'ME',
            'Maryland': 'MD',
            'Massachusetts': 'MA',
            'Michigan': 'MI',
            'Minnesota': 'MN',
            'Mississippi': 'MS',
            'Missouri': 'MO',
            'Montana': 'MT',
            'Nebraska': 'NE',
            'Nevada': 'NV',
            'New Hampshire': 'NH',
            'New Jersey': 'NJ',
            'New Mexico': 'NM',
            'New York': 'NY',
            'North Carolina': 'NC',
            'North Dakota': 'ND',
            'Ohio': 'OH',
            'Oklahoma': 'OK',
            'Oregon': 'OR',
            'Pennsylvania': 'PA',
            'Rhode Island': 'RI',
            'South Carolina': 'SC',
            'South Dakota': 'SD',
            'Tennessee': 'TN',
            'Texas': 'TX',
            'Utah': 'UT',
            'Vermont': 'VT',
            'Virginia': 'VA',
            'Washington': 'WA',
            'West Virginia': 'WV',
            'Wisconsin': 'WI',
            'Wyoming': 'WY',
        }
    us_abbrev_state = {value: key.lower() for key, value in us_state_abbrev.iteritems()}
    all_states_long['StateName'] = all_states_long['State'].map(us_abbrev_state)
    return all_states_long

# Scrapes US GDP Data from "http://www.multpl.com/us-gdp/table/by-year" and
# returns a pandas dataframe
def get_US_GDP():
#   Pulls year and GDP data from table at link
    USGDPDict = {}
    USGDPLink = 'http://www.multpl.com/us-gdp/table/by-year'
    html = urllib2.urlopen(USGDPLink).read()
    soup = bs(html)
    allYears = soup.findAll('td', { "class" : "left" })
    allGDPs = soup.findAll('td', { "class" : "right" })
#   Isolates year and GDP data and stores it in a dictionary 
    for i in range(0,len(allYears)):
        allYears[i] = allYears[i].text.strip()
        allGDPs[i] = allGDPs[i].text.strip()
        year = re.split(r'\s*', str(allYears[i]))
        year = year[2]
        GDP = re.split(r'\s*', str(allGDPs[i]))
        GDP = GDP[0]
        USGDPDict[year] = GDP
#   Converts dictionary to pandas dataframe
    USGDPdf = pd.DataFrame(USGDPDict.items(), columns=['Year', 'US_GDP'])
    USGDPdf = USGDPdf.sort('Year')
    USGDPdf = USGDPdf.reset_index(drop=True)
    return USGDPdf

def df_to_mysql(dbName, tableName, df):
    #write to mysql
    conn = mySQL.connect(host='localhost', user='root', passwd='root')
    cursor = conn.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS " + dbName + ";")      
    conn = mySQL.connect(host='localhost', user='root', passwd='root', db=dbName)
    df.to_sql(tableName, conn, flavor='mysql', if_exists='replace', index=False)
    cursor = conn.cursor()
    cursor.execute(' USE %s; ' % (dbName) ) 
##   UNCOMMENT TO SEE SQL TABLE DATA
#    myDataFrame = pdSQL.read_sql('SELECT * FROM %s' % (tableName), conn)
#    print myDataFrame
    conn.close()

def mysql_to_df(dbName, tableName):
    #read mysql
    conn = mySQL.connect(host='localhost', user='root', passwd='root', db=dbName)
    df = pd.read_sql('SELECT * FROM %s;' % (tableName), con=conn)  
    return df
    conn.close()

def main():
    # main function for running the program
    stateURdf = get_state_ur()
    USGDPdf = get_US_GDP()
    
    # FORMAT STATE DATA INTO ANNUAL AND MONTHLY DATASETS
    allStatesAnnually = state_ur_annually(stateURdf)
    allStatesMonthly = state_ur_monthly()
    
    # STORE DATA AS LOCAL CSV FILES TO USE FOR SHINY APP
    allStatesAnnually.to_csv('allStatesAnnually.csv')
    allStatesMonthly.to_csv('allStatesMonthly.csv')
    USGDPdf.to_csv('USGDP.csv')
    
    # SEND DATA TO SQL
    df_to_mysql('GroupProject', 'stateURAnnually', allStatesAnnually)
    df_to_mysql('GroupProject', 'stateURMonthly', allStatesMonthly)
    df_to_mysql('GroupProject', 'USGDPData', USGDPdf)
    
    # GET DATA FROM SQL AS DATAFRAMES
    allStatesAnnually = mysql_to_df('GroupProject', 'stateURAnnually')
    allStatesMonthly = mysql_to_df('GroupProject', 'stateURMonthly')
    USGDPdf = mysql_to_df('GroupProject', 'USGDPData')
    
    print allStatesAnnually
    print allStatesMonthly
    print USGDPdf
    print "The data has been saved locally as csv files, and has been saved to the SQL database."
    
if __name__ == "__main__":
    main()