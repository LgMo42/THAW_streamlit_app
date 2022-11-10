Based on an RGU THAW MSc Project completed on 12th August 2022

The streamlit app is desigend to manage and analyse transactions between clients and local stores via a data dashboard. All data was stored a BJSON documents in MongoDB Atlas collections. The documents from the collections in the database are converted into dataframes and the pandas and plotly express libraries are used to transform these dataframes to display the data as charts and tables. For the MSc project the Streamlit app was hosted on Heroku so ti could be viewed online. 

The streamlit enables employees to view, update and create documents (which they will think of as 'transactions' or 'wallets') using the password protected pages. These act as API/GUIs for different system functions. 

Post project the files were uploaded to the THAW repo for further development with the aim of deploying a trail system using the accompanying Flask app designed to be the public GUI for the system. 
