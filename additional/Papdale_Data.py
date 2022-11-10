## page for displaying, inserting and deleteing documents from the 'papdale' collection

import streamlit as st # import streamlit so for sending outputs to app
import pandas as pd # for cleaning and analysing with data
from decouple import config
import pymongo

from THAW import pap

# function for displaying a document from the papdale collection
def display(pap):
    # get new voucher details
    #ID = st.text_input('URN')
    #Worth  = st.text_input('Value')
    Code  = st.text_input('Code', 'PSN')
    # input above values to papadale collection
    if st.button('Display Document'): st.json(pap.find_one({"Voucher Code": Code}))

# function for inserting a document
def insert(pap):
    # get new voucher details from user
    DateAlloc = st.text_input('Type date allocated in format dd/mm/yyyy')
    DateCol = st.text_input('Type date collected in format dd/mm/yyyy')
    Fund = st.text_input('Funded By')
    TypeV = st.text_input('Type of Voucher', 'Electricity')
    ID = st.text_input('URN')
    Worth  = st.text_input('Value', '0') # if left blank will cause errors when imported to df
    Code  = st.text_input('Code', 'PSN')
    # input above values as a new document into the 'papdale' collection
    newDoc = {'Date Allocated': DateAlloc, 'Date Collected': DateCol ,  'Funded By': Fund, 'Store': 'papale', 'Type': TypeV, 'URN': ID, 'Value': Worth,  'Voucher Code': Code}
    if st.button('Insert Document') : pap.insert_one(newDoc), 
    if st.button('Display Document'): (st.json(pap.find_one({"Voucher Code": Code})))

# function to delete a document
def delete(pap):
    try:
        # get voucher code for document to be deleted
        Code  = st.text_input('Input the voucher code for the document to be deleted:', 'PSN')
        # use above values to delete the document from the 'papdale' collection
        if st.button('Delete Document') : pap.delete_one({"Voucher Code": Code})
        if st.button('Display Document'): (st.json(pap.find_one({"Voucher Code": Code})))
    except:
        st.error('This Document number is not in the database') 


st.subheader("Papdale Documents")

st.write('Modify the papale collection via the options in the drop down menu to the left.')

# request password
password = st.sidebar.text_input("Enter password to view confidential data:", type='password')

# menu options for user
db_info = st.sidebar.selectbox('Papdale Data', ['Display Document', 'Insert Document','Delete Document'])

st.write("\n")
st.write("\n")

# get passwor from heroku config vars
strmpass = config('STRM_PASS_ADMIN')
# compare password entered to password retrieved from heroku
if password == strmpass:
# if password match go to following if function else give error message
#if password == "1234":
    st.sidebar.write("Delete your password to hide this data.")
    st.write(db_info)
    def get_info(what_info):
        if what_info == 'Display Document':
            db_data = display(pap) 
        elif what_info == 'Insert Document':
            db_data = insert(pap) 
        else:
            db_data = delete(pap) 
        return db_data
    db_data = get_info(db_info)
else:
    st.write("Password has either not been entered or is incorrect.")
