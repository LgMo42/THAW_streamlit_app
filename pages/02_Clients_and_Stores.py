## API pages for client and store transactions and wallets 

import streamlit as st # import streamlit so for sending outputs to app
import pandas as pd # for cleaning and analysing with data
from decouple import config
import pymongo
import datetime as datetime
import random
import string
import time


# connect to the collections, ok to use import as accessing connection not a dataframe
from THAW import trans
from THAW import wallet

# css code for formating tables
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

# define today for using as default date on forms
today = datetime.date.today().strftime(format = '%d/%m/%Y')

# added time into transaction documents for display and delete actions
now = datetime.datetime.today().strftime(format = '%H:%M')

# a list of funding sources for drop down menus 
# so only have ot make amendment once when a source is added or removed
fundSc = ['OICNew', 'Foodbank', 'OICemergency']
store = ['Papdale', 'RGU']

# function to display a document from the 'transactions' collection
def display(trans):
    try:
        # get transaction details from the user
        Sender  = st.text_input('Input the URN or store name that sent the funds')
        Recipient  = st.text_input('Input the URN or store name that received the funds')
        Date = st.text_input('Input the date the funds were moved', today)
        # use above values to find function to find matching douments in the 'transactions' collection for the sender
        findsend = trans.find({'Sender': Sender, "Date": datetime.datetime.strptime(Date, "%d/%m/%Y")})
        #convert cursor to list
        sendlst = list(findsend)
        # convert list to df
        senddf = pd.DataFrame(sendlst)
        senddf = senddf.drop('_id', axis=1)
        senddf['Date'] = senddf['Date'].dt.date
        # use above values to find function to find matching douments in the 'transactions' collection for the recipient
        findrecip = trans.find({'Recipient': Recipient, "Date": datetime.datetime.strptime(Date, "%d/%m/%Y")})
        #convert cursor to list
        reciplst = list(findrecip)
        # convert list to df
        recipdf = pd.DataFrame(reciplst)
        recipdf = recipdf.drop('_id', axis=1)
        recipdf['Date'] = recipdf['Date'].dt.date
        # button and action for user to click when ready to search for document(s)
        if st.button('Show Transaction by Sender'): st.table(senddf)
        if st.button('Show Transaction by Recipient'): st.table(recipdf)
    except KeyError:
        # error messsage when no recipent or one without a wallet is entered
        st.write("Either a sender or recipient must be entered")

# function to create and insert a new document into the 'transactions' collection
# amended to also update the documents the funds are being moved from and to
def insert(trans):
    try:
        # get details needed to create document by asking for user inputs
        # set day as today but is able to be changed if necessary
        Date = st.text_input('Type date allocated in format dd/mm/yyyy', today)
        # get funding source using a drop down menu to avoid input errors
        Funder = st.selectbox('Funded By', fundSc)
        # define what the voucher is to be used for using a drop down menu to avoid input errors
        TypeV = st.selectbox('What can the funds be used for?', ['Electricity', 'Food', 'Cash'])
        # get client ID or store name
        ID = st.text_input('Client URN or Store Name (Recipient)')
        # get the value of funds to be transferred from funding source wallet to client wallet
        Value  = st.number_input('Value of Award', 0) # if left blank will cause errors when imported to df
        # ValType added to make addition of crypto-currency easier in future developments
        ValType = st.text_input('Type of Value', 'GBP') # if left blank will cause errors when imported to df
        # generate a random 16 digit code
        Rcode = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        # code defaults to randomly generated code but can be changed if necessary
        Code  = st.text_input('Transaction Code', Rcode)
        # select delivery method
        Deliver = st.selectbox('Delivery Method', ['App', 'Email', 'Text', 'Paper'])
        # get type balance for client/store wallet
        cliBal =  wallet.find_one({"URN": ID})[TypeV]
        # set time to now for use in undo and display function
        # get current balance on THAW wallet document
        thawBal = wallet.find_one({"URN": 'THAW'})[TypeV]
        time = now
        # input above values as a document into the 'transactions' collection and update associated wallets
        newDoc = {'Date': datetime.datetime.strptime(Date, "%d/%m/%Y"), 'Time': time, 'Sender': Funder, 'Type': TypeV, 'Recipient': ID, 'Value': Value, 'Type of Value' : ValType,  'Transaction Code': Code, 'Delivery Method': Deliver, 'Transaction Type':'Create'}
        if st.button('Allocate Funds'): 
            # check transacton code does not exist (kept in case non-random generated codes are used)
            if trans.count_documents({"Transaction Code": Code}) > 0: 
                st.write("Transaction code already exists please enter a different code to complete transaction.")
            else:
                #create transaction document and update client and THAW wallet
                trans.insert_one(newDoc),  wallet.update_one({'URN': ID}, {'$set':{TypeV: cliBal + Value}}),
                wallet.update_one({'URN': 'THAW'}, {'$set':{TypeV: thawBal - Value}})
        # a button to display the document just created
        if st.button('Show last transaction'): (st.json(trans.find_one({'Recipient': ID, 'Type':TypeV,"Date": datetime.datetime.strptime(Date, "%d/%m/%Y"), "Time":time})))
        # a button to show the client/store wallet
        if st.button('Show the recipients wallet'): st.json(wallet.find_one({"URN": ID}))
        # a button to show the THAW wallet
        if st.button('Show the THAW wallet'): st.json(wallet.find_one({"URN": 'THAW'}))
        # add a button to undo last transaction in case of error
        if st.button('Undo the last transaction'):
            # revert wallet balances and delete document
            wallet.update_one({'URN': ID}, {'$set':{TypeV: cliBal - Value}}), 
            wallet.update_one({'URN': 'THAW'}, {'$set':{TypeV: thawBal + Value}}), 
            trans.delete_one({'Recipient': ID, 'Type':TypeV, 'Sender': Funder, 'Type of Value' : ValType, "Date": datetime.datetime.strptime(Date, "%d/%m/%Y"), "Time":time})
            # delete has multiple fields, including time, so only one document is found and deleted
    except TypeError:
        # error messsage when no recipent or one without a wallet is entered
        st.write("Enter client URN under recipient. Client must have a wallet document before any funds can be allocated")

