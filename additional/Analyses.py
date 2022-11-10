#~ Analyses Streamlit page for THAW data

from concurrent.futures.thread import BrokenThreadPool
from numpy import int32
import streamlit as st # import streamlit so for sending outputs to app
import pandas as pd # for cleaning and analysing with data
import pymongo #for accessing data from database
from decouple import config
import plotly_express as px
import datetime as dt


### Analytics: aim open to the public eventually

# get the dataframes from main page
from THAW import incFB
from THAW import funding2

funds = funding2[['Date', 'Value', 'Funded By']]
funds['Date'] = pd.to_datetime(funds['Date'], format = '%d/%m/%Y', errors='coerce')
#funds['Value'] = funds['Value'].astype('float')

# Create a seperate dataframe containing data to be shared with the public
publicdf = incFB[['Date', 'Value', 'Recipient', 'Type', 'Delivery Method', 'Postcode']]
publicdf = publicdf[(publicdf['Recipient'] == 'Papdale') | (publicdf['Recipient'] == 'Charis') | (publicdf['Recipient'] == 'Unknown')]
publicdf['Date'] = pd.to_datetime(publicdf['Date'], format = '%d/%m/%Y', errors='coerce')


# code to correct delivery method inputs
publicdf['Delivery Method'] = publicdf['Delivery Method'].replace(dict.fromkeys(['email', 'Email'], 'E-mail'))
publicdf['Delivery Method'] = publicdf['Delivery Method'].replace(dict.fromkeys(['SMS', 'sms'], 'Text'))
publicdf['Delivery Method'] = publicdf['Delivery Method'].replace(dict.fromkeys(['Email - In Person'], 'In Person'))


# allow the user to plot and data from publicdf as a bar chart
def bar_plots(publicdf):
    x_axis_val = st.selectbox('Select data for the horizontal x-axis:', options = publicdf.columns)
    plotbar = px.bar(publicdf, x=x_axis_val, y=publicdf['Value'], template="xgridoff").update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})
    st.write('Use your cursor to select and zoom into any area on the graph.')
    st.write('Hovering over the graph will show other graph interaction options to the top right of the plot.')
    st.plotly_chart(plotbar, use_container_width=True, marker_line_width=0)

# allow the user to plot and data from publicdf as a grouped bar chart for store or voucher type

##  change x-axis options??

def grp_plots(publicdf):
    x_axis_val = st.selectbox('Select data for the horizontal x-axis:', options = publicdf[['Date', 'Value', 'Type', 'Recipient', 'Delivery Method', 'Postcode']].columns)
    col_val = st.selectbox('Select data for bar colour:', options = publicdf[['Type', 'Recipient']].columns)
    plotgrp = px.bar(publicdf, x=x_axis_val, y=publicdf['Value'], color = col_val, barmode='group', template="xgridoff").update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})
    st.write('Use your cursor to select and zoom into any area on the graph.')
    st.write('Hovering over the graph will show other graph interaction options to the top right of the plot.')
    st.plotly_chart(plotgrp, use_container_width=True )


# allow user to make a scatter plot of any data in public df
def scat_plots(publicdf):
    x_axis_val = st.selectbox('Select data for the horizontal x-axis:', options = publicdf.columns)
    y_axis_val = st.selectbox('Select data for the vertica y-axis:', options = publicdf.columns)
    plotscat = px.scatter(publicdf, x=x_axis_val, y=y_axis_val, template="xgridoff").update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})
    st.write('Use your cursor to select and zoom into any area on the graph.')
    st.write('Hovering over the graph will show other graph interaction options to the top right of the plot.')
    st.plotly_chart(plotscat, use_container_width=True)

# show the funding recived by THAW as a bar chart
def fund_plots(funds):
    x_axis_val = st.selectbox('Select data for the horizontal x-axis:', options = funds[['Funded By', 'Date']].columns)
    plotfund = px.bar(funds, x=x_axis_val, y=funds['Value'], template='xgridoff').update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})
    st.write('Use your cursor to select and zoom into any area on the graph.')
    st.write('Hovering over the graph will show other graph interaction options to the top right of the plot.')
    st.plotly_chart(plotfund, use_container_width=True)

# a line plot to show total funding received by THAW over time
totfund = funds.dropna(subset=['Value'])
totfund['Value'] = totfund['Value'].astype('float')
totfund['Value'] = totfund['Value'].astype('int32')
totIncLine = px.ecdf(totfund, x='Date',  y='Value', ecdfnorm=None,  markers=True, title="Funding Received", template="xgridoff").update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})

