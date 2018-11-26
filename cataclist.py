#!/usr/bin/env python3

import pandas as pd
import requests
import time
import re
import datetime
from os import path

'''
GOAL:
Columns of:
mac - ip - switchport - switch - vlan - mac_vendor - last_updated - ping_MM-DD-24-MM - ping_...
(mac is index, and required)

Cisco-like console for working on data 

starts with blank template

default mac format - cisco (since being used by cisco mainly)

create function to convert between them all

Functions:
-csv input (with merge)
-input via manual entry
-view all data
-view select data
-input via raw paste (detecting and parsing, find switchname on first or last lines)
-ping (multiple attempts recorded, nmap)
-Mac vendor lookup (local database csv required, likely)
-export to csv/excel

'''


# http://standards-oui.ieee.org/oui.txt
def get_mac_vendor_txt(maca):

    # First, convert mac to "base 16" non-symboled format, all uppercase
    maca = re.sub('[:\.-]', '', maca)
    maca = maca.upper()

    with open("oui.txt") as search:
        for line in search:
            if maca[:6] == line[:6]:

                return line[21:].strip()

    # If mac vendor could not be found
    return "(NO VENDOR MATCH)"


'''
#test design of mac convert function
#perhaps try: http://www.macvendorlookup.com/api/v2/00-23-AB-7B-58-99
#  --- https://www.macvendorlookup.com/index.php?page=api


def get_mac_vendor_api(maca):
    time.sleep(1.1) #API only allows 1 request per second, 1000 per day
    r = requests.get(f"http://api.macvendors.com/{maca}")
    if r.text.startswith('{"errors"'):
        return ""
    else:
        return r.text
'''

def print_instructions():
    print ("""
\033[36m
╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍

\033[1m[1]\033[22m - View Current Data
\033[1m[2]\033[22m - Import CSV
\033[1m[3]\033[22m - Import Copy/Paste
\033[1m[4]\033[22m - Soon - (Add Single Line/Data)
\033[1m[5]\033[22m -
\033[1m[6]\033[22m - DEBUG
\033[1m[7]\033[22m - MAC OUI Vendor Lookup
\033[1m[8]\033[22m - Soon - (Ping Check)
\033[1m[9]\033[22m - Export to CSV
\033[1m[0]\033[22m - Quit (Without Save)

╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍

\033[0m""")

def row_combine (r1, r2):
    

    #for c2, v2 in r2.items():
        #print('column:', c2, '     value:', v2)
        #for c1, v1 in r1.items():

    #print("r1 (Existing):\n",r1,"\n\n")
    #print("r2 (Adding):\n",r2,"\n\n")
    r2.update(r1)
    #Preferring old data. "Adding" csv must contain all valid columns.
    #logic could be better and this may be expanded in the future
    return r2


def view_current_data():
    print(df)

'''
def import_merge_csv_old(df_current):
    print ("csv file must have first row match EXACTLY as the valid column types:")
    print ("mac - ip - switchport - mac_vendor - vlan")
    inp = input('Specify filename for import╼> ')
    dtmp = pd.read_csv(inp)
    dtmp.set_index("mac", inplace=True)

    # need to prune columns that shouldn't be there (TO BE DONE LATER)

    #remove whitespace from all strings. (TO BE DONE LATER)
    # dtmp['mac'] = dtmp['mac'].str.strip()
    # dtmp['ip'] = dtmp['ip'].str.strip()

    # merge with existing data - index against the mac address for each. 
    df_new = pd.concat([df_current, dtmp], axis=1, sort=True )   # Axis zero means concatenate againt index (mac address)
    print(df_new)
    return df_new
'''

def import_merge_csv(df_existing):
    print (".CSV file must have first row match EXACTLY as the valid column types (order not important):")
    print ("mac - ip - switchport - switch - vlan - mac_vendor")
    inp = input('Specify filename for import╼> ')
    df_adding = pd.read_csv(inp)
    
    # Remove duplcate MAC addresses, keeping first one
    df_adding = df_adding.drop_duplicates(subset="mac")
    
    df_adding.set_index("mac", inplace=True)

    # df_final will be copy of df_existing and appended/edited
    # df_leftover is copy of df_adding....will be counted removed, and then remainder will be appended straight on to df-final
    df_final = df_existing
    df_leftover = df_adding


    for a_indx, a_row in df_adding.iterrows():   #iterate through "adding" df
        for e_indx,e_row in df_existing.iterrows():  #iterate through "existing" df
            if a_indx == e_indx:
                df_final.loc[e_indx] = row_combine(df_existing.loc[e_indx],df_adding.loc[a_indx])
                #finally, delete the row from df-leftover
                df_leftover = df_leftover.drop([a_indx])

    # now, append df-leftover onto df-final
    df_final = df_final.append(df_leftover, sort=False)
    # then, return df_final out of this function
    return df_final

def export_csv(df_export):
    while True:
        inp = input('Specify filename for export╼> ')
        if path.exists(inp):
            print (f"File {inp} already exists! Choose another filename...")
        elif inp == "":
            pass
        else:
            df_export.to_csv(inp)
            break


########### BEGIN!!!!! ###############


# First, create empty pandas as starting point
df = pd.DataFrame(columns=['mac', 'ip', 'switchport', 'vlan', 'mac_vendor', 'last_updated'])
# Set last_updated column to datetime datatype (set all others to object)
df = df.astype(object)
df["last_updated"] = pd.to_datetime(df["last_updated"])

# Set mac-address as the index
df.set_index("mac", inplace=True)


print ('''
\033[32m
⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓⬓
\033[33m
      ██████╗ █████╗ ████████╗ █████╗  ██████╗██╗     ██╗███████╗████████╗
     ██╔════╝██╔══██╗╚══██╔══╝██╔══██╗██╔════╝██║     ██║██╔════╝╚══██╔══╝
     ██║     ███████║   ██║   ███████║██║     ██║     ██║███████╗   ██║   
     ██║     ██╔══██║   ██║   ██╔══██║██║     ██║     ██║╚════██║   ██║   
     ╚██████╗██║  ██║   ██║   ██║  ██║╚██████╗███████╗██║███████║   ██║   
      ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝╚══════╝╚═╝╚══════╝   ╚═╝     

\033[32m                                                                                                                                                   

                      by JeffTadashi 
                v1.0                   2018-11-24      
\033[32m
⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒⬒

\033[0m''')

print_instructions()

while True:
    inp = input('Choose Number╼> ')
    if inp == "1":
        view_current_data()
    elif inp == "2":
        df = import_merge_csv(df)
    elif inp == "3":
        print("Placeholder")
    elif inp == "4":
        print("Placeholder")
    elif inp == "5":
        print("Placeholder")
    elif inp == "6":
        print(df.dtypes)
    elif inp == "7":
        df['mac_vendor'] = df['mac_vendor'].astype("object") #convert column to Object if it got messed elsewhere...
        for macx, row in df.iterrows():
            df.at[macx,"mac_vendor"] = get_mac_vendor_txt(macx)
    elif inp == "8":
        print("Placeholder")
    elif inp == "9":
        export_csv(df)
    elif inp == "0":
        break   #end of program
    else:
        print_instructions()

#end of program


