# Admin page for THAW employees

import streamlit as st # import streamlit so for sending outputs to app
import pandas as pd # for cleaning and analysing with data
import pymongo #for accessing data from database
from decouple import config #for retreiving password etc in .env file lcally or config vars online
import plotly_express as px
import datetime as dt

# css code for formatin tables
# CSS to inject contained in a string
hide_table_row_index = """
            <style>
            tbody th {display:none}
            .blank {display:none}
            </style>
            """
# Inject CSS with Markdown
st.markdown(hide_table_row_index, unsafe_allow_html=True)

## The dataframe was only uploading if the page was refreshed and then 
## user had to navigate to the home page to reinitialize the session state.
## Adding the code to the page using it keeps the app up-to-date without the user having to faff about.
## If THAW want historic data included then it is best to import it here then then transform and merge with new data. 

mongo = config('DATA')

# Initialize connection.
# Uses st.experimental_singleton to only run once.
@st.experimental_singleton
def init_connection():
    return pymongo.MongoClient(mongo)
client = init_connection()


# from https://docs.streamlit.io/knowledge-base/tutorials/databases/mongodb

# Pull data from the transaction collection
# Uses st.experimental_memo to only rerun when the query changes or after 10 min.
@st.experimental_memo(ttl=6)
def get_trans():
    db = client.THAW.transactions.find()
    trans_items = list(db)  # make hashable for st.experimental_memo
    transactions = pd.DataFrame(trans_items)
    transactions = transactions.drop('_id', axis=1)
    transactions['Admin Cost'] = 0.0
    return transactions

# define dataframe created from the transactions collection
all = get_trans()

# create a df where the 'Date' column is a string
all2 = all
all2['Value'] = all2['Value'].astype('str')


####################
## Streamlit code ##
####################

# create df for store accoun
storeAcc = all[['Date', 'Transaction Code', 'Type', 'Transaction Type', 'Value', 'Recipient', 'Sender']]
# list of stores w=that are on the system
store = ['Papdale', 'RGU']

# funcition to filter storeAcc depending on used input
def acc(storeAcc):
    # use df to provide store selection, added in RGU for testing new
    # can;t use unique function as will get all client URNs as well as stores
    StoreName = st.selectbox('Which store account do you want to see:', store)
    # input date so can use to filter df
    start = st.text_input('Enter start date in format YYYY-MM-DD', '2020-01-01')
    end = st.text_input('Enter end date in format YYYY-MM-DD', '2025-12-31')
    # create df with only data from selected store
    recvd = storeAcc[storeAcc['Recipient'] == StoreName]
    recvd = recvd.rename(columns={'Recipient':'Store'})
    recvd['Value'] = recvd['Value'].astype('int32')
    refd = storeAcc[storeAcc['Sender'] == StoreName]
    refd = refd.rename(columns={'Sender':'Store'})
    refd['Value'] = refd['Value'].astype('int32')*-1
    due = recvd.merge(refd, how='outer', on=['Store', 'Date', 'Transaction Code', 'Date', 'Value', 'Type', 'Transaction Type'])
    # filter by date
    due =  due[(due['Date'] >= start)& (due['Date'] <= end)]
    # convert to date to make it look nicer (date time gives h:m:s as well)
    due['Date'] = due['Date'].dt.date
    # remove unnecessary columns 
    due = due.drop(['Store', 'Sender', 'Recipient'], axis=1)
    # add a column that gives the cumulative total for the selected dates.
    due['Cumulative Total (£)'] = due['Value'].cumsum()
    st.table(due)


# creatE df for repeat and dupe dfs so can manipulate dates
repvouch = all[['Recipient', 'Transaction Code', 'Value', 'Date']]

repCli = repvouch.groupby(['Recipient'])['Transaction Code'].count().reset_index(name='Number Issued').sort_values(['Number Issued'], ascending=False)
# create a df where # issues is greater than 1
repCli = repCli[repCli['Number Issued']  > 1]
# aggreagate the dates for each Transaction Code
# change date to standard format
repvouch['Date'] = pd.to_datetime(repvouch['Date']).dt.strftime('%m/%d/%Y')
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

