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


# get data from papdale collection
pap = client.THAW.papdale
cursor = pap.find()
# convert curso objects to list
all = list(cursor)
# convert list to dataframe
papdale = pd.DataFrame(all) 
# remove MongoDB document id
papdale = papdale.drop('_id', axis=1)
# rename the voucher code to transaction code to match transaction collection schema
papdale = papdale.rename(columns={'Voucher Code':'Transaction Code'})

# extract funding info from the papdale dataframe
papFun = papdale[['Date Allocated',  'Value', 'Funded By']]
papFun = papFun.rename(columns={'Date Allocated':'Date'})

# create new df where Funding source is the sender and client is the recipient
pap1 = papdale[['Transaction Code', 'Date Allocated',  'Value', 'URN', 'Type', 'Funded By']]
pap1 = pap1.rename(columns={'Date Allocated':'Date', 'URN':'Recipient','Funded By':'Sender'})

# create 2nd df where client is the sender and the Papdale is the recipient
pap2 = papdale[['Transaction Code', 'Value', 'URN', 'Type', 'Date Allocated', 'Store']]
# create a new transaction code based on the original transaction code
pap2['Transaction Code'] = pap2['Transaction Code'] + '_1'
pap2 = pap2.rename(columns={'Date Allocated':'Date', 'Store':'Recipient','URN':'Sender'})

# merge the 2 df to create a df to replicate df that will be created from the 'transactions' collection
newPap = pd.merge(pap1, pap2, how='outer', on=['Transaction Code', 'Value', 'Sender', 'Type', 'Date', 'Recipient'])
# add a column for admin cost
newPap['Admin Cost'] = 0.0
# add the delivery method
newPap['Delivery Method'] = 'SMS'


# load Charis data
char = client.THAW.charis
cursor = char.find()
# convert cursor object to list
all = list(cursor)
# convert list to dataframe
charis = pd.DataFrame(all)
# remove MongoDB document id 
charis = charis.drop('_id', axis=1)
# rename chris field names to match 'transactions' collection field names
charis = charis.rename(columns={'Cost':'Value', 'Deliver To Postcode': 'Postcode', 'Payment Id':'Transaction Code'})
# split date in to time and date fields
charis[['Date', 'Time']] = charis['Payment Date'].str.split(' ', 1, expand=True)


# extract type using the first word as a descriptor
charis[['Type', 'Rest']] = charis['Product Name'].str.split(' ', 1, expand=True)
# extract the last word from of the 'Rest' column to get the delivery Method
charis['Delivery Method'] = (charis['Rest'].str.split().str[-1:])

# remove unnecessary punctuation from 'Delivery Type' colunms
charis['Delivery Method'] = charis['Delivery Method'].astype(str).str.replace('[', '', regex=True).str.replace(']', '', regex=True)
charis['Delivery Method'] = charis['Delivery Method'].astype(str).str.replace("'", '',  regex=True)

## extract funding info from the charis dataframe
# extract rows that relate to THAW payments into Charis account as a new df
charisFun = charis[charis['Type'] == 'Shop']
# extract columns relating to payment amount and date
charisFun = charisFun[['Credit', 'Date']]
# add a column for the funding source
charisFun['Funded By'] = 'CharisOIC'
charisFun = charisFun.rename(columns={'Credit':'Value'})

# remove rows that do not relate to client transactions for the charis df
charis = charis[(charis['Type'] != 'Starting') & (charis['Type'] != 'Shop') & (charis['Type'] != 'End')]

# aggragate 'Admin Fee' and 'VAT' into one column
charis['Admin Cost'] = charis['Admin Fee'].astype('float') + charis['VAT'].astype('float')
# remove 'Admin Fee' and 'VAT' into one columns
charis = charis.drop(['Admin Fee','VAT'], axis=1)
# change Tesco to food to repesent type of voucher allocated
charis['Type'] = charis['Type'].replace(dict.fromkeys(['Tesco'], 'Food'))

# extracting the relevant columns for creating a useful df
charis = charis[['Transaction Code', 'Date','Time', 'Value', 'URN', 'Type', 'Delivery Method', 'Postcode','Admin Cost']]
# add a store column as charis does not have one on their csv files
charis['Store'] = 'Charis'

# for Type in charis:  print(charis['Type'].unique())  
# gives 'Tesco' 'Paypoint' 'Post' 'PayPoint' so convert 'Paypoint' 'Post' 'PayPoint' to 'Electricity'
charis['Type'] = charis['Type'].replace(dict.fromkeys(['Paypoint','PayPoint','Post'],'Electricity'))

