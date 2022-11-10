import streamlit as st # import streamlit so for sending outputs to app
import pandas as pd # for cleaning and analysing with data
from decouple import config
import pymongo
import datetime as datetime

from THAW import wallet

def displayw(wallet):
    # get wallet details
    URN  = st.text_input('Enter the client URN', 'V2_01')
    # input above values to retreive the document from the wallet collection
    if st.button('Display Wallet'): st.json(wallet.find_one({"URN": URN}))

today = datetime.date.today().strftime(format = '%d/%m/%Y')
def insertw(wallet):
    # get new voucher details
    URN = st.text_input('Insert client URN')
    Electrity  = st.number_input('Electrity balance', 0) # if left blank will cause errors when imported to df
    Food  = st.number_input('Food balance', 0) # if left blank will cause errors when imported to df
    Misc  = st.number_input('Misc balance', 0) # if left blank will cause errors when imported to df
    Date = st.text_input('Date created in format dd/mm/yyyy', today)
    Comments  = st.text_input('Comments, e.g. why balance is not 0 if chnaged from defaults')
    # input above values to Wallet collection
    newDoc = {'Date': datetime.datetime.strptime(Date, "%d/%m/%Y"),  'URN': URN,  'Electrity':Electrity, 'Food':Food, 'Misc':Misc, 'Comments': Comments}
    if st.button('Insert Document'): 
        if wallet.count_documents({"URN" : URN}) > 0:  
            st.write("Client already has a wallet assigned.")
        else:
            wallet.insert_one(newDoc)
    if st.button('Display Document'): (st.json(wallet.find_one({"URN": URN})))

def deletew(wallet):
    try:
        # get voucher code to be deleted
        URN  = st.text_input('Input the URN for client wallet to be removed')
        # input above values to newadale collection
        if st.button('Delete Document') : wallet.delete_one({"URN": URN})
        if st.button('Display Document'): (st.json(wallet.find_one({"URN": URN})))
    except:
        st.error('This transaction number is not in the database') 


st.subheader("Client Wallet")

st.write('Select from the options in the drop down menu to the left')

password = st.sidebar.text_input("Enter password to view confidential data:", type='password')

db_info = st.sidebar.selectbox('New Data', ['Display Wallet', 'Insert Wallet', 'Delete Wallet'])

st.write("\n")
st.write("\n")

strmpass = config('STRM_PASS_ADMIN')
if password == strmpass:
#if password == "1234":
    st.sidebar.write("Delete your password to hide this data.")
    st.write(db_info)
    def get_info(what_info):
        if what_info == 'Display Wallet':
            db_data = displayw(wallet) 
        elif what_info == 'Insert Wallet':
            db_data = insertw(wallet) 
        else:
            db_data = deletew(wallet) 
        return db_data
    db_data = get_info(db_info)
else:
    st.write("Password has either not been entered or is incorrect.")
