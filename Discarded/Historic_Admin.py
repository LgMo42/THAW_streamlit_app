## The original admin page using historic data

import streamlit as st # import streamlit so for sending outputs to app
import pandas as pd # for cleaning and analysing with data
import pymongo #for accessing data from database
from decouple import config
import plotly_express as px
import datetime as dt

from THAW import incFB
from THAW import funding2

all = incFB[['Transaction Code', 'Date', 'Value', 'Recipient','Type','Sender','Admin Cost', 'Delivery Method', 'Time', 'Postcode']]
all['Date'] = pd.to_datetime(all['Date'], format = '%d/%m/%Y', errors='coerce')
all['Value'] = all['Value'].astype('float')
all = all.sort_values(by=['Date'])

all2 = all[['Transaction Code', 'Date', 'Value', 'Recipient','Type','Sender','Admin Cost', 'Delivery Method', 'Time', 'Postcode']]
all2['Date'] = all2['Date'].dt.strftime('%d/%m/%Y')

fundtb = funding2[['Date', 'Value', 'Funded By']]
fundtb['Date'] = pd.to_datetime(fundtb['Date'], format = '%d/%m/%Y', errors='coerce')

####################
## Streamlit code ##
####################

#https://docs.streamlit.io/knowledge-base/using-streamlit/how-download-pandas-dataframe-csv
@st.cache
def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')

# function to filter the complete dataframe by recipient
def recipient(all):
    # use df to provide store selection
    recip = st.text_input('Type the code of name of the recipient account you want to see. Please note this is case sensitive.', 'Papdale')
    # input date so can use to filter df
    start = st.text_input('Enter start date in format YYYY-MM-DD', '2020-01-01')
    end = st.text_input('Enter end date in format YYYY-MM-DD', '2025-01-01')
    # create df with only data from selected store
    recipdf = all[all['Recipient'] == recip]
    recipdf = recipdf.sort_values(by=['Date'])
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


# function to filter the complete dataframe by sender
def sender(all):
    # use df to provide store selection
    send = st.text_input('Type the code of name of the recipient account you want to see. Please note this is case sensitive.', '1376')
    # input date so can use to filter df
    start = st.text_input('Enter start date in format YYYY-MM-DD', '2020-01-01')
    end = st.text_input('Enter end date in format YYYY-MM-DD', '2025-01-01')
    # create df with only data from selected store
    senddf = all[all['Sender'] == send]
    senddf = senddf.sort_values(by=['Date'])
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

def type(all):
    try:
        # use df to provide type selection
        type = all['Type'].drop_duplicates()
        typeID = st.multiselect('Which store account do you want to see:', type, default=["Food"])
        # input date so can use to filter df
        start = st.text_input('Enter start date in format YYYY-MM-DD', '2020-01-01')
        end = st.text_input('Enter end date in format YYYY-MM-DD', '2025-01-01')
        # create df with only data from selected store
        typedf = all[all['Type'].isin(typeID)]
        typedf = typedf.sort_values(by=['Date'])
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

def fundTable(fundtb):
   try:
        # use df to provide type selection
        funded = fundtb['Funded By'].unique().tolist()
        fundID = st.multiselect("Select one or more options:", funded, default=["OIC"])
        # input date so can use to filter df
        start = st.text_input('Enter start date in format YYYY-MM-DD', '2020-01-01')
        end = st.text_input('Enter end date in format YYYY-MM-DD', '2025-01-01')
        # create df with only data from selected store
        fundtbdf = fundtb[fundtb['Funded By'].isin(fundID)]
        # filter by date
        fundtbdf =  fundtbdf[(fundtbdf['Date'] >= start) & (fundtbdf['Date'] <= end)]
    # convert to date to make it look nicer (date time gives h:m:s as well)
        fundtbdf['Date'] = fundtbdf['Date'].dt.date
        # add a column that gives the cumulative total for the selected dates. 
        fundtbdf['Value'] = fundtbdf['Value'].astype('float').astype('int32')
        fundtbdf['Cumulative Total (£)'] = fundtbdf['Value'].cumsum()
        fundtbdf = fundtbdf.sort_values(by='Date',ascending=True)
        st.write('The final total is £', fundtbdf.iloc[-1]['Cumulative Total (£)'])
        csv = convert_df(fundtbdf)
        st.download_button("Click to download table as csv file", csv, "filename.csv", "text/csv", key='download-csv')
        st.table(fundtbdf)
   except:
        st.stop()   

def allTable(all2):
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

password = st.sidebar.text_input("Enter password to view private data:", type='password')

ad_info = st.sidebar.selectbox('Admin Data', ['All','Filter by Recipient', 'Filter by Sender', 'Filter by Type', 'Funding Table'])

st.write("\n")
st.write("\n")

# display the data selected by THAW employee
# this code will display a previously calculated dataframe or def function

strmpass = config('STRM_PASS_ADMIN')
if password == strmpass:
#if password == "1234":
    st.write("Delete your password to hide this data.")
    st.write(ad_info)
    def get_info(what_info):
        if what_info == 'All':
            ad_data = allTable(all2) 
        elif what_info == 'Filter by Recipient':
            ad_data = recipient(all) 
        elif what_info == 'Filter by Sender':
            ad_data = sender(all)
        elif what_info == 'Filter by Type':
            ad_data = type(all)
        else:
            ad_data = fundTable(fundtb)
        return ad_data
    ad_data = get_info(ad_info)
else:
    st.write("Password has either not been entered or is incorrect.")

print(all.dtypes)
