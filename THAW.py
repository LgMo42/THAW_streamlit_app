## Home/main page for data loading and cleaning and charts

import streamlit as st # import streamlit so for sending outputs to app
import pandas as pd # for cleaning and analysing with data
import pymongo #for accessing data from database
from decouple import config
import plotly_express as px
import datetime as dt

## User sees

st.header('Welcome to THAW Data')

st.write('These pages contain data regarding the funds THAW has procured to assist vunerable residents in Orkney with food and electicity.')
st.write('\nPlease choose which page you would like to view from the menu on the left side of the page.')

# list of funding sources for creating funding df
funders = ['OICNew', 'Foodbank', 'OICemergency']


#load data from MongoDB from https://thedatafrog.com/en/articles/mongodb-python-pandas/
# get heroku config vars
mongo = config('DATA')
# use HEROKU Config Vars to access the link for loading data
 
# Initialize connection.
# Uses st.experimental_singleton to only run once.
@st.experimental_singleton
def init_connection():
    return pymongo.MongoClient(mongo)
client = init_connection()

# create a connection to the wallet collection
wallet = client.THAW.wallet

# create a connection to the funds collection
funding = client.THAW.funds

# create connection to the transactions collection 
trans = client.THAW.transactions



############################################################

###  Analytics: aim to be open to the public eventually  ###

############################################################


mongo = config('DATA')

# Pull data from the transaction collection
# Uses st.experimental_memo to only rerun when the query changes or after 10 min.
@st.experimental_memo(ttl=6)
def get_trans():
    db = client.THAW.transactions.find()
    trans_items = list(db)  # make hashable for st.experimental_memo
    transactions = pd.DataFrame(trans_items)
    #transactions = transactions.drop('_id', axis=1)
    transactions['Admin Cost'] = 0.0
    return transactions

transactions = get_trans()

# # Create a seperate dataframe containing data to be shared with the public
# publicdf = transactions[['Date', 'Value', 'Recipient', 'Type', 'Delivery Method', 'Postcode']]
# # NB: postcode will have to be removed or edited if sharing this with the public
# publicdf = publicdf[(publicdf['Recipient'] == 'Papdale') | (publicdf['Recipient'] == 'RGU') | (publicdf['Recipient'] == 'Unknown')]
# publicdf['Date'] = pd.to_datetime(publicdf['Date'], format = '%d/%m/%Y', errors='coerce')

# ## create a funds dataframe
# # first extract columns needed 
# funds = transactions[['Date', 'Value', 'Sender']]
# funds = funds.rename(columns={'Sender':'Funded By'})
# # filter for funding sources in funders list above
# funds = funds[funds['Funded By'].isin(funders)]


# # allow the user to plot and data from publicdf as a bar chart
# def bar_plots(publicdf):
#     # use all column headers from publicdf as options for the x-axis
#     x_axis_val = st.selectbox('Select data for the horizontal x-axis:', options = publicdf.columns)
#     # plot a bar chat with y-axis to be the 'Value' column from publicdf
#     plotbar = px.bar(publicdf, x=x_axis_val, y=publicdf['Value'], template="xgridoff").update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})
#     st.write('Use your cursor to select and zoom into any area on the graph.')
#     # add some directions for a user exploring the chart
#     st.write('Hovering over the graph will show other graph interaction options to the top right of the plot.')
#     # display the chart in the streamlit app
#     st.plotly_chart(plotbar, use_container_width=True, marker_line_width=0)

# # allow the user to plot and data from publicdf as a grouped bar chart for store or voucher type
# def grp_plots(publicdf):
#     # use selected column headers from publicdf as options for the x-axis
#     x_axis_val = st.selectbox('Select data for the horizontal x-axis:', options = publicdf[['Date', 'Value', 'Type', 'Recipient', 'Delivery Method', 'Postcode']].columns)
#     # use selected column headers from publicdf as options for how the bars are grouped
#     col_val = st.selectbox('Select data for bar colour:', options = publicdf[['Type', 'Recipient']].columns)
#     # plot a grouped bar chat with y-axis to be the 'Value' column from publicdf
#     plotgrp = px.bar(publicdf, x=x_axis_val, y=publicdf['Value'], color = col_val, barmode='group', template="xgridoff").update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})
#     # add some directions for a user exploring the chart
#     st.write('Use your cursor to select and zoom into any area on the graph.')
#     st.write('Hovering over the graph will show other graph interaction options to the top right of the plot.')
#     # display the chart in the streamlit app
#     st.plotly_chart(plotgrp, use_container_width=True )


# # allow user to make a scatter plot of any data in public df
# def scat_plots(publicdf):
#     # use all column headers from publicdf as options for the x-axis
#     x_axis_val = st.selectbox('Select data for the horizontal x-axis:', options = publicdf.columns)
#     # use all column headers from publicdf as options for the y-axis
#     y_axis_val = st.selectbox('Select data for the vertica y-axis:', options = publicdf.columns)
#     # plot a scatter chart with x-axis and y-axis  defined by user selections
#     plotscat = px.scatter(publicdf, x=x_axis_val, y=y_axis_val, template="xgridoff").update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})
#     # add some directions for a user exploring the chart
#     st.write('Use your cursor to select and zoom into any area on the graph.')
#     st.write('Hovering over the graph will show other graph interaction options to the top right of the plot.')
#     # display the chart in the streamlit app
#     st.plotly_chart(plotscat, use_container_width=True)