#https://docs.streamlit.io/knowledge-base/using-streamlit/how-download-pandas-dataframe-csv
@st.cache
def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')

# function to filter the complete dataframe by recipient
def recipient(all):
    try:
        # use df to provide store selection
        recip = st.text_input('Type the code of name of the recipient account you want to see. Please note this is case sensitive.')
        # input date so can use to filter df
        start = st.text_input('Enter start date in format YYYY-MM-DD', '2020-01-01')
        end = st.text_input('Enter end date in format YYYY-MM-DD', '2025-01-01')
        # create df with only data from selected store
        recipdf = all[all['Recipient'] == recip].sort_values(by=['Date'])
        # filter by date
        recipdf =  recipdf[(recipdf['Date'] >= start)& (recipdf['Date'] <= end)]
        # convert to date to make it look nicer (date time gives h:m:s as well)
        recipdf['Date'] = recipdf['Date'].dt.strftime('%d/%m/%Y')
        # convert value to integer
        recipdf['Value'] = recipdf['Value'].astype('int32')
        # add a column that gives the cumulative total for the selected dates. 
        recipdf['Cumulative Total (£)'] = recipdf['Value'].cumsum()
        # print the final total and  the selected rows as a df
        st.write('The final total is £', recipdf.iloc[-1]['Cumulative Total (£)'])
        # give admin the option to print table as csv file
        csv = convert_df(recipdf)
        st.download_button("Click to download table as csv file", csv, "filename.csv", "text/csv", key='download-csv')
        st.table(recipdf)
    except IndexError:
        st.write("Either no recipient has been entered or recipient does not have any transactions to show.")

# function to filter the transaction dataframe by sender
# thi shows where clients are 'spending' their funds
def sender(all):
    try:
        # use df to provide store selection
        send = st.text_input('Type the code of name of the recipient account you want to see. Please note this is case sensitive.')
        # input date so can use to filter df
        start = st.text_input('Enter start date in format YYYY-MM-DD', '2020-01-01')
        end = st.text_input('Enter end date in format YYYY-MM-DD', '2025-01-01')
        # create df with only data from selected store
        senddf = all[all['Sender'] == send].sort_values(by=['Date'])
        # filter by date
        senddf =  senddf[(senddf['Date'] >= start) & (senddf['Date'] <= end)]
        # convert to date to make it look nicer (date time gives h:m:s as well)
        senddf['Date'] = senddf['Date'].dt.strftime('%d/%m/%Y')
        # add a column that gives the cumulative total for the selected dates. 
        senddf = senddf.dropna(subset=['Value'])
        senddf['Value'] = senddf['Value'].astype('int32')
        senddf['Cumulative Total (£)'] = senddf['Value'].cumsum()
        st.write('The final total is £', senddf.iloc[-1]['Cumulative Total (£)'])
        csv = convert_df(senddf)
        st.download_button("Click to download table as csv file", csv, "filename.csv", "text/csv", key='download-csv')
        st.table(senddf)
    except IndexError:
        st.write("Either no sender has been entered or recipient does not have any transactions to show.")


def type(all):
    try:
        # use df to provide type selection
        type = all['Type'].drop_duplicates()
        typeID = st.multiselect('Which type you want to see:', type, default=["Food"])
        # input date so can use to filter df
        start = st.text_input('Enter start date in format YYYY-MM-DD', '2020-01-01')
        end = st.text_input('Enter end date in format YYYY-MM-DD', '2025-01-01')
        # create df with only data from selected type
        typedf = all[all['Type'].isin(typeID)].sort_values(by=['Date'])
        # filter by date
        typedf =  typedf[(typedf['Date'] >= start) & (typedf['Date'] <= end)]
        # convert to date to make it look nicer (date time gives h:m:s as well)
        typedf['Date'] = typedf['Date'].dt.strftime('%d/%m/%Y')
        # add a column that gives the cumulative total for the selected dates. 
        typedf = typedf.dropna(subset=['Value'])
        typedf['Value'] = typedf['Value'].astype('float').astype('int32')
        typedf['Cumulative Total (£)'] = typedf['Value'].cumsum()
        st.write('The final total is £', typedf.iloc[-1]['Cumulative Total (£)'])
        csv = convert_df(typedf)
        st.download_button("Click to download table as csv file", csv, "filename.csv", "text/csv", key='download-csv')
        st.table(typedf)
    except:
        st.stop() 