# create a df where funding source is the sender and the client is the recipient
# extracting the relevant columns
cha1 = charis[['Transaction Code', 'Date', 'Time', 'Value', 'URN', 'Type', 'Delivery Method', 'Postcode','Admin Cost']]
cha1 = cha1.rename(columns={'URN':'Recipient'})
# create the sender column as funding source is not rcorded on the Charis csv files 
cha1['Sender'] = 'CharisOIC'

# create a 2nd df where client is the sender and Chair is the recipient
cha2 = charis[['Transaction Code', 'Date', 'Time', 'Value', 'URN', 'Type', 'Delivery Method', 'Postcode', 'Admin Cost', 'Store']]
# create a new transaction code based on the original transaction code code
cha2['Transaction Code'] = cha2['Transaction Code'] + '_1'
cha2 = cha2.rename(columns={'Store':'Recipient','URN':'Sender'})

# merge the 2 df to create a df to replicate df that will be created from the 'transactions' collection 
newCha = pd.merge(cha1, cha2, how='outer', on=['Transaction Code', 'Date', 'Time', 'Value', 'Recipient', 'Type', 'Delivery Method' , 'Postcode', 'Admin Cost' ,'Sender'])

# load FuleBank data
fuel = client.THAW.fuelbank
#print(char.find_one())
cursor = fuel.find()
all = list(cursor)
#convert to dataframe
fuelbank = pd.DataFrame(all)
#remove MongoDB document id 
fuelbank = fuelbank.drop('_id', axis=1)

# rename fuelbank field names to match 'transactions' collection field names
fuelbank = fuelbank.rename(columns={'Date Form Submitted' : 'Date' , 'Award Value' : 'Value' , 'Unique Reference Number' : 'Transaction Code', 'How is the client receiving their code' : 'Delivery Method'})

# Add missing column for data analysis purposes
fuelbank['Funded By'] = 'FuelBank'
fuelbank['Type'] = 'Electricity'
fuelbank['Admin Cost'] = 0.0

# extract funding info from the fuelbank dataframe
fuelFun = fuelbank[['Date',  'Value', 'Funded By']]

# create a df where funding source is the sender and the client is the recipient
fuelbank = fuelbank.rename(columns={'Funded By': 'Sender', 'URN' : 'Recipient'})
fuelbank = fuelbank[['Transaction Code', 'Date', 'Value',  'Recipient', 'Type', 'Sender', 'Delivery Method', 'Postcode', 'Admin Cost']]

# there is no 2nd df for fuelbank as the client to store transactions are unknown

#merge papdale and charis transformed dfs to crease a df of transactions from THAW allocated funding
historic = pd.merge(newPap, newCha, how='outer', on=['Transaction Code', 'Date', 'Value', 'Recipient', 'Type', 'Sender', 'Admin Cost','Delivery Method'])

# merge the fulebank df as well to create a df with all funding received by residents due to THAW assistance
incFB = pd.merge(historic, fuelbank, how='outer', on=['Transaction Code', 'Date', 'Value',  'Recipient', 'Type', 'Sender', 'Admin Cost','Delivery Method', 'Postcode'])

# merge the 3 funding dfs to create on single funding df
funding = pd.merge(papFun, charisFun, how='outer', on=['Date', 'Value', 'Funded By'])
funding2 = pd.merge(funding, fuelFun, how='outer', on=['Date', 'Value', 'Funded By'])
funding['Value'] = funding['Value'].astype('float')


# create a connection to the wallet collection
wallet = client.THAW.wallet

# create a connection to the funds collection
funding = client.THAW.funds

# create connection to the transactions collection 
trans = client.THAW.transactions



############################################################

###  Analytics: aim to be open to the public eventually  ###

############################################################

# make a new dataframes so can transform them for anaylses

funds = funding2[['Date', 'Value', 'Funded By']]
funds['Date'] = pd.to_datetime(funds['Date'], format = '%d/%m/%Y', errors='coerce')


# Create a seperate dataframe containing data to be shared with the public
publicdf = incFB[['Date', 'Value', 'Recipient', 'Type', 'Delivery Method', 'Postcode']]
# NB: postcode will have to be removed or edited if sharing this with the public
publicdf = publicdf[(publicdf['Recipient'] == 'Papdale') | (publicdf['Recipient'] == 'Charis') | (publicdf['Recipient'] == 'Unknown')]
publicdf['Date'] = pd.to_datetime(publicdf['Date'], format = '%d/%m/%Y', errors='coerce')


