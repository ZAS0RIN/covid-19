# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 12:53:34 2020

@author: u379834
"""
import pandas as pd
import pycountry

def import_data():
    #import data from CSSE
    confirmed = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Confirmed.csv')
    recovered = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Recovered.csv')
    deaths = pd.read_csv('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_19-covid-Deaths.csv')
    
    #combine
    confirmed['type']='confirmed'
    recovered['type']='recovered'
    deaths['type']='died'
    df= confirmed.append(recovered)
    df=df.append(deaths)
    df['Province/State']=df['Province/State'].fillna('N.A.')
    
    #reformat for graphing
    df= df.set_index(['Province/State','Country/Region','Lat','Long','type'])
    df=df.stack()
    df=df.reset_index()
    df.columns=['City','Country','Lat','Long','type','date','value']
    df['date']=pd.to_datetime(df['date'],infer_datetime_format=True)
    df=pd.pivot_table(df, index=['City','Country','Long','Lat','date'],columns='type',values='value')
    df['currently ill'] = df['confirmed'] - df['died']-df['recovered']
    df=df.stack()
    df=df.reset_index()
    df.columns=['City','Country','Long','Lat','date','type','value']
    df.to_csv('C:/Users/u379834/Documents/GitHub/Covid-19/covid-19/data.csv')
    return df

def update_country_isocodes(df):
    #use pycountry to get iso_3 codes
    countries = pd.DataFrame(df['Country'].unique())
    countries.columns=['Country']
    countries['C_Clean']=countries['Country'].replace(['Mainland China', 'Macau', 'South Korea', 'Others'],
                                                      ['China', 'China', 'Korea','Japan'])
    countries['alpha-3']= countries.apply(lambda x: (pycountry.countries.search_fuzzy(x['C_Clean'])[0]).alpha_3,axis=1)
    #lookup region data from iso_3 codes
    regions = pd.read_csv('https://raw.githubusercontent.com/lukes/ISO-3166-Countries-with-Regional-Codes/master/all/all.csv')
    countries=pd.merge(countries, regions, how='left', on='alpha-3')
    countries.to_csv('C:/Users/u379834/Documents/GitHub/Covid-19/covid-19/countrycodes.csv')
    return

#refresh data
df=import_data()
countries = update_country_isocodes(df)