import streamlit as st # import streamlit so for sending outputs to app
import pandas as pd # for cleaning and analysing with data
from decouple import config
import pymongo
import datetime as datetime

from THAW import wallet

def display(wallet):
    # get wallet details
    URN  = st.text_input('Funding Source', 'Enter name of funding source, e.g. OIC or Foodbank')
    # input above values to retreive the document from the wallet collection
    if st.button('Display Wallet Document'): st.json(wallet.find_one({"URN": URN}))

today = datetime.date.today().strftime(format = '%d/%m/%Y')
def insert(wallet):
    # get new wallet details
    URN = st.text_input('Funding Source')
    Balance  = st.number_input('Current balance', 0) # if left blank will cause errors when imported to df
    Date = st.text_input('Date created in format dd/mm/yyyy', today)
    Comments  = st.text_input('Comments')
    # input above values to wallet collection
    newDoc = {'Date': datetime.datetime.strptime(Date, "%d/%m/%Y"),  'URN': URN, 'Balance': Balance , 'Comments': Comments}
    if st.button('Insert Document'): 
        if wallet.count_documents({"URN" : URN}) > 0:  
            st.write("Funding source already has a wallet assigned.")
        else:
            wallet.insert_one(newDoc)
    if st.button('Display Document'): (st.json(wallet.find_one({"URN": URN})))

def delete(wallet):
    try:
        # get wallet name to be deleted
        URN  = st.text_input('Input the Funding Source wallet to be removed')
        # input above values to retrieve document from wallet collection
        if st.button('Delete Wallet') : wallet.delete_one({"URN": URN})
        if st.button('Display Wallet'): (st.json(wallet.find_one({"URN": URN})))
    except:
        st.error('This transaction number is not in the database') 


st.subheader("Wallets for Funds Recieved")

st.write('Select from the options in the drop down menu to the left')

password = st.sidebar.text_input("Enter password to view confidential data:", type='password')

db_info = st.sidebar.selectbox('Fund Wallets', ['Display Wallet', 'Create New Wallet','Delete Wallet'])

st.write("\n")
st.write("\n")

#strmpass = config('STRM_PASS_ADMIN')
#if password == strmpass:
if password == "1234":
    st.sidebar.write("Delete your password to hide this data.")
    st.write(db_info)
    def get_info(what_info):
        if what_info == 'Display Wallet':
            db_data = display(wallet) 
        elif what_info == 'Create New Wallet':
            db_data = insert(wallet) 
        else:
            db_data = delete(wallet) 
        return db_data
    db_data = get_info(db_info)
else:
    st.write("Password has either not been entered or is incorrect.")