# code to standardise delivery method text
publicdf['Delivery Method'] = publicdf['Delivery Method'].replace(dict.fromkeys(['email', 'Email'], 'E-mail'))
publicdf['Delivery Method'] = publicdf['Delivery Method'].replace(dict.fromkeys(['SMS', 'sms'], 'Text'))
publicdf['Delivery Method'] = publicdf['Delivery Method'].replace(dict.fromkeys(['Email - In Person'], 'In Person'))

# allow the user to plot and data from publicdf as a bar chart
def bar_plots(publicdf):
    # use all column headers from publicdf as options for the x-axis
    x_axis_val = st.selectbox('Select data for the horizontal x-axis:', options = publicdf.columns)
    # plot a bar chat with y-axis to be the 'Value' column from publicdf
    plotbar = px.bar(publicdf, x=x_axis_val, y=publicdf['Value'], template="xgridoff").update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})
    # add some directions for a user exploring the chart
    st.write('Use your cursor to select and zoom into any area on the graph.')
    st.write('Hovering over the graph will show other graph interaction options to the top right of the plot.')
    # display the chart in the streamlit app
    st.plotly_chart(plotbar, use_container_width=True, marker_line_width=0)

# allow the user to plot and data from publicdf as a grouped bar chart for store or voucher type
def grp_plots(publicdf):
    # use selected column headers from publicdf as options for the x-axis
    x_axis_val = st.selectbox('Select data for the horizontal x-axis:', options = publicdf[['Date', 'Value', 'Type', 'Recipient', 'Delivery Method', 'Postcode']].columns)
    # use selected column headers from publicdf as options for how the bars are grouped
    col_val = st.selectbox('Select data for bar colour:', options = publicdf[['Type', 'Recipient']].columns)
    # plot a grouped bar chat with y-axis to be the 'Value' column from publicdf
    plotgrp = px.bar(publicdf, x=x_axis_val, y=publicdf['Value'], color = col_val, barmode='group', template="xgridoff").update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})
    # add some directions for a user exploring the chart
    st.write('Use your cursor to select and zoom into any area on the graph.')
    st.write('Hovering over the graph will show other graph interaction options to the top right of the plot.')
    # display the chart in the streamlit app
    st.plotly_chart(plotgrp, use_container_width=True )


# allow the user to make a scatter plot of any data in public df
def scat_plots(publicdf):
    # use all column headers from publicdf as options for the x-axis
    x_axis_val = st.selectbox('Select data for the horizontal x-axis:', options = publicdf.columns)
    # use all column headers from publicdf as options for the y-axis
    y_axis_val = st.selectbox('Select data for the vertica y-axis:', options = publicdf.columns)
    # plot a scatter chart with x-axis and y-axis  defined by user selections
    plotscat = px.scatter(publicdf, x=x_axis_val, y=y_axis_val, template="xgridoff").update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})
    # add some directions for a user exploring the chart
    st.write('Use your cursor to select and zoom into any area on the graph.')
    st.write('Hovering over the graph will show other graph interaction options to the top right of the plot.')
    # display the chart in the streamlit app
    st.plotly_chart(plotscat, use_container_width=True)


# show the funding recived by THAW as a bar chart
def fund_plots(funds):
    # use selected column headers from funds as options for the x-axis
    x_axis_val = st.selectbox('Select data for the horizontal x-axis:', options = funds[['Funded By', 'Date']].columns)
    # plot a bar chart with with y-axis to be the 'Value' column from funds
    plotfund = px.bar(funds, x=x_axis_val, y=funds['Value'], template='xgridoff').update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})
    # add some directions for a user exploring the chart
    st.write('Use your cursor to select and zoom into any area on the graph.')
    st.write('Hovering over the graph will show other graph interaction options to the top right of the plot.')
    # display the chart in the streamlit app
    st.plotly_chart(plotfund, use_container_width=True)

# remove any rows with NaN in the 'Value' column of the 'funds' df
totfund = funds.dropna(subset=['Value'])
# have to set as float then integer due to a streamlit bug
totfund['Value'] = totfund['Value'].astype('float')
totfund['Value'] = totfund['Value'].astype('int32')
# create a line chart of income recieved
totIncLine = px.ecdf(totfund, x='Date',  y='Value', ecdfnorm=None,  markers=True, title="Funding Received", template="xgridoff").update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})