# # show the funding recived by THAW as a bar chart
# def fund_plots(funds):
#     # use selected column headers from funds as options for the x-axis
#     x_axis_val = st.selectbox('Select data for the horizontal x-axis:', options = funds[['Funded By', 'Date']].columns)
#     # plot a bar chart with with y-axis to be the 'Value' column from funds
#     plotfund = px.bar(funds, x=x_axis_val, y=funds['Value'], template='xgridoff').update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})
#     # add some directions for a user exploring the chart
#     st.write('Use your cursor to select and zoom into any area on the graph.')
#     st.write('Hovering over the graph will show other graph interaction options to the top right of the plot.')
#     # display the chart in the streamlit app
#     st.plotly_chart(plotfund, use_container_width=True)

# ## create a graph to show cumulative fundinf awarded using funds df
# # remove any rows with NaN in the 'Value' column of the 'funds' df
# totfund = funds.dropna(subset=['Value'])
# # have to set as float then integer due to a streamlit bug
# totfund['Value'] = totfund['Value'].astype('float')
# totfund['Value'] = totfund['Value'].astype('int32')
# # create a line chart of funds 
# totIncLine = px.ecdf(totfund, x='Date',  y='Value', ecdfnorm=None,  markers=True, title="Funding Awarded", template="xgridoff").update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})


# # create a new transactions df where recipients are all clients for awards calculation
# publicdf2 = transactions
# # remove rows where a store is a recipient
# publicdf2 = publicdf2[(publicdf2['Recipient'] != 'Papdale') & (publicdf2['Recipient'] != 'RGU')]
# # change date to datetime
# publicdf2['Date'] = pd.to_datetime(publicdf2['Date'], format = '%d/%m/%Y', errors='coerce')

# # remove any rows with nan in 'Value' column of the 'funds' as px.ecdf sees them as string and cannot plot them
# publicfun = publicdf2.dropna(subset=['Value'])
# publicfun['Value'] = publicfun['Value'].astype('float')
# publicfun['Value'] = publicfun['Value'].astype('int32')
# publicfun['Date'] = pd.to_datetime(publicfun['Date'], format = '%d/%m/%Y', errors='coerce')
# # create a line chart of funds awarded
# totVochLine = px.ecdf(publicfun, x='Date',  y='Value', ecdfnorm=None, markers=True, title="Funding Awarded", template="xgridoff").update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})


# def time_plots(publicdf):
#     #drop all rows with nan
#     publicdf = publicdf.dropna(subset=['Date'])
#     # create year, month and day columns so can chart value of awards by time
#     publicdf['Year']= publicdf['Date'].dt.year.astype('Int32').astype('str')
#     # extract month as a number, if extract as name then graph plots out of order
#     publicdf['Month']= publicdf['Date'].dt.month.astype('Int32').astype('str')
#     publicdf['Day']= publicdf['Date'].dt.day.astype('Int32').astype('str')
#     col_val = st.selectbox('Select data for bar colour:', options = publicdf[['Type', 'Year', 'Recipient']].columns)
#     plotgrp = px.bar(publicdf, x='Month', y='Value', color = col_val, barmode='group', title= 'Funds Awarded by Month', template="xgridoff").update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})
#     # add some directions for a user exploring the chart
#     st.write('Use your cursor to select and zoom into any area on the graph.')
#     st.write('Hovering over the graph will show other graph interaction options to the top right of the plot.')
#     # display the chart in the streamlit app
#     st.plotly_chart(plotgrp, use_container_width=True )

# # create year and month columns so can chart value of awards by time
# publicdf['Year']= publicdf['Date'].dt.year.astype('Int32').astype('str')
# publicdf['Month']= publicdf['Date'].dt.month.astype('Int32').astype('str')
# publicdf['Day']= publicdf['Date'].dt.day.astype('Int32').astype('str')
# plotgrp = px.box(publicdf, x='Month', y='Value',  title="Boxplot of Total Funds Awarded by Month of the Year",template="xgridoff").update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})



# ###################
# # Streamlit code ##
# ###################

# # display the table selected by any user
# st.header("All the Graphs")

# # The following code gives the user the option about which chart to view
# public = st.sidebar.selectbox('What would you like to see?', ['Total Awards', 'Funding Bar Charts', 'Award Spent by Month of the Year', 'Awards Spent as a Bar Plot', 'Awards Spent as a Grouped Bar Chart', 'Awards Scatter Plots'])
# st.subheader('\n')

# def get_public(what_info_public):
#     if what_info_public == 'Total Awards':
#         analysis = st.plotly_chart(totIncLine, use_container_width=True)
#     elif what_info_public == 'Funding Bar Charts':
#         analysis = fund_plots(funds)
#     elif what_info_public == 'Award Spent by Month of the Year':
#         analysis = time_plots(publicdf), st.plotly_chart(plotgrp, use_container_width=True)
#     elif what_info_public == 'Awards Spent as a Bar Plot':
#         analysis = bar_plots(publicdf)
#     elif what_info_public == 'Awards Spent as a Grouped Bar Chart':
#         analysis = grp_plots(publicdf)
#     else:
#         analysis = scat_plots(publicdf)
#     return analysis
# analysis = get_public(public)

    