# function to display a document form the wallet collection
def displayw(wallet):
    # get wallet details
    URN  = st.text_input('Enter the client URN')
    # use above values to retreive the document from the wallet collection
    if st.button('Show Wallet'): st.json(wallet.find_one({"URN": URN}))

# function to create a new wallet for a client or store
def insertw(wallet):
    # get client/store details
    URN = st.text_input('Input a client URN or Store name')
    Username = st.text_input('Create a unique username for the client whichis not their URN')
    Electricity  = st.number_input('Electricity balance', 0) # if left blank will cause errors when imported to df
    Food  = st.number_input('Food balance', 0) # if left blank will cause errors when imported to df
    Cash  = st.number_input('Cash balance', 0) # if left blank will cause errors when imported to df
    #  set day as today but is able to be changed if necessary
    Date = st.text_input('Date created in format dd/mm/yyyy', today)
    Comments  = st.text_input('Comments, e.g. why balance is not 0 or client hard of hearing etc')
    # input above values as a new document into the 'wallet' collection
    newDoc = {'Date': datetime.datetime.strptime(Date, "%d/%m/%Y"), 'Username': Username, 'URN': URN,  'Electricity':Electricity, 'Food':Food, 'Cash':Cash, 'Comments': Comments}
    if st.button('Insert Document'): 
        # check wallet does not exist as each clie/store only allowed one wallet
        if wallet.count_documents({"URN" : URN}) > 0:  
            st.write("Client already has a wallet assigned.")
        elif wallet.count_documents({"Username" : Username}) > 0:  
            st.write("Username already taken, please choose another one")
        else:
            wallet.insert_one(newDoc)
    if st.button('Show Document'): (st.json(wallet.find_one({"URN": URN})))

# function to delete wallet e.g. if client moves or a store closes
def deletew(wallet):
    try:
        # get voucher code to be deleted
        URN  = st.text_input('Input the URN for client wallet to be removed')
        # use above values to remove document from the 'wallet' collection
        if st.button('Delete Wallet') : wallet.delete_one({"URN": URN})
        if st.button('Show Wallet'): (st.json(wallet.find_one({"URN": URN})))
    except:
        st.error('This transaction number is not in the database')

# function to 'pay' a store wallet
def resetw(wallet):
    try:
        # get voucher code to be deleted
        URN  = st.selectbox('Input the name of the store wallet to be reset', 'THAW')
        # select which type is to be reset
        TypeV = st.selectbox('What type do you want to record payment for?', ['Electricity', 'Food', 'Cash'])
        # get the value of funds to be transferred from funding source wallet to client wallet
        Paid  = st.number_input('Amount paid', 0)
        # get type balance for store wallet
        Bal =  wallet.find_one({"URN": URN})[TypeV]
        # use above values to remove document from the 'wallet' collection
        if st.button('Reset Balance') : wallet.update_one({'URN': URN}, {'$set':{TypeV: Bal - Paid}})
        if st.button('Show Document'): (st.json(wallet.find_one({"URN": URN})))
    except:
        st.error('This transaction number is not in the database') 


st.subheader("Client and Store Transactions and Wallets")

st.write('Select from the options in the drop down menu to the left')

# request password from user
password = st.sidebar.text_input("Enter password to view confidential data:", type='password')

# create a side menu with options for user to choose from
db_info = st.sidebar.selectbox('Clients and Stores Menu', ['Show a Transaction', 'Allocate Funds', 'Show Wallet', 'Create Wallet', 'Remove Wallet', 'Reset THAW Wallet'])

st.write("\n")
st.write("\n")

# get password from Heroku config vars
strmpass = config('STRM_PASS')
# check password entered against password retrieved from Heroku 
if password == strmpass:
    st.sidebar.write("Delete your password to hide this data.")
    st.write(db_info)
    def get_info(what_info):
        if what_info == 'Show a Transaction':
            db_data = display(trans) 
        elif what_info == 'Allocate Funds':
            db_data = insert(trans) 
        elif what_info == 'Show Wallet':
            db_data = displayw(wallet) 
        elif what_info == 'Create Wallet':
            db_data = insertw(wallet) 
        elif what_info == 'Remove Wallet':
            db_data = deletew(wallet) 
        elif what_info == 'Reset THAW Wallet':
            db_data = resetw(wallet) 
        return db_data
    db_data = get_info(db_info)
else:
    st.write("Password has either not been entered or is incorrect.")