def tranType(all):
    try:
        # use df to provide type selection
        type = all['Transaction Type'].drop_duplicates()
        typeID = st.multiselect('Which type of transaction you want to see:', type)
        # input date so can use to filter df
        start = st.text_input('Enter start date in format YYYY-MM-DD', '2020-01-01')
        end = st.text_input('Enter end date in format YYYY-MM-DD', '2025-01-01')
        # create df with only data from selected type
        typedf = all[all['Transaction Type'].isin(typeID)].sort_values(by=['Date'])
        # filter by date
        typedf =  typedf[(typedf['Date'] >= start) & (typedf['Date'] <= end)]
        # convert to date to make it look nicer (date time gives h:m:s as well)
        typedf['Date'] = typedf['Date'].dt.strftime('%d/%m/%Y')
        # add a column that gives the cumulative total for the selected dates. 
        typedf = typedf.dropna(subset=['Value'])
        typedf['Value'] = typedf['Value'].astype('float').astype('int32')
        typedf['Cumulative Total (£)'] = typedf['Value'].cumsum()
        st.write('The final total is £', typedf.iloc[-1]['Cumulative Total (£)'])
        csv = convert_df(typedf)
        st.download_button("Click to download table as csv file", csv, "filename.csv", "text/csv", key='download-csv')
        st.table(typedf)
    except:
        st.stop() 

def allTable(all2):
    start = st.text_input('Enter start date in format YYYY-MM-DD', '2020-01-01')
    end = st.text_input('Enter end date in format YYYY-MM-DD', '2025-01-01')
    # filter by date
    all2 =  all2[(all2['Date'] >= start) & (all2['Date'] <= end)]
    all2['Date'] = all2['Date'].dt.strftime('%d/%m/%Y')
    csv = convert_df(all2)
    st.download_button("Click to download table as csv file", csv, "filename.csv", "text/csv", key='download-csv')
    st.table(all2)

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

st.subheader("Administrator")

# request password from user
password = st.sidebar.text_input("Enter password to view private data:", type='password')

# create a side menu with options for user to choose from
ad_info = st.sidebar.selectbox('Admin Data Menu', ['All','Filter by Recipient', 'Filter by Sender', 'Filter by Voucher Type', 'Filter by Transaction Type', 'Repeat Client List', 'Check Store Account'])

st.write("\n")
st.write("\n")

# display the data selected by THAW employee
# this code will display a previously calculated dataframe or function

# request password from Heroku config vars
strmpass = config('STRM_PASS_ADMIN')
# check password entered against password retrieved from Heroku 
if password == strmpass:
    st.write("Delete your password to hide this data.")
    st.write(ad_info)
    def get_info(what_info):
        if what_info == 'Check Store Account':
            ad_data = acc(storeAcc)    
        elif what_info == 'Repeat Client List':
            ad_data = st.table(repeatCli)
        elif what_info == 'All':
            ad_data = allTable(all2) 
        elif what_info == 'Filter by Recipient':
            ad_data = recipient(all) 
        elif what_info == 'Filter by Sender':
            ad_data = sender(all)
        elif what_info == 'Filter by Voucher Type':
            ad_data = type(all)
        elif what_info == 'Filter by Transaction Type':
            ad_data = tranType(all)
        return ad_data
    ad_data = get_info(ad_info)
else:
    st.write("Password has either not been entered or is incorrect.")