# a line plot to show total awards allocated by THAW over time
# create df where recipients are all clients for awards calculation
publicdf2 = incFB[['Date', 'Transaction Code', 'Value', 'Recipient', 'Type', 'Delivery Method', 'Postcode']]

publicdf2 = publicdf2[(publicdf2['Recipient'] != 'Papdale') & (publicdf2['Recipient'] != 'Charis')]
publicdf2['Date'] = pd.to_datetime(publicdf2['Date'], format = '%d/%m/%Y', errors='coerce')
# remove any rows with nan in value column as px.ecdf sees them as string as gives error
publicfun = publicdf2.dropna(subset=['Value'])
publicfun['Value'] = publicfun['Value'].astype('float')
publicfun['Value'] = publicfun['Value'].astype('int32')
publicfun['Date'] = pd.to_datetime(publicfun['Date'], format = '%d/%m/%Y', errors='coerce')
totVochLine = px.ecdf(publicfun, x='Date',  y='Value', ecdfnorm=None, markers=True, title="Funding Awarded", template="xgridoff").update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})


# create a df with award value and funde value by date so can plot on one chart
awards = publicfun[['Date','Value']]
awards['Type'] = "Awards"
funded = totfund[['Date', 'Value']]
funded['Type'] = "Funds"
both = pd.merge(awards, funded, how='outer', on=['Date', 'Value', 'Type'])
both = both.sort_values('Date')
bothplot = px.ecdf(both, x='Date',  y='Value', color = 'Type', ecdfnorm=None, markers=True, title="Funding and  Awards", template="xgridoff").update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})


def time_plots(publicdf):
    #drop all rows with nan
    publicdf = publicdf.dropna(subset=['Date'])
    # create year, month and day columns so can chart value of awards by time
    publicdf['Year']= publicdf['Date'].dt.year.astype('Int32').astype('str')
    # extract month as a number, if extract as name then graph plots out of order
    publicdf['Month']= publicdf['Date'].dt.month.astype('Int32').astype('str')
    publicdf['Day']= publicdf['Date'].dt.day.astype('Int32').astype('str')
    col_val = st.selectbox('Select data for bar colour:', options = publicdf[['Type', 'Year', 'Recipient']].columns)
    plotgrp = px.bar(publicdf, x='Month', y='Value', color = col_val, barmode='group', title= 'Funds Awarded by Month', template="xgridoff").update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})
    st.write('Use your cursor to select and zoom into any area on the graph.')
    st.write('Hovering over the graph will show other graph interaction options to the top right of the plot.')
    st.plotly_chart(plotgrp, use_container_width=True )

# create year and month columns so can chart value of awards by time
publicdf['Year']= publicdf['Date'].dt.year.astype('Int32').astype('str')
publicdf['Month']= publicdf['Date'].dt.month.astype('Int32').astype('str')
publicdf['Day']= publicdf['Date'].dt.day.astype('Int32').astype('str')
plotgrp = px.box(publicdf, x='Month', y='Value',  title="Boxplot of Total Funds Awarded by Month of the Year",template="xgridoff").update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})



####################
## Streamlit code ##
####################

#display the table selected by any user
st.header("All the Graphs")

# The following code gives anyone the option about which table to view
public = st.sidebar.selectbox('What would you like to see?', ['Total Funding and Awards', 'Funding Bar Charts', 'Award Value by Month of the Year', 'Awards Value as a Bar Plot', 'Awards Value as a Grouped Bar Chart', 'Awards Scatter Plots'])
st.subheader('\n')

def get_public(what_info_public):
    if what_info_public == 'Total Funding and Awards':
        analysis = st.plotly_chart(bothplot, use_container_width=True)
    elif what_info_public == 'Funding Bar Charts':
        analysis = fund_plots(funds)
    elif what_info_public == 'Award Value by Month of the Year':
        analysis = time_plots(publicdf), st.plotly_chart(plotgrp, use_container_width=True)
    elif what_info_public == 'Awards Value as a Bar Plot':
        analysis = bar_plots(publicdf)
    elif what_info_public == 'Awards Value as a Grouped Bar Chart':
        analysis = grp_plots(publicdf)
    else:
        analysis = scat_plots(publicdf)
    return analysis
analysis = get_public(public)

    