# create df where recipients are all clients for awards calculation
publicdf2 = incFB[['Date', 'Transaction Code', 'Value', 'Recipient', 'Type', 'Delivery Method', 'Postcode']]
# remove the rows where recipients are stores
publicdf2 = publicdf2[(publicdf2['Recipient'] != 'Papdale') & (publicdf2['Recipient'] != 'Charis')]
# change date to datetime
publicdf2['Date'] = pd.to_datetime(publicdf2['Date'], format = '%d/%m/%Y', errors='coerce')
# remove any rows with NaN in value column as px.ecdf sees them as string and cannot plot them
publicfun = publicdf2.dropna(subset=['Value'])
publicfun['Value'] = publicfun['Value'].astype('float')
publicfun['Value'] = publicfun['Value'].astype('int32')
publicfun['Date'] = pd.to_datetime(publicfun['Date'], format = '%d/%m/%Y', errors='coerce')
totVochLine = px.ecdf(publicfun, x='Date',  y='Value', ecdfnorm=None, markers=True, title="Funding Awarded", template="xgridoff").update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})


## create a df with award values and fund values by date so can plot on one chart
# extract 'Date' and 'Value' for the publicfun df
awards = publicfun[['Date','Value']]
# set the 'Type' to be 'Awards' to denote funds allocated to clients
awards['Type'] = "Awards"
# extract 'Date' and 'Value' for the totfund df
funded = totfund[['Date', 'Value']]
# set the 'Type' to be 'Funds' to denote funds donated to THAW
funded['Type'] = "Funds"
# merge the 2 extracted dfs
both = pd.merge(awards, funded, how='outer', on=['Date', 'Value', 'Type'])
#sort the merged df by date
both = both.sort_values('Date')
#plot as a cumuliative line chart with colour set to type so will have 1 line ofr funding and 1 for awards 
bothplot = px.ecdf(both, x='Date',  y='Value', color = 'Type', ecdfnorm=None, markers=True, title="Funding and  Awards", template="xgridoff").update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})


def time_plots(publicdf):
    # drop all rows with NaN in the 'Date' column
    publicdf = publicdf.dropna(subset=['Date'])
    # create year, month and day columns so can chart value of awards by time
    publicdf['Year']= publicdf['Date'].dt.year.astype('Int32').astype('str')
    # extract month as a number as if extract as name then graph plots out of order
    publicdf['Month']= publicdf['Date'].dt.month.astype('Int32').astype('str')
    publicdf['Day']= publicdf['Date'].dt.day.astype('Int32').astype('str')
    # create a select box for user to choose how the awards are grouped
    col_val = st.selectbox('Select data for bar colour:', options = publicdf[['Type', 'Year', 'Recipient']].columns)
    plotgrp = px.bar(publicdf, x='Month', y='Value', color = col_val, barmode='group', title= 'Funds Awarded by Month', template="xgridoff").update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})
    # add some directions for a user exploring the chart
    st.write('Use your cursor to select and zoom into any area on the graph.')
    st.write('Hovering over the graph will show other graph interaction options to the top right of the plot.')
    # display the chart in the streamlit app
    st.plotly_chart(plotgrp, use_container_width=True )

# create year and month columns so can chart value of awards by time
publicdf['Year']= publicdf['Date'].dt.year.astype('Int32').astype('str')
publicdf['Month']= publicdf['Date'].dt.month.astype('Int32').astype('str')
publicdf['Day']= publicdf['Date'].dt.day.astype('Int32').astype('str')
plotgrp = px.box(publicdf, x='Month', y='Value',  title="Boxplot of Total Funds Awarded by Month of the Year",template="xgridoff").update_layout({'plot_bgcolor' : 'rgba(0,0,0,0)'})



####################
## Streamlit code ##
####################

# display the charts as selected by the user
st.subheader("Some charts showing the funding THAW has received and allocated since 2020")

# The following code gives the user the option of which chart to view
public = st.sidebar.selectbox('What would you like to see?', ['Total Funding and Awards', 'Funding Bar Charts', 'Award Value by Month of the Year', 'Awards Value as a Bar Plot', 'Awards Value as a Grouped Bar Chart', 'Awards Scatter Plots'])
st.subheader('\n')

# a function to displaye a chart as selected by the user
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

    
