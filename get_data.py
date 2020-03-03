# -*- coding: utf-8 -*-
"""
Created on Mon Mar  2 10:24:34 2020

@author: u379834
"""

import pandas as pd
import plotly.express as px
import plotly.offline as po
import pycountry
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
from datetime import datetime
import itertools

app = dash.Dash()
server = app.server

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
    df.to_pickle('C:/Users/u379834/Documents/GitHub/Covid-19/data.pkl')
    return

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
    countries.to_pickle('C:/Users/u379834/Documents/GitHub/Covid-19/countrycodes.pkl')
    return

#refresh data
#df=import_data()
#countries = update_country_isocodes(df)

#read in saved data and merge
df=pd.read_pickle('C:/Users/u379834/Documents/GitHub/Covid-19/data.pkl')
countries = pd.read_pickle('C:/Users/u379834/Documents/GitHub/Covid-19/countrycodes.pkl')
df=pd.merge(df, countries, how='left', on='Country')
df['date']=pd.to_datetime(df['date'])
df['year']=df['date'].dt.year
df['month']=df['date'].dt.month
df['day']=df['date'].dt.day
df['yy/mm/dd']=df['year'].astype(str) + '/' + df['month'].astype(str) + '/' + df['day'].astype(str)

#lists for use in dropdowns
country_list = countries['C_Clean'].unique()
country_list=country_list.tolist()
country_list.sort()

type_list= df['type'].unique()
type_list=type_list.tolist()

date_list=df['date'].drop_duplicates()
date_list=pd.DataFrame(date_list)

region_list=df['region'].unique()
region_list=region_list.tolist()
region_list.sort()


dm=df['date'].drop_duplicates()[0::7]#every 7nth date
dm=dm.tolist()
date_mark = {i.strftime('%m/%d/%Y'):i for i in dm} 



#TESTING ***********************************************************************************************

#LAYOUT**************************************************************************************************
app.layout = html.Div(dcc.Tabs(id="tabs", children=[
    dcc.Tab(label='Country View', children=[
        dcc.Dropdown(id='countries', options=[dict(label=i,value=i) for i in country_list ],value=country_list, multi=True ),
        dcc.Graph(id='country_view')
        ]),
    dcc.Tab(label='Global View', children=[
        dcc.Dropdown(id='g_region', options=[dict(label=i,value=i) for i in region_list ],value=region_list, multi=True ),
        dcc.Dropdown(id='g_type', options=[dict(label=i,value=i) for i in type_list ],value='confirmed'),
        #dcc.Slider(id='g_date',min=min(df['date']), max=max(df['date']), value=max(df['date']), marks=date_mark),
         dcc.Dropdown(id='g_date', options=[dict(label=i.strftime('%m/%d/%Y'),value=i) for i in dm ],value=max(df['date'])),
        html.Div(dcc.Graph(id='global_view'))
        ])      
]))


#FUNCTIONS AND CALLBACKS**********************************************************************************************************

@app.callback(
    Output(component_id='country_view', component_property='figure'),
    [dash.dependencies.Input('countries', 'value')])
def country_view(g_country):
    #graph country over time
    dfc=df[df['Country'].isin(g_country)]
    dfc=pd.pivot_table(dfc,index=['type','date'],values='value',aggfunc='sum')
    dfc=dfc.reset_index()
    fig = px.line(dfc,x='date',y='value',color='type')
    fig.update_layout(title= ', '.join(g_country))
    return fig

@app.callback(
    Output(component_id='global_view', component_property='figure'),
    [dash.dependencies.Input('g_region', 'value'),
     dash.dependencies.Input('g_type', 'value'),
     dash.dependencies.Input('g_date', 'value')])
def global_view(g_region,g_type,g_date):
    dfg=df[df['date']==g_date]
    dfg=dfg[dfg['type']==g_type]
    dfg=dfg[dfg['region'].isin(g_region)]
    dfg=pd.pivot_table(dfg,index=['C_Clean','alpha-3'], values='value',aggfunc='sum')
    dfg=dfg.reset_index()
    dfg.columns=['Country','CCode','cases']
    fig=px.choropleth(dfg,locations='CCode',color='cases',hover_name='Country',
                      color_continuous_scale=px.colors.sequential.Plasma,
                      width=1600, height=800)
    fig.update_layout(title=g_date)
    return fig

if __name__ == '__main__':
    #app.run_server(host='0.0.0.0', port=8049)
    app.run_server(debug=False, threaded=True)