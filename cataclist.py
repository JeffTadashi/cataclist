#!/usr/bin/env python3

import pandas as pd
import requests
import time
import re
import datetime
from os import path
import nmap

# Global Parameters:
template_columns = ["mac", "ip", "switchport", "switch", "vlan", "mac_vendor"]


"""

TO DO:
-convert all MAC address input to cisco format (10aa.bbbb.cccc)
--create function that can convert between the three main formats (01-23-45-67-89-AB,  86:00:a8:48:73:00, and 10aa.bbbb.cccc)
-Check that input CSV has the correct columns. Delete or add as necessary (before the merge step)
-conver Vlan to cisco format on input (Vlan25, not 25)
-download oui.txt file automatically at beginning, if it does not exist

TO DO Functions:
-input via manual entry
-view select data
-input via raw paste (detecting and parsing, find switchname on first or last lines)
-ping (multiple attempts recorded, nmap)
-export to excel
-export to text (choose single column)

"""


def get_mac_vendor_txt(maca):

    # http://standards-oui.ieee.org/oui.txt
    # Uses this file as reference, must match spacing exactly.
    # Download the file into the same folder as the main script

    # First, convert mac to "base 16" non-symboled format, all uppercase
    maca = re.sub("[:\.-]", "", maca)
    maca = maca.upper()

    with open("oui.txt") as search:
        for line in search:
            if maca[:6] == line[:6]:

                return line[21:].strip()

    # If mac vendor could not be found
    return "(NO VENDOR MATCH)"


def print_instructions():
    print(
        """
\033[36m
╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍

\033[1m[1]\033[22m - View Current Data
\033[1m[2]\033[22m - Import CSV
\033[1m[3]\033[22m - Import Copy/Paste
\033[1m[4]\033[22m - Soon - (Add Single Line/Data)
\033[1m[5]\033[22m -
\033[1m[6]\033[22m - DEBUG
\033[1m[7]\033[22m - MAC OUI Vendor Lookup
\033[1m[8]\033[22m - Ping Sweep
\033[1m[9]\033[22m - Export to CSV
\033[1m[0]\033[22m - Quit (Without Save)

╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍╍

\033[0m"""
    )

def ping_check(df_in):

    # This works better when script overall is run as SUDO/ROOT. otherwise it seems to miss a few IP's consistently.
    
    df_out = df_in

    now_time = datetime.datetime.now()
    ping_column_name = f"ping_{now_time.strftime('%b')}{now_time.day}_{now_time.hour}:{now_time.minute}"
    # print (ping_column_name)

    first_list = (list(df_in['ip']))
    cleaned_list = [x for x in first_list if str(x) != 'nan']
    nmap_ip_in = (' '.join(cleaned_list))
  
    nm = nmap.PortScanner()
    nm.scan(hosts=nmap_ip_in, arguments='-n -sn -v')
    hosts_list = [[x, nm[x]['status']['state']] for x in nm.all_hosts()]

    for df_ind, df_row in df_in.iterrows():
        for nm_ip, nm_updown in hosts_list:
            if df_row['ip'] == nm_ip:
                print (nm_ip + " found match and is " + nm_updown)
                df_out.at[df_ind,ping_column_name] = nm_updown


    return df_out



def row_combine(r1, r2):

    # for c2, v2 in r2.items():
    # print('column:', c2, '     value:', v2)
    # for c1, v1 in r1.items():

    # print("r1 (Existing):\n",r1,"\n\n")
    # print("r2 (Adding):\n",r2,"\n\n")
    r2.update(r1)
    # Preferring old data. "Adding" csv must contain all valid columns.
    # logic could be better and this may be expanded in the future
    return r2



def import_merge_csv(df_existing):
    print(
        ".CSV file must have first row match EXACTLY as the valid column types (order not important):"
    )
    print(template_columns)
    inp = input("Specify filename for import╼> ")

    try:
        df_adding = pd.read_csv(inp)
    except:
        print("File could not be read, or does not exist!")
        # exit by returning input arg file
        return df_existing

    # Remove duplcate MAC addresses, keeping first one
    df_adding = df_adding.drop_duplicates(subset="mac")

    df_adding.set_index("mac", inplace=True)

    # df_final will be copy of df_existing and appended/edited
    # df_leftover is copy of df_adding....will be counted removed, and then remainder will be appended straight on to df-final
    df_final = df_existing
    df_leftover = df_adding

    for a_indx, a_row in df_adding.iterrows():  # iterate through "adding" df
        for e_indx, e_row in df_existing.iterrows():  # iterate through "existing" df
            if a_indx == e_indx:
                df_final.loc[e_indx] = row_combine(
                    df_existing.loc[e_indx], df_adding.loc[a_indx]
                )
                # finally, delete the row from df-leftover
                df_leftover = df_leftover.drop([a_indx])

    # now, append df-leftover onto df-final
    df_final = df_final.append(df_leftover, sort=False)
    # then, return df_final out of this function
    return df_final


def export_csv(df_export):
    while True:
        inp = input("Specify filename for export╼> ")
        if path.exists(inp):
            print(f"File {inp} already exists! Choose another filename...")
        elif inp == "":
            pass
        else:
            df_export.to_csv(inp)
            break


############### BEGIN!!!!! ###############

# mac - ip - switchport - switch - vlan - mac_vendor - ping_MM-DD-24-MM - ping_...

# First, create empty pandas as starting point
df = pd.DataFrame(columns=template_columns)
# Set last_updated column to datetime datatype (set all others to object)
df = df.astype(object)
# (implementing later) df["last_updated"] = pd.to_datetime(df["last_updated"])

# Set mac-address as the index
df.set_index("mac", inplace=True)


print(
    """
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

\033[0m"""
)

print_instructions()

while True:
    inp = input("Choose Number╼> ")
    if inp == "1":
        print(df)
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
        # convert column to Object if it got messed elsewhere...
        df["mac_vendor"] = df["mac_vendor"].astype("object")
        for macx, row in df.iterrows():
            df.at[macx, "mac_vendor"] = get_mac_vendor_txt(macx)
    elif inp == "8":
        df = ping_check(df)
    elif inp == "9":
        export_csv(df)
    elif inp == "0":
        break  # end of program
    else:
        print_instructions()

# end of program
