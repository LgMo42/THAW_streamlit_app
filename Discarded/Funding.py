## API pages for funding transactions and wallets

import streamlit as st # import streamlit so for sending outputs to app
import pandas as pd # for cleaning and analysing with data
from decouple import config
import pymongo
import datetime as datetime

# connect to the collections, ok to use import as accessing connection not a dataframe
from THAW import funding
from THAW import wallet


# css code for formatin tables
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


# a list of funding sources for drop down menus 
# so only have ot make amendment once when a source is added or removed
funder = ['OICNew', 'Foodbank', 'OICemergency',]

# define today for using as default date on forms
today = datetime.date.today().strftime(format = '%d/%m/%Y')

# added time into transaction documents for display and delete actions
now = datetime.datetime.today().strftime(format = '%H:%M')

# function to display a document from the 'funds' collection
def display(funding):
    # get funding soucrce from user
    Name  = st.selectbox('Name', funder)
    # get date for transactions on a single date
    Date = st.text_input('Date received', today)
    # get document from 'funds' collection
    curs1 = funding.find({'Funded By': Name, "Date": datetime.datetime.strptime(Date, "%d/%m/%Y")})
    # convert cursor object to a list and sort in descending date order
    alldocs = list((funding.find({'Funded By': {"$in": [Name]} }).sort('Date',pymongo.DESCENDING)))
    # convert list to a df
    all_df = pd.DataFrame(alldocs) 
    #remove MongoDB document id
    all_df = all_df.drop('_id', axis=1)
    # convert date to string as more reader friendly
    all_df['Date'] = all_df['Date'].dt.strftime('%d/%m/%Y')
    # buttond for user to select transactions for date entered or all dates
    if st.button('Show Transaction'): st.write(list(curs1))
    if st.button('Show all transactions for funding source'): st.table(all_df)

# function to create and insert a new document into the 'funds' collection
def insert(funding):
    # get details needed to create document by asking for user inputs
    # set day as today but is able to be changed if necessary
    Date = st.text_input('Date funds were received', today)
    # get name of funding source using a drop down menu to avoid input errors
    Name  = st.selectbox('Name of funding source. Note: They must have a wallet before funds can be recorded.', funder)
    # get value of funds donated to THAW
    Value  = st.number_input('Value of Donation', 0) # if left blank will cause errors when imported to df
    # ValType added to make addition of crypto-currency easier in future developments
    ValType = st.text_input('Type of Value', 'GBP') # if left blank will cause errors when imported to df
    # added a comments option incase additional info is needed e.g. only for food etc
    Comments  = st.text_input('Comments', )
    # get current balance on funding source wallet document
    funBal = wallet.find_one({"URN": Name})['Balance']
    # set time as now for use in undo and display function
    time = now
    # input above valuesas a new document into the 'funds' collection and update funding source wallet
    newDoc = {'Date': datetime.datetime.strptime(Date, "%d/%m/%Y"), 'Time': time, 'Funded By': Name, 'Value': Value, 'Type of Value' : ValType,  'Comments': Comments}
    shownew = funding.find({'Funded By': Name, "Date": datetime.datetime.strptime(Date, "%d/%m/%Y"), 'Time':time})
    if st.button('Upload transaction'): 
        funding.insert_one(newDoc), 
        wallet.update_one({'URN': Name}, {'$set':{'Balance': funBal + Value}}), 
    # a button to display the document just created
    if st.button('Show last transaction'): st.write(list(shownew))
    # a button to show the funding source wallet
    if st.button('Show wallet for funding source'): st.json(wallet.find_one({"URN": Name}))
    # add a button to undo last transaction in case of error
    if st.button('Undo the last transaction'): 
            wallet.update_one({'URN': Name}, {'$set':{'Balance': funBal - Value}}),  
            funding.delete_one({'Date': datetime.datetime.strptime(Date, "%d/%m/%Y"), 'Time': time, 'Funded By': Name, 'Value': Value, 'Type of Value' : ValType})
            # delete has multiple fields, including time, so only one document is found and deleted

# function to display a document form the wallet collection
def displayw(wallet):
    # get wallet details
    URN  = st.text_input('Funding Source', 'Enter name of funding source, e.g. OIC or Foodbank')
    #  use above values to retreive the document from the wallet collection
    if st.button('Display wallet for funding source'): st.json(wallet.find_one({"URN": URN}))

# function to create a new wallet for a funding source
def insertw(wallet):
    # get new funding source details
    URN = st.text_input('Funding Source')
    Balance  = st.number_input('Current balance', 0) # if left blank will cause errors when imported to df
    Date = st.text_input('Date created in format dd/mm/yyyy', today)
    Comments  = st.text_input('Comments')
    # input above values as a new document into the 'wallet' collection
    newDoc = {'Date': datetime.datetime.strptime(Date, "%d/%m/%Y"),  'URN': URN, 'Balance': Balance , 'Comments': Comments}
    if st.button('Create Wallet'): 
        if wallet.count_documents({"URN" : URN}) > 0:  
            st.write("Funding source already has a wallet assigned.")
        else:
            wallet.insert_one(newDoc)
    if st.button('Show Wallet'): (st.json(wallet.find_one({"URN": URN})))

# function to delete wallet
def deletew(wallet):
    try:
        # get wallet name to be deleted
        URN  = st.text_input('Input the Funding Source wallet to be removed')
        # use above values to remove document from the 'wallet' collection
        if st.button('Remove Wallet') : wallet.delete_one({"URN": URN})
        if st.button('Show Wallet'): (st.json(wallet.find_one({"URN": URN})))
    except:
        st.error('This transaction number is not in the database') 


st.subheader("Funding: Transactions and Wallets")

st.write('Select from the options in the drop down menu to the left')

# request password from user
password = st.sidebar.text_input("Enter password to view confidential data:", type='password')

# create a side menu with options for user to choose from
db_info = st.sidebar.selectbox('Funds Data Menu', ['Show Transaction', 'Record Transaction', 'Show Wallet', 'Create New Wallet', 'Remove Wallet'])

st.write("\n")
st.write("\n")

# get password from Heroku config vars
strmpass = config('STRM_PASS_ADMIN')
# check password entered against password retrieved from Heroku 
if password == strmpass:
# password used during development, NOT the same as the online one
#if password == "1234":
    st.sidebar.write("Delete your password to hide this data.")
    st.write(db_info)
    def get_info(what_info):
        if what_info == 'Show Transaction':
            db_data = display(funding) 
        elif what_info == 'Record Transaction':
            db_data = insert(funding)  
        elif what_info == 'Show Wallet':
            db_data = displayw(wallet) 
        elif what_info == 'Create New Wallet':
            db_data = insertw(wallet) 
        else:
            db_data = deletew(wallet) 
        return db_data
    db_data = get_info(db_info)
else:
    st.write("Password has either not been entered or is incorrect.")
