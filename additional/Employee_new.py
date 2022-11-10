# Data that any employee can see

import streamlit as st # import streamlit so for sending outputs to app
import pandas as pd # for cleaning and analysing with data
import pymongo #for accessing data from database
from decouple import config
import plotly_express as px
import datetime as dt

# get the dataframes from main page
from THAW import transactions
from THAW import funds

voucher = transactions[['Transaction Code', 'Date', 'Value', 'Recipient','Type','Sender','Admin Cost', 'Delivery Method', 'Time', 'Postcode']]
voucher['Date'] = voucher['Date'].dt.strftime('%d/%m/%Y')

fundEmp = funds[['Date', 'Value', 'Funded By']]
fundEmp['Value'] = fundEmp['Value'].astype('str') # to match employee df

#voucher = st.session_state['voucher']
#income = st.session_state['income']

# following code outputs info for clients who have recieved more than one voucher from THAW
# counts the URNs and sorts the df in descenting order of # vouchers issued

################################################################
################################################################

# Code relating to date voucher is used could be implmemnted for new voucher system
# no use for historic data as this information is not currently avaiable
# kept as hope to use for new system when up and runnning. Code works.
# create a column to calculate the time between voucher allocation and use

#dateError[['Date Allocated','Date Used']] = (voucher[['Date Allocated','Date Used']]).apply(pd.to_datetime, format = '%d/%m/%Y')
#dateError['Days Until Used'] = (dateError['Date Used'] - dateError['Date Allocated']).astype('timedelta64[D]')
#dateError[['Days Until Used','Value']] = dateError[['Days Until Used','Value']].astype('int32')

# create a dataframe where Date Allocated is before Date Used
#dateerr = dateError[dateError['Days Until Used'] < 0].sort_values(['Date Allocated'], ascending=True)
# convert datetime to object as looks better on streamlit table
#dateerr['Date Allocated'] = dateerr['Date Allocated'].dt.strftime('%m/%d/%Y')
#dateerr['Date Used'] = dateerr['Date Used'].dt.strftime('%m/%d/%Y')


################################################################
################################################################


# creat df for repeat and dupe dfs so can manipulate dates
repvouch = voucher[['Recipient', 'Transaction Code', 'Value', 'Date']]

repCli = repvouch.groupby(['Recipient'])['Transaction Code'].count().reset_index(name='Number Issued').sort_values(['Number Issued'], ascending=False)
# create a df where # issues is greater than 1
repCli = repCli[repCli['Number Issued']  > 1]
# aggreagate the dates for each Transaction Code
# change date to standard format
#repvouch['Date'] = pd.to_datetime(repvouch['Date']).dt.strftime('%m/%d/%Y')
repCli2 = repvouch.groupby(['Recipient'])[('Date')].agg(list).reset_index()
# sum the values of the vouchers to see total amount given to each repeat client
# Value has to be converted to float before it can be summed
# #NaN means cannot convert to int and do not want to remove data at ths point
repvouch['Value'] = repvouch['Value'].astype('float')
repCli3 = repvouch.groupby(['Recipient'])[('Value')].agg(sum)

# df 1 & 3 are merged on the URN so the resulting dataframe has both number of vouchers issues there total value
repeatClis = repCli.merge(repCli3, how='inner', on='Recipient').sort_values(['Number Issued'], ascending=False)
# this is merged with the 2nd df to add the list of dates the vouchers were issued on
repeatCli = repeatClis.merge(repCli2, how='inner', on='Recipient').sort_values(['Number Issued'], ascending=False)
# rename value column to total value
repeatCli['Value'] = repeatCli['Value'].astype('int32')
repeatCli = repeatCli.rename(columns={'Value':'Total Value'})


#following code outputs the duplicated Transaction Codes and counts how many duplictaes there are
dupeV = repvouch.groupby(['Transaction Code'])['Transaction Code'].count().reset_index(name='count').sort_values(['count'], ascending=False)
dupeV = dupeV[dupeV['count'] > 1]
# aggragate the dates that each voucher was issued and used one
#repvouch['Date'] = pd.to_datetime(repvouch['Date']).dt.strftime('%m/%d/%Y')
dupeV2 = repvouch.groupby(['Transaction Code'])[('Date')].agg(list).reset_index()
# the 2 dataframes are merged on the Transaction Code so the resulting dataframe has both nunber of vouchers issued and the dates they were issued and used on for each Transaction Code
dupeV3 = dupeV.merge(dupeV2, how='inner', on='Transaction Code').sort_values(['count'], ascending=False)

#this code returns a all rows where the Date is empty
nodate = voucher[['Recipient', 'Value','Type','Transaction Code','Date']][voucher['Date'].isna() ]
#unused['Date'] = pd.to_datetime(unused['Date']).dt.strftime('%m/%d/%Y')

voucher['Recipient'] = voucher['Recipient'].replace(dict.fromkeys(['papadale', 'Papadale','Papdale Store', 'Papdale Stores', 'papdale store', 'papdale stores', 'papdale Store', 'papdale Stores', 'Papdale store', 'Papdale stores'], 'Papdale'))
# then create a table where store != Papdale or Charis for other errors
#storeErr = voucher[(voucher['Recipient'] != 'Papdale') & (voucher['Recipient'] != 'Charis')]

# code to correct delivery method inputs
voucher['Delivery Method'] = voucher['Delivery Method'].replace(dict.fromkeys(['email', 'Email'], 'E-mail'))
voucher['Delivery Method'] = voucher['Delivery Method'].replace(dict.fromkeys(['SMS', 'sms'], 'Text'))
voucher['Delivery Method'] = voucher['Delivery Method'].replace(dict.fromkeys(['Email - In Person'], 'In Person'))

# converted date column from object to datetime
voucher['Date'] = pd.to_datetime(voucher['Date'], format = '%d/%m/%Y', errors='coerce')

#remove duplicate vouchers
voucher = voucher.drop_duplicates(subset=['Transaction Code'])

# once the duplicates have been removed but before and na are removed total voucher spend can be calculated
#As there are na in voucher value colum it wil be converted to float for now
voucher[['Value','Admin Cost']] = (voucher[['Value','Admin Cost']]).astype(float)
TotSpend = voucher['Value'].sum() + voucher['Admin Cost'].sum()


# calculate cuerrent total of all income received since 01/01/2020
totfundEmp = fundEmp.dropna(subset=['Value'])
totfundEmp['Value'] = totfundEmp['Value'].astype('float')
totfundEmp['Value'] = totfundEmp['Value'].astype('int32')
TotIn = totfundEmp['Value'].sum()
Bal = round((TotIn - TotSpend),2)

# covnert date to datetime
fundEmp['Date'] = pd.to_datetime(fundEmp['Date'], format = '%d/%m/%Y', errors='coerce')

# correct data entry error
fundEmp['Funded By'] = fundEmp['Funded By'].replace(dict.fromkeys(['OICOICCharis', 'OICCharis'], 'OIC Charis'))


####################
## Streamlit code ##
####################

# from https://docs.streamlit.io/knowledge-base/using-streamlit/hide-row-indices-displaying-dataframe
# CSS to inject contained in a string
hide_table_row_index = """
            <style>
            tbody th {display:none}
            .blank {display:none}
            </style>
            """
# Inject CSS with Markdown
st.markdown(hide_table_row_index, unsafe_allow_html=True)


## Private Data

# require a password to see any data in this selection
st.subheader("Private Data")

password = st.sidebar.text_input("Enter password to view private data:", type='password')

# The following code gives THAW the option about which table to view

info = st.sidebar.selectbox('Private Data', ['Store Account', 'Repeat Client List', 'Duplicate Transcation Information', 'Missing Date List'])

st.write("\n")
st.write("\n")

# from https://discuss.streamlit.io/t/filter-dataframe-by-selections-made-in-select-box/6627/2

## Create a dataframe that shows 'Transaction Code','Date Used', 'Value', 'Type' & 'Store'
storeAcc = voucher[['Transaction Code','Date', 'Value', 'Type', 'Recipient']]

# funcition to filter storeAcc depending on used input
def acc(storeAcc):
    # use df to provide store selection, added in RGU for testing new
    StoreName = st.selectbox('Which store account do you want to see:', ['Papdale', 'Charis' , 'RGU'])
    # input date so can use to filter df
    start = st.text_input('Enter start date in format YYYY-MM-DD', '2020-01-01')
    end = st.text_input('Enter end date in format YYYY-MM-DD', '2025-12-31')
    # create df with only data from selected store
    due = storeAcc[storeAcc['Recipient'] == StoreName]
    # filter by date
    due =  due[(due['Date'] >= start)& (due['Date'] <= end)]
    # convert to date to make it look nicer (date time gives h:m:s as well)
    due['Date'] = due['Date'].dt.date
    # add a column that gives the cumulative total for the selected dates. 
    due['Value'] = due['Value'].astype('int32')
    due['Cumulative Total (£)'] = due['Value'].cumsum()
    st.table(due)


# display the data selected by THAW employee
# this code will display a previously calculated dataframe or def function
# code for password protected data. Replace "1234" with code that says compare to heroku config vars 
#strmpass = config('STRM_PASS')
#if password == strmpass:
if password == "1234":
    st.write("Delete your password to hide this data.")
    st.write(info)
    def get_info(what_info):
        if what_info == 'Store Account':
            data = acc(storeAcc)    
        elif what_info == 'Repeat Client List':
            data = st.table(repeatCli)
        elif what_info == 'Duplicate Transcation Information':
            data = st.table(dupeV3)
        elif what_info == 'Missing Date List':
            data = st.table(nodate)
        return data
    data = get_info(info)
else:
    st.write("Password has either not been entered or is incorrect.")

